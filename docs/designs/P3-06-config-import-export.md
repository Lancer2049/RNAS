# P3-06: 配置导入导出 详细设计

## 用户故事
> 作为网络工程师，我需要一键导出 RNAS 的完整配置（JSON/YAML），保存到 Git 仓库进行版本管理；也能一键导入已有配置，快速重建测试环境。不同测试场景之间可以快速切换配置，不需要手动编辑 20+ 个模板文件。

## 当前状态
- ✅ 21 个 INI 配置模板在 `/etc/rnas/`
- ✅ PUT /api/config/{module} 可逐模块写入
- ✅ POST /api/config/apply 可重新生成并应用
- ❌ 无批量导出功能
- ❌ 无批量导入功能
- ❌ 无配置快照/回滚
- ❌ 无 Git 集成

## 技术设计

### API 设计

```
POST   /api/config/export              → 导出全部配置 (JSON)
POST   /api/config/export?format=yaml  → 导出为 YAML
POST   /api/config/import              → 导入配置 (multipart/form-data)
GET    /api/config/snapshots           → 列出所有快照
POST   /api/config/snapshot            → 创建快照
POST   /api/config/snapshot/{id}/restore → 恢复到指定快照
DELETE /api/config/snapshot/{id}       → 删除快照
GET    /api/config/diff?from={a}&to={b} → 对比两个版本
```

### 导出格式

```json
{
  "rnas_version": "3.0",
  "exported_at": "2026-05-02T15:00:00Z",
  "topology": {
    "vm1_cpe": "192.168.0.201",
    "vm2_radius": "192.168.0.202",
    "vm3_rnas": "192.168.0.203"
  },
  "config": {
    "access.d.core": {
      "pppoe": "yes",
      "ipoe": "yes",
      "l2tp": "yes",
      "pptp": "yes",
      "sstp": "yes",
      "thread_count": "4"
    },
    "access.d.radius": {
      "server": "192.168.0.202",
      "secret": "testing123",
      "auth_port": "1812"
    },
    "...": "..."
  },
  "checksum": "sha256:abc123..."
}
```

### Web UI 设计

```
┌─────────────────────────────────────────────────────────┐
│ Configuration Management                                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  [Export JSON]  [Export YAML]  [Import...]  [Snapshot]  │
│                                                         │
│  ┌─ Snapshots ─────────────────────────────────────────┐│
│  │ ID        Date        Description         Actions    ││
│  │ ────────  ──────────  ─────────────────  ─────────  ││
│  │ snap-001  05-02 14:30  Baseline config    [Restore] ││
│  │ snap-002  05-02 15:00  802.1X enabled     [Restore] ││
│  │ snap-003  05-02 15:30  QoS tiered         [Restore] ││
│  │                                       [Delete All]  ││
│  └──────────────────────────────────────────────────────┘│
│                                                         │
│  ┌─ Import Preview ────────────────────────────────────┐│
│  │ Section         Changes                             ││
│  │ ─────────────   ─────────────────────────────────── ││
│  │ access.d.core   pppoe: yes → no                     ││
│  │ access.d.ipoe   interface: ens33 → br-lan (NEW)     ││
│  │ network.d.dhcp  + relay section                     ││
│  │                                    [Apply] [Cancel] ││
│  └──────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

### 快照存储

```
/var/lib/rnas/snapshots/
├── snap-001_2026-05-02T143000.json
├── snap-002_2026-05-02T150000.json
└── latest -> snap-002_2026-05-02T150000.json
```

### Git 集成（可选高级功能）

```bash
rnas-config version init        # git init /etc/rnas + .gitignore
rnas-config version save "msg"  # git add -A && git commit -m "msg"
rnas-config version log         # git log --oneline
rnas-config version diff        # git diff HEAD
rnas-config version restore N   # git checkout HEAD~N
```

### 导入安全机制

| 检查项 | 说明 |
|--------|------|
| 版本兼容性 | 检查 `rnas_version` 字段，拒绝不兼容版本 |
| 校验和验证 | 验证 `checksum` 防止文件损坏 |
| 干运行预览 | 导入前显示变更对比，用户确认后执行 |
| 自动备份 | 导入前自动创建快照 |
| 回滚 | 导入后 5 分钟内可一键回滚 |

### 实现步骤

| 步骤 | 内容 | 产出 |
|------|------|------|
| 1 | 实现 walk_config_tree 的导出逻辑 | 完整 JSON 导出 |
| 2 | 实现批量导入逻辑（干运行 + 确认 + 应用） | Import API |
| 3 | 添加差异对比功能 | diff API |
| 4 | 实现快照功能（save/restore/delete） | 快照 CRUD |
| 5 | 创建 ConfigManager Vue 组件 | UI |
| 6 | 端到端测试（导出→修改→导入→验证） | 集成测试 |

### 验收标准

| # | 标准 | 验证方法 |
|---|------|---------|
| 1 | 导出 JSON 包含所有配置节 | `jq '.config | keys | length'` = 40 |
| 2 | 导出→导入→导出 结果相同 | 两次导出的 checksum 一致 |
| 3 | 快照可恢复 | 修改配置→恢复快照→验证还原 |
| 4 | 导入预览显示变更 | Playwright 测试 |
| 5 | 导入时自动备份 | 快照列表增加一条 |
| 6 | 校验和不匹配拒绝导入 | 修改 JSON 后导入被拒绝 |

### 依赖
- Python stdlib json/yaml (无外部依赖)
- 前端：无新依赖（使用现有 fetch API）

### 预估工时
4-6 小时（API 2h + UI 2h + 测试 2h）
