# RNAS 集成测试计划

## 现状

已有 **29 个 E2E 测试**，全部通过。但大部分是页面加载检测（smoke test），缺少真正的业务场景验证。

---

## 一、场景分类矩阵

| 类别 | 优先级 | 现有覆盖 | 需新增 |
|------|--------|----------|--------|
| A. 认证与会话管理 | P0 | 0 | 4 |
| B. 配置 CRUD 工作流 | P0 | 4 (部分) | 8 |
| C. 网络运维工具 | P1 | 1 | 5 |
| D. 监控与状态 | P1 | 3 | 5 |
| E. 边界与错误处理 | P1 | 0 | 6 |
| F. 跨功能联动 | P2 | 0 | 5 |
| G. 性能与稳定性 | P2 | 1 | 3 |

---

## 二、场景详情

### A. 认证与会话管理（P0）

| # | 场景 | 验证点 | 涉及 API | 当前状态 |
|---|------|--------|----------|----------|
| A1 | 会话列表加载 | 表格渲染、列正确（SID/用户名/IP/类型/状态/时长/流量） | `GET /sessions` | ✅ 已覆盖 |
| A2 | 会话详情 | 点击接口名跳转详情页，显示关联会话 | `GET /interfaces/{name}` | ✅ 已覆盖 |
| A3 | 断开会话 | 在会话页面点击断开，确认消息出现 | `POST /sessions/{sid}/disconnect` | ✅ 已覆盖 |
| A4 | RADIUS 用户列表 | 用户表格加载，包含 username/attribute/value | `GET /aaa/users` | ✅ 已覆盖 |
| A5 | RADIUS 计费记录 | 计费记录表格加载 | `GET /aaa/acct` | ✅ 已覆盖 |
| A6 | RADIUS 用户组 | 用户组列表加载 | `GET /aaa/groups` | ✅ 已覆盖 |
| A7 | NAS 客户端列表 | NAS 设备列表加载 | `GET /aaa/nas` | ✅ 已覆盖 |

### B. 配置 CRUD 工作流（P0）

| # | 场景 | 验证点 | 涉及 API | 当前状态 |
|---|------|--------|----------|----------|
| B1 | Services 各协议切换 & 修改 | PPTP / L2TP / SSTP / IPsec 标签切换，每个标签下表单可见，修改字段，Save，验证 "✓ Saved" | `PUT /config/{module}` | ✅ 已覆盖 |
| B2 | IP Manager — 添加 DHCP 静态绑定 | 切换到 Static 标签，填 mac/ip/hostname，添加，确认出现在列表中 | `GET /ip/dhcp-static`, `POST /ip/dhcp-static` | ✅ 已覆盖 |
| B3 | IP Manager — 删除 DHCP 静态绑定 | 删除刚添加的条目，确认不再出现在列表 | `DELETE /ip/dhcp-static` | ✅ 已覆盖 |
| B4 | IP Manager — 添加 IP 地址 | Addresses 标签，填接口和 IP，添加，确认列表更新 | `GET /ip/addresses`, `POST /ip/addresses` | ✅ 已覆盖 |
| B5 | Config Editor — 浏览配置分类 | 分类侧边栏展开，选择分类，字段展示 | `GET /config` | ✅ 已覆盖 |
| B6 | Config Editor — 修改并保存配置 | 修改一个字段，保存，验证反馈 | `PUT /config/{module}` | ✅ 已覆盖 |
| B7 | Config Snapshot — 创建 & 列表显示 | 创建快照，确认出现在列表中 | `POST /config/snapshot`, `GET /config/snapshots` | ✅ 已覆盖 |
| B8 | Config Snapshot — 对比差异 | 选择一个快照，查看 diff 内容 | `GET /config/snapshot/{name}/diff` | ✅ 已覆盖 |
| B9 | Certificate — 生成证书 | 填写名称/域名/有效期，生成，确认列表新增 | `POST /system/certificates/generate` | ✅ 已覆盖 |
| B10 | Certificate — 列表展示 | 证书列表加载，类型/大小/修改时间正确 | `GET /system/certificates` | ✅ 已覆盖 |
| B11 | Queue — 删除规则 | 添加规则后，点击删除，验证规则消失 | 删除相关 API | ✅ 已覆盖 |
| B12 | Quick Setup — 三步向导完成 | Step1 填网络 → Step2 填 RADIUS → Step3 确认 → Apply，验证成功消息 | `POST /setup/apply` | ✅ 已覆盖 |

### C. 网络运维工具（P1）

| # | 场景 | 验证点 | 涉及 API | 当前状态 |
|---|------|--------|----------|----------|
| C1 | Tools — Ping | 打开 Tools 页面，Ping 标签可见，输入 IP，执行，输出显示 | `GET /tools/ping` | ✅ 已覆盖 |
| C2 | Tools — Traceroute | Traceroute 标签，执行，输出显示 | `GET /tools/trace` | ✅ 已覆盖 |
| C3 | Tools — DNS Lookup | DNS 标签，输入域名，查询，结果展示 | `GET /tools/dns` | ✅ 已覆盖 |
| C4 | Tools — RADIUS 认证测试 | RADIUS Test 标签，默认用户/密码/服务器预填，发送，结果展示 | `GET /tools/radius-test` | ✅ 已覆盖 |
| C5 | Tools — CoA 断连 | CoA 标签，输入用户名/服务器/Secret，发送断连请求 | `GET /tools/coa` | ✅ 已覆盖 |
| C6 | Sniffer — 启动/停止/状态 | 启动抓包→确认 running→停止→确认 stopped | `POST sniffer/start`, `GET sniffer/status`, `POST sniffer/stop` | ✅ 已覆盖 |

### D. 监控与状态（P1）

| # | 场景 | 验证点 | 涉及 API | 当前状态 |
|---|------|--------|----------|----------|
| D1 | System Status — 服务列表 | 所有 8 个系统服务状态加载 (accel-ppp/dnsmasq/web/strongswan/wg/openvpn/keepalived/snmpd) | `GET /system/status` | ✅ 已覆盖 |
| D2 | Health Alerts — 告警列表 | 告警页面渲染，严重/警告分类 | `GET /system/health/alerts` | ✅ 已覆盖 |
| D3 | Notification — 保存配置 | 填入 Telegram/Webhook 信息，保存，确认成功 | `POST /system/notifications` | ✅ 已覆盖 |
| D4 | Interface Detail — 接口详情 | 点击接口名，详情页加载：IP/MAC/流量统计/关联会话 | `GET /interfaces/{name}` | ✅ 已覆盖 |
| D5 | Traffic History — 历史图表 | Traffic Monitor 选择时间范围（5m/1h/1d），图表渲染 | `GET /interfaces/history` | ✅ 已覆盖 |
| D6 | RADIUS Monitor — 详细统计 | 独立 RADIUS 监控页面，认证/计费统计 | `GET /radius/stats` | ✅ 已覆盖 |

### E. 边界与错误处理（P1）

| # | 场景 | 验证点 | 涉及 API | 当前状态 |
|---|------|--------|----------|----------|
| E1 | 空状态 — 无会话 | 会话列表为空时显示 "No active sessions" 或空状态占位 | 无 | ✅ 已覆盖 |
| E2 | 空状态 — 无 DHCP 租约 | DHCP 租约空时显示空状态 | `GET /ip/dhcp` | ✅ 已覆盖 |
| E3 | 空状态 — 无 ARP 条目 | ARP 表空时显示空状态 | `GET /ip/arp` | ✅ 已覆盖 |
| E4 | 无效输入 — 表单校验 | DHCP 静态绑定缺 mac/ip 时点击 Add，应有错误提示 | `POST /ip/dhcp-static` | ✅ 已覆盖 |
| E5 | 无效输入 — IP 地址格式错误 | Addresses 页面填非法 IP，应有校验 | `POST /ip/addresses` | ✅ 已覆盖 |
| E6 | 重复提交 — 快速双击 | 快速点击 Save 两次，后端只处理一次 | `PUT /config/{module}` | ✅ 已覆盖 |
| E7 | 认证失败 — 错误密码 | Tools/RADIUS Test 填错误密码，显示 Access-Reject | `GET /tools/radius-test` | ✅ 已覆盖 |

### F. 跨功能联动（P2）

| # | 场景 | 验证点 | 涉及流程 | 当前状态 |
|---|------|--------|----------|----------|
| F1 | 配置修改 → Apply → 系统状态验证 | 修改某项配置→Apply→返回系统状态页验证服务正常运行 | Config → Apply → System Status | ✅ 已覆盖 |
| F2 | 创建快照 → 修改配置 → 对比差异 | 创建快照→改配置→对比 diff 显示变化 | Snapshot Create → Edit → Diff | ✅ 已覆盖 |
| F3 | 生成证书 → 证书列表验证 | 在 Certificate Manager 生成→列表中出现新条目 | Generate → List | ✅ 已覆盖 |
| F4 | PPPoE 配置 → 会话页面验证 | 启用 PPPoE→确认 Sessions 页面有 ppp 接口 | Protocols → Sessions | ✅ 已覆盖 |
| F5 | 多标签连续操作 | 连续在不同功能间跳转，每一步验证页面正常渲染 | IP → Services → Protocols → Tools → Config | ✅ 已覆盖 |

### G. 性能与稳定性（P2）

| # | 场景 | 验证点 | 当前状态 |
|---|------|--------|----------|
| G1 | 快速页面跳转 | 连续快速点击 5 个不同菜单项，无页面崩溃/JS 错误 | ✅ 已覆盖 |
| G2 | 页面刷新持久化 | 修改配置后刷新页面，数据保持（如 PPPoE 启用状态、IP 列表） | ✅ 已覆盖 |
| G3 | 长时间打开 | 页面打开 30 秒，持续监控无 console error 增加 | ✅ 已覆盖 |

---

## 三、执行优先级

### Phase 1 — P0（核心业务流程）
```
A1-A4  会话 & RADIUS 用户
B1-B6  Services 全协议、IP Manager CRUD、Config Editor
B12    Quick Setup 完整流程
```

### Phase 2 — P1（运维 & 监控）
```
B7-B11  Snapshot/Certificate/Queue
C1-C6   Tools & Sniffer
D1-D6   System Status/Health/Interface Detail
E1-E7   错误 & 边界
```

### Phase 3 — P2（跨功能 & 稳定性）
```
F1-F5   跨功能联动
G1-G3   性能/稳定性
```

---

## 四、测试结构建议

按功能模块分文件：

```
tests/e2e/
├── browser-pppoe.spec.ts       # 已有 - PPPoE 配置工作流
├── dashboard.spec.ts           # 已有 + 补充监控场景
├── new-features.spec.ts        # 已有 - 网络功能页面
├── full-integration.spec.ts    # 已有 - 综合场景
├── sessions.spec.ts            # 新建 - 会话管理 (A1-A3)
├── aaa.spec.ts                 # 新建 - RADIUS AAA (A4-A7)
├── services.spec.ts            # 新建 - Services 全部协议 (B1)
├── ip-manager-crud.spec.ts     # 新建 - IP CRUD (B2-B4)
├── config-editor.spec.ts       # 新建 - Config 编辑/快照 (B5-B8)
├── certificates.spec.ts        # 新建 - 证书管理 (B9-B10)
├── tools.spec.ts               # 新建 - 诊断工具 (C1-C6)
├── monitoring.spec.ts          # 新建 - 监控/状态 (D1-D6)
├── error-boundary.spec.ts      # 新建 - 边界/错误 (E1-E7)
├── cross-feature.spec.ts       # 新建 - 跨功能联动 (F1-F5)
└── stability.spec.ts           # 新建 - 性能/稳定性 (G1-G3)
```

---

## 五、关键测试设计原则

1. **纯浏览器 UI 交互**：所有测试通过 Playwright `page` 对象驱动，不直接调用 API
2. **人类操作模拟**：先导航→等待渲染→找元素→操作→验证反馈
3. **幂等性**：测试需可重复执行，不依赖上一次运行的状态
4. **隔离性**：每个测试独立运行，不影响其他测试
5. **反馈验证优先**：验证 UI 上的成功/失败消息，而非请求/响应数据
6. **错误容忍**：测试环境可能有差异，需处理元素可能存在或不存在的情况

---

## 六、计划审批

此计划包含 **~35 个新增测试场景**，分 3 个 Phase 执行。请确认：
- 优先级是否合理？
- 是否有遗漏的关键场景？
- 是否希望先执行某个 Phase？
