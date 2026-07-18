# RNAS 对标分析及改进计划

> 对标项目: pfSense · OPNsense · MikroTik RouterOS · VyOS · OpenWrt
> 分析日期: 2026-06-22

---

## 第一部分: 各项目架构与设计理念

### 1.1 pfSense (CE 2.7+)

| 维度 | 特征 |
|------|------|
| **语言** | PHP (Phoenix/Form based) |
| **存储** | XML 配置文件 (`/cf/conf/config.xml`) |
| **RADIUS** | 内置 FreeRADIUS 包，用户/计费管理 GUI |
| **UI 亮点** | Dashboard widget 系统、status_graph RRD 图、firewall rule 拖拽排序 |
| **特色** | ``status.php`` 实时查看连接状态、RRD 流量历史、配置备份/回滚 |
| **要点** | 每个功能页面都有 status + graph，数据采集层独立 (rrdtool) |

**可借鉴:**
- RRDtool 循环数据库 → 接口流量历史折线图
- Widget 化 Dashboard（可自由拖拽排列）
- 配置历史/备份/回滚功能
- 诊断工具一站式页面（ping/traceroute/ DNS lookup/ packet capture）

### 1.2 OPNsense (24.x)

| 维度 | 特征 |
|------|------|
| **语言** | PHP (MVC — Phalcon 框架) |
| **API** | 原生 REST API，Swagger 文档 |
| **监控** | 内置 Netdata 集成、Health 报警、Reporting 全菜单 |
| **特色** | ``configctl`` CLI、审计日志、入侵检测/预防 |
| **要点** | 前后端分离最佳实践、Reporting 自成体系、API 完全覆盖 |

**可借鉴:**
- REST API 优先的设计理念（每个 UI 操作背后都是 API 调用）
- Health/Status 报警机制（服务 down → 前端通知）
- Reporting 子系统（按时间范围查询历史数据）
- ``configctl`` CLI（通过 CLI 执行任意 API 操作）

### 1.3 MikroTik RouterOS / WinBox (v7+)

| 维度 | 特征 |
|------|------|
| **UI** | WinBox (原生桌面应用) + WebFig (Web) + CLI |
| **架构** | 层级菜单: Interfaces → 具体接口 → 详细设置 |
| **特色** | QuickSet 一键配置、Traffic Graph 实时浮动、Torch 实时流量分析 |
| **监控** | /interface monitor-traffic、Graphing 工具、Log 按 topic 筛选 |
| **要点** | 多级 drill-down、每个节点都可配置、Tab 式 panel 布局 |

**可借鉴:**
- **QuickSet** — 首次启动向导（LAN/WAN/PPPoE/RADIUS 快速配置）
- **Interface list → detail drill-down** — 点击接口进入实时流量/状态页
- **Tab 式多级菜单** — RouterOS 风格（左侧菜单 → 次级 Tab → 详情）
- **实时 Traffic Graph 浮动** — 独立的 graph 窗口
- **Log 按 Topic** — 按 service/协议级别筛选日志

### 1.4 VyOS (1.4+)

| 维度 | 特征 |
|------|------|
| **架构** | CLI-first, Python-based config system |
| **配置模型** | `configure` → `set` → `commit` → `save` 事务模型 |
| **特色** | 配置回滚、版本化 commit、`show` 命令树 |
| **要点** | 配置即代码、API 基于 commit 事务 |

**可借鉴:**
- **配置事务提交** — `rnas-config` 支持 `commit`/`rollback` 语义
- **show 命令树** — 结构化配置查看
- **操作模式/配置模式分离** — 查看 vs 修改的权限边界

### 1.5 OpenWrt / LuCI (23.05+)

| 维度 | 特征 |
|------|------|
| **架构** | Lua + JavaScript, ubus RPC, procd 服务管理 |
| **UIC** | UCI (Unified Configuration Interface) 配置文件系统 |
| **特色** | `luci-app-*` 包体系、`cbi` 自动表单生成 |
| **要点** | 模块化 UI 包、配置系统抽象层 |

**可借鉴:**
- **UCI 命名空间** — `/etc/rnas/access.d/` 已经很接近，可标准化
- **cbi 形式自动生成** — 根据配置 schema 自动渲染表单
- **热榜/强制门户** — OpenWrt 的 freeradius3 + CoovaChilli 集成

---

## 第二部分: RNAS 与对标项目差距矩阵

| 功能域 | pfSense | OPNsense | RouterOS | VyOS | OpenWrt | RNAS 当前 |
|--------|---------|----------|----------|------|---------|-----------|
| 配置回滚 | ✅ XML backup + restore | ✅ Config revisions | ✅ /system backup | ✅ commit/rollback | ❌ | ⚠️ CLI snapshot 无 UI |
| 流量历史 | ✅ RRD graphs (1h/24h/7d/30d/1y) | ✅ Reporting graphs | ✅ /tool graphing | ❌ | ⚠️ collectd | ❌ |
| 防火墙规则排序 | ✅ 拖拽排序 | ✅ 拖拽排序 | ✅ 数字优先级 | ✅ rule 编号 | ✅ 数字优先级 | ❌ 纯文本 |
| 端口转发向导 | ✅ NAT → Port Forward wizard | ✅ 同左 | ✅ /ip firewall nat | ❌ | ✅ 有转发模板 | ❌ |
| RADIUS 用户管理 | ✅ FreeRADIUS 包 GUI | ✅ FreeRADIUS 包 GUI | ✅ /radius incoming | ❌ | ✅ freeradius3 | ⚠️ AAA users API 空 |
| PPPoE 服务器管理 | ✅ accel-ppp 支持 | ✅ accel-ppp 支持 | ✅ /interface pppoe-server | ❌ | ✅ accel-ppp | ✅ 有但无向导 |
| DHCP 静态绑定 UI | ✅ 一键绑定 | ✅ 一键绑定 | ✅ Make Static | ⚠️ 文件配置 | ✅ 类似 | ⚠️ POST API 无一键 |
| 证书管理 | ✅ System → Certificates | ✅ Trust → Certificates | ✅ /certificate | ❌ | ✅ 有 CA 管理 | ❌ |
| Web 终端 | ✅ Diagnostics → Command | ✅ Shell | ✅ /terminal | ✅ 原生 CLI | ✅ ttyd | ❌ |
| 健康报警 | ⚠️ 基本 | ✅ Monit + 通知 | ✅ /system watchdog | ❌ | ❌ | ❌ |
| 实时会话图 | ✅ status_graph.php | ✅ Reporting → traffic | ✅ Graphs 浮动窗口 | ⚠️ | ❌ | ⚠️ 有表格无图 |
| 配置向导 | ✅ Setup wizard | ✅ Setup wizard | ✅ QuickSet | ❌ | ❌ | ❌ |
| 诊断工具箱 | ✅ 一站式页面 | ✅ Diagnostics 菜单 | ✅ /tools | ✅ operational mode | ✅ 系统 → 工具 | ⚠️ 分散多个页面 |
| API 优先 | ⚠️ 部分 | ✅ 原生 REST | ✅ REST API | ✅ gRPC/HTTP | ✅ ubus RPC | ✅ FastAPI 但有缺口 |
| 插件/包系统 | ✅ Package Manager | ✅ Plugins | ✅ 无正式(但可扩展) | ❌ | ✅ opkg | ❌ |

---

## 第三部分: 改进计划

### S-Tier (最高优先级——直接影响可用性)

#### S1: 防火墙规则可视化排序管理

**现状**: 只有纯文本 nftables 规则显示，无法拖拽排序、无法直观看到规则命中计数。

**方案**: 
- 后端: 增强 `GET /api/ip/firewall-full`，返回每条规则的 `handle` + `packet_count` + `byte_count` + `position`
- 前端: 拖拽排序（SortableJS），hitcount 彩色柱状条，规则启/禁用开关

**参考**: pfSense firewall rules table — 每条规则一行，拖拽改变顺序，彩色打勾表示启用。

#### S2: 配置备份/快照/回滚 Web UI

**现状**: CLI 已支持 `rnas-config snapshot`，但无法通过 Web 界面操作。

**方案**:
- 后端: `GET /api/config/snapshots` 列表、`POST /api/config/snapshot` 创建、`POST /api/config/snapshot/{name}/restore`
- 前端: System → Snapshots 页面，显示快照列表 + 创建/恢复按钮 + diff 对比

**参考**: pfSense Diagnostics → Backup & Restore

### A-Tier (高优先级)

#### A1: 接口实时流量图 (RRD 风格)

**现状**: TrafficMonitor 有实时速率表格和 Chart.js 会话图，但缺 **每个接口的历史速率折线图**（5 分钟 / 1 小时 / 1 天 / 1 周）。

**方案**:
- 后端: 新增 `/api/interfaces/history?name=ens33&range=1h`，后端定时轮询 `/sys/class/net/{iface}/statistics/`，存储环形缓冲区
- 前端: Chart.js 多时间段选择（5m / 1h / 1d / 1w），叠加 RX/TX 双线，平滑曲线

**参考**: pfSense RRD graphs / RouterOS Graphs。

#### A2: 端口转发向导

**现状**: NAT tab 有手动添加规则的表单，但缺少"标准端口转发"引导界面（外部端口 → 内部 IP:端口）。

**方案**:
- 后端: `POST /api/ip/firewall` 已支持添加 nftables dnat 规则
- 前端: NAT tab 增加 Port Forward 子 tab，表单: 协议(TCP/UDP) → 外部端口 → 内部 IP → 内部端口 → 描述。自动生成 `dnat to ...` 规则

**参考**: pfSense Firewall → NAT → Port Forward。

#### A3: DHCP 一键静态绑定

**现状**: Static tab 允许手动添加 MAC→IP 绑定，但需要手动输入所有信息。DHCP Leases tab 显示当前租约，但没法"把当前租约一键变成静态绑定"。

**方案**:
- 前端: DHCP Leases tab 每行加 "Make Static" 按钮，点击自动填充 MAC/IP/hostname 到添加表单
- 后端: `POST /api/ip/dhcp-static` 已支持

**参考**: RouterOS IP → DHCP Server → Leases → Make Static。

#### A4: 系统日志可视化

**现状**: SystemLog 组件原始显示 journalctl 输出，无按级别颜色高亮。

**方案**:
- 前端: 日志行按 `ERROR`(红) / `WARN`(黄) / `INFO`(白) / `DEBUG`(灰) 着色
- 后端: 已支持 `unit=` 和 `level=` 过滤参数，前端加多选 filter chips
- 加日志统计: 过去 24h 各级别日志数量迷你图

### B-Tier (中优先级)

#### B1: 诊断工具一站式页面

**现状**: Ping、Traceroute、Bandwidth Test、Packet Sniffer、CoA Test 分散在 Tools 和 RADIUS Tools 等多个页面。

**方案**: 合并为单一 Diagnostics 页面，左侧 tab 切换：Ping / Traceroute / DNS Lookup / Packet Capture / Bandwidth Test / CoA Test

#### B2: 接口 Drill-Down 详情页

**现状**: 点击接口无反应，只能在外层表格查看。

**方案**: 点击接口名 → 进入接口详情页，显示:
- 基本信息 (MAC/MTU/状态/IP)
- 实时速率 Chart.js 图（最后 5 分钟）
- 报文分布饼图（TCP/UDP/ICMP/Other）
- 错误计数器折线图
- 关联的活跃 Session 列表

**参考**: RouterOS Interface → detail。

#### B3: 服务健康报警

**现状**: 无主动通知机制。

**方案**:
- 后端: `GET /api/system/health/alerts` 检查各服务状态，返回 down 的服务列表 + 持续时间
- 前端: Topbar 加告警铃铛图标，红色标记异常服务数量；点击展开详情
- 简单报警规则: 服务 down 超过 30 秒 → 状态标记为 ERR

#### B4: RADIUS 用户管理 GUI

**现状**: AAA Users API 返回空（因为数据在 FreeRADIUS 文件/SQL 中），前端 AAAEditor 可以发 RADIUS 请求但没有用户列表。

**方案**:
- 后端: `GET /api/aaa/users` 从 FreeRADIUS 数据库读取（sql 或文件），显示用户+属性列表
- 前端: 用户列表 → 添加/编辑/删除用户 → RADIUS 属性管理

### C-Tier (未来方向)

#### C1: 配置向导 (QuickSet)

首次启动引导配置: WAN IP / LAN 网段 / RADIUS 服务器 / PPPoE 参数 / 管理员密码。3 步完成基本配置。

#### C2: Web 终端

在浏览器内提供 shell 访问，基于 xterm.js + WebSocket。可用于运维调试。

#### C3: 证书管理

SSL/TLS 证书的生成/导入/管理界面，用于 SSTP/OpenVPN/HTTPS。

#### C4: 流量历史 RRD 数据持久化

超过实时窗口的历史流量数据持久化到磁盘（SQLite 或 RRD），支持按天/周/月/年查看趋势。

#### C5: 报警通知渠道

邮件 / Webhook / Telegram Bot 通知。

---

## 第四部分: 实施路线图

```
Phase A (1-2 周)                           Phase B (2-4 周)                    Phase C (长期)
┌────────────────────────┐              ┌────────────────────────┐           ┌────────────────────┐
│ S1 防火墙规则拖拽排序    │              │ B1 诊断工具一站式        │           │ C1 配置向导 QuickSet │
│ S2 配置快照 Web UI      │──── Phase──▶│ B2 接口 Drill-Down      │──Phase──▶│ C2 Web 终端         │
│ A1 接口流量图(RRD风格)   │  B          │ B3 健康报警              │  C        │ C3 证书管理          │
│ A2 端口转发向导          │              │ B4 RADIUS 用户管理 GUI   │           │ C4 流量历史持久化     │
│ A3 DHCP 一键静态绑定     │              │                         │           │ C5 报警通知          │
│ A4 日志可视化            │              │                         │           │                     │
└────────────────────────┘              └────────────────────────┘           └────────────────────┘
```

### 投入估算

| 级别 | 功能数 | 后端改动 | 前端改动 | 预估人天 |
|------|--------|---------|---------|---------|
| S | 2 | 中 | 中 | 3-4 天 |
| A | 4 | 小-中 | 中 | 5-7 天 |
| B | 4 | 中 | 中-大 | 6-8 天 |
| C | 5 | 大 | 大 | 10-15 天 |

---

## 第五部分: Todo 清单

```yaml
s_tier:
  s1_firewall_drag_sort:
    component: IPManager.vue + routes/extra.py
    effort: 2d
    description: "防火墙规则拖拽排序 + hitcount 显示 + 启用/禁用开关"
    reference: pfSense firewall_rules.php

  s2_config_snapshot_ui:
    component: SystemPage.vue + routes/config.py
    effort: 1d
    description: "配置快照 Web 界面（创建/列表/恢复/diff）"
    reference: pfSense diag_backup.php

a_tier:
  a1_interface_traffic_graph:
    component: TrafficMonitor.vue + routes/extra.py
    effort: 3d
    description: "per-interface Chart.js 实时折线图（5m/1h/1d/1w）"
    reference: RouterOS Graphs / pfSense status_graph.php

  a2_port_forward_wizard:
    component: IPManager.vue (NAT tab subtab)
    effort: 1d
    description: "端口转发向导表单 → 自动生成 dnat 规则"
    reference: pfSense firewall_nat.php

  a3_dhcp_make_static:
    component: IPManager.vue (DHCP tab)
    effort: 0.5d
    description: "DHCP Lease 列表 + Make Static 一键绑定按钮"
    reference: RouterOS IP → DHCP → Leases → Make Static

  a4_log_visualization:
    component: SystemLog.vue
    effort: 0.5d
    description: "日志级别颜色高亮 + 级别统计"
    reference: RouterOS Log / pfSense syslog.php

b_tier:
  b1_diag_all_in_one:
    component: ToolsPage.vue + routes/tools.py
    effort: 2d
    description: "一站式诊断页面（Ping/Trace/DNS/Capture/BW/CoA）"
    reference: pfSense Diagnostics menu

  b2_interface_drilldown:
    component: InterfaceDetail.vue (new) + routes/extra.py
    effort: 3d
    description: "点击接口进入详情页（实时图/报文分布/错误/关联会话）"
    reference: RouterOS Interface detail

  b3_health_alerts:
    component: App.vue (topbar badge) + routes/system.py
    effort: 1d
    description: "服务状态异常 → 顶部告警铃铛"
    reference: OPNsense Health

  b4_radius_user_gui:
    component: AAAUsers.vue + routes/aaa.py
    effort: 2d
    description: "FreeRADIUS 用户管理 GUI（增删改查 RADIUS 属性）"
    reference: pfSense FreeRADIUS package
```

---

## 总结

RNAS 当前处于 **工具能用** 的阶段。对标 pfSense/RouterOS 等成熟项目，差距主要体现在三个方面：

1. **数据可视化** — 没有流量历史图、没有 hitcount 可视化、没有日志级别高亮
2. **交互效率** — 没有拖拽排序、没有一键绑定、没有端口转发向导、没有 drill-down
3. **系统管理** — 没有配置 Web UI、没有健康报警、没有证书管理

S 级和 A 级的 6 个功能加起来预估 **6-10 天**，完成后 RNAS 的可用性和专业感会提升一个档次，接近 pfSense 的体验水平。
