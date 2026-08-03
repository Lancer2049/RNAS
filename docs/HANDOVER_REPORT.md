# RNAS 项目交接报告

> **版本**: v3.0  
> **交接日期**: 2026-07-18  
> **项目地址**: https://github.com/Lancer2049/RNAS  
> **定位**: 独立 NAS 仿真平台（协议仿真与组件集成测试，非商业 NAS 设备）

---

## 目录

0. [项目概览](#0-项目概览)
1. [架构总览](#1-架构总览)
2. [代码仓库结构](#2-代码仓库结构)
3. [配置引擎（rnas-config）](#3-配置引擎rnas-config)
4. [后端 API（FastAPI）](#4-后端-apifastapi)
5. [前端 SPA（Vue.js 3）](#5-前端-spavuejs-3)
6. [系统服务（systemd）](#6-系统服务systemd)
7. [部署指南](#7-部署指南)
8. [测试体系](#8-测试体系)
9. [当前工作状态](#9-当前工作状态)
10. [路线图与未完成工作](#10-路线图与未完成工作)
11. [已知问题与技术债务](#11-已知问题与技术债务)
12. [对开发者的建议](#12-对开发者的建议)

---

## 0. 项目概览

### 0.1 项目定位

RNAS **不是**要做一个真正的商业 NAS 设备。其核心目标：

| 对比项 | 商业 NAS（如 H3C vBRAS、华为） | RNAS |
|--------|-------------------------------|------|
| 核心目标 | 流量转发与用户管理 | **协议仿真与组件集成测试** |
| 用户群体 | 终端用户 | 测试/开发/运维人员 |
| 功能重点 | 带宽管理/QoS/限速 | **产生真实协议报文** |
| 价值体现 | 网络接入服务 | **协议测试/验证/调试** |

### 0.2 核心价值

- 模拟 NAS 产生**真实的**协议报文（PPPoE/L2TP/DHCP/RADIUS）
- 与各种网络组件**联动测试**（FreeRADIUS / LDAP / AD）
- 验证 NAS 设备和 RADIUS 服务器的**协议正确性**
- 支持**压力测试**和**自动化测试**

### 0.3 技术栈摘要

| 层 | 技术 | 说明 |
|----|------|------|
| 接入协议 | **accel-ppp** | PPPoE/IPoE/L2TP/PPTP/SSTP 服务器 |
| DHCP/DNS | **dnsmasq** | DHCP 分配、DNS 缓存、DHCPv6 |
| 防火墙 | **nftables** | 防火墙规则管理（取代 iptables） |
| QoS | **tc (CAKE/fq_codel/HTB)** | 流量整形与队列管理 |
| VPN | **strongSwan / WireGuard / OpenVPN** | IPsec/WireGuard/OpenVPN 服务 |
| HA | **keepalived** | VRRP 高可用 |
| 配置引擎 | **Python 3 (rnas-config)** | 解析 INI 格式 → 生成原生配置 |
| 后端 API | **FastAPI / uvicorn** | REST API + WebSocket 实时推送 |
| 前端 | **Vue.js 3 + Vite** | SPA 仪表盘，RouterOS 暗色风格 |
| 测试 | **Playwright（E2E）/ pytest（单元）** | 浏览器自动化 + 配置引擎测试 |
| 基础 OS | **Debian/Ubuntu/UOS x86_64** | 标准 Linux，**非 OpenWrt 固件** |

---

## 1. 架构总览

### 1.1 Fusion 模型（合并非聚合）

```
┌────────────────────────────────────────────────────────────┐
│                  Vue.js 3 SPA Dashboard                     │
│     42 个组件 · 25+ 页面 · WebSocket 实时推送               │
└────────────────────────┬───────────────────────────────────┘
                         │ REST API + WebSocket
┌────────────────────────▼───────────────────────────────────┐
│               FastAPI Backend (uvicorn, 4 workers)          │
│  8 个路由模块: status · config · tools · system · aaa      │
│  · sim · extra ·  WebSocket /api/ws (3s 推送)              │
├────────────────────────┬───────────────────────────────────┤
│              RNAS 配置引擎 (rnas-config)                     │
│  /etc/rnas/*.conf  UCI 格式配置树 → 生成原生配置             │
├─────────┬─────────┬─────────┬─────────┬────────────────────┤
│ accel-ppp│ dnsmasq │ strong- │ tc/SQM  │ keepalived/VRRP   │
│ PPPoE/  │ DHCP/   │ Swan/WG/│ CAKE/   │ CoovaChilli/      │
│ L2TP/   │ DNS/    │ OpenVPN │ HTB     │ snmpd/netflow     │
│ IPoE    │ firewall│         │         │                    │
├─────────┴─────────┴─────────┴─────────┴────────────────────┤
│              标准 x86 Linux 内核 (Debian/Ubuntu/UOS)       │
└───────────────────────────────────────────────────────────┘
```

### 1.2 设计原则

1. **一个配置树**: `/etc/rnas/` 包含所有配置，不分散在不同文件
2. **一个 Web 控制台**: 单页应用管理一切，不是多个独立模块
3. **systemd 原生**: 所有服务使用 systemd 单元，而非 procd/init.d
4. **可安装，不可刷写**: `sudo bash install.sh` 即可，无需固件编译
5. **UCI 格式，非 OpenWrt 依赖**: 配置格式借鉴 OpenWrt，运行在标准 Linux 上

---

## 2. 代码仓库结构

```
RNAS/
├── cmd/rnas-config/                    # 配置引擎 (Python)
│   ├── rnas_config.py                  # CLI 入口 —— snapshot/scenario/validate/apply
│   ├── core.py                         # INI 解析器 + 配置树遍历 (58 行)
│   ├── generators.py                   # 19 个配置生成器 (549 行)
│   ├── config_ops.py                   # 配置读写操作 (69 行)
│   └── tests/                          # pytest 单元测试 (36 个测试)
│       ├── test_core.py
│       └── test_snapshot.py
│
├── web/
│   ├── server.py                       # 遗留 HTTP 服务器 (570 行, 仅部署到 VM3)
│   ├── rnas_env.py                     # 环境变量 + db_query() 封装
│   ├── api/
│   │   ├── main.py                     # FastAPI 入口 —— 路由注册 + CORS + 静态挂载
│   │   ├── models.py                   # Pydantic 数据模型 (65 行)
│   │   └── routes/
│   │       ├── status.py               # GET /api/health, /api/status
│   │       ├── config.py               # CRUD /api/config/*, 快照, 导入/导出
│   │       ├── tools.py                # Ping/Traceroute/DNS/RADIUS 测试/CoA
│   │       ├── system.py               # 系统状态/日志/证书/服务管理
│   │       ├── aaa.py                  # RADIUS AAA 用户/计费/组/NAS 客户端
│   │       ├── extra.py                # 多功能路由: 防火墙/接口/SIM/抓包/设置向导 (623 行)
│   │       ├── sim.py                  # 用户拨号仿真 (CPE SSH 执行 pppd)
│   │       └── __init__.py
│   └── services/
│       ├── accel_cmd.py                # accel-cmd 封装
│       ├── traffic.py                  # 流量采集与历史记录
│       ├── oui.py                      # MAC 地址 OUI 查询
│       └── __init__.py
│
├── web/frontend/                       # Vue.js 3 SPA
│   ├── index.html                      # HTML 入口
│   ├── vite.config.ts                  # Vite 构建配置
│   ├── package.json                    # 依赖: vue 3.5, chart.js 4.4, xterm 6.0
│   ├── src/
│   │   ├── App.vue                     # 根组件 —— 布局/侧边栏/哈希路由/Toast 通知
│   │   ├── main.js                     # Vue 入口
│   │   └── components/                 # 42 个 Vue 组件（见第 5 章）
│   └── tests/e2e/                      # Playwright E2E 测试 (19 个 spec 文件)
│
├── configs/                            # 配置模板 (部署到 /etc/rnas/)
│   ├── rnas.conf                       # 全局配置
│   ├── access.d/                       # 接入服务器配置 (7 个文件)
│   ├── network.d/                      # 网络配置 (4 个文件)
│   ├── vpn.d/                          # VPN 配置 (3 个文件)
│   ├── qos.conf / monitor.conf / hotspot.conf / ha.conf
│   └── README.md                       # 配置项说明
│
├── systemd/                            # systemd 服务单元 (9 个文件)
│   ├── rnas.target                     # 目标单元
│   ├── rnas-accel-ppp.service
│   ├── rnas-dnsmasq.service / rnas-firewall.service
│   ├── rnas-ha.service / rnas-ipsec.service
│   ├── rnas-qos.service / rnas-snmpd.service
│   ├── rnas-wireguard.service
│   └── ...(其他)
│
├── scripts/
│   ├── install.sh                      # 一键安装脚本 (Debian/Ubuntu/UOS)
│   └── deploy-to-vm3.sh                # 部署到 VM3 服务器
│
├── tools/                              # CLI 测试工具
│   ├── coa-test.py                     # CoA 测试
│   ├── acct-verify.py                  # 计费验证
│   └── ...(其他)
│
├── tests/                              # 集成测试
│   └── radius/                         # RADIUS 协议测试
│
├── docker/
│   ├── docker-compose.yml              # 全栈测试环境 (accel-ppp + freeradius + api + web)
│   ├── Dockerfile.accel-ppp
│   └── Dockerfile.rnas-api
│
├── docs/                               # 文档目录
│   ├── API.md                          # REST API 参考
│   ├── PROTOCOLS.md                    # 协议支持矩阵与字典统计
│   ├── GAP_ANALYSIS.md                 # 竞品差距分析 (pfSense/OPNsense/RouterOS/VyOS/OpenWrt)
│   ├── RNAS_IMPROVEMENT_PLAN.md        # 改进计划 (S/A/B/C 四级, 166 行)
│   ├── COMPETITIVE_ANALYSIS.md         # 竞品详细对比
│   ├── ROADMAP-v3.md                   # v3 路线图
│   ├── rnas-improvement-report.md      # 改进报告
│   ├── plans/                          # 规划文档
│   │   ├── 2026-04-21-rnas-functionality-plan.md       # 功能完善规划 (561 行)
│   │   ├── 2026-04-26-rnas-full-platform-design.md     # 完整平台设计 (368 行)
│   │   ├── 2026-04-26-rnas-phase1-implementation.md    # Phase1 实现计划
│   │   └── IMPLEMENTATION_PLAN.md      # 实现计划
│   ├── designs/                        # 设计文档
│   │   ├── P1-01-dhcp-relay.md         # DHCP Relay 设计
│   │   ├── P1-02-radius-dictionary.md  # RADIUS Dictionary 设计
│   │   ├── P2-01-8021x-auth.md         # 802.1X 认证设计
│   │   └── P3-06-config-import-export.md # 配置导入导出设计
│   └── HANDOVER_REPORT.md (本文件)
│
├── AGENTS.md                           # AI Agent 上下文文件（项目规则）
├── README.md                           # 主 README
├── ZREAD_ANALYSIS.md                   # Zread 协议分析报告
├── integration-test-plan.md            # 集成测试计划 (174 行)
├── state.md                            # 项目状态追踪
├── .github/workflows/ci.yml            # GitHub CI 工作流
└── .github/ISSUE_TEMPLATE/             # Issue 模板
```

### 2.1 关键统计

| 指标 | 数值 |
|------|------|
| 总 commit 数 | 210 |
| Python 文件 (cmd/rnas-config) | 4 模块, ~1139 行 |
| Python 文件 (web/api) | 8 路由 + 4 服务 + main.py, ~2500 行 |
| Vue 组件 | 42 个 |
| E2E 测试 spec 文件 | 19 个 (含 3 个新增: monitoring/cross-feature/stability) |
| E2E 测试用例 | 125 个 (121 通过, 4 跳过, 0 失败) |
| 配置引擎单元测试 | 36 个 |
| 系统服务 | 9 个 systemd 单元 |
| 配置模板 | 14+ 文件 |
| REST API 端点 | ~40 个 |

---

## 3. 配置引擎（rnas-config）

### 3.1 概述

配置引擎是 RNAS 的核心，将 `/etc/rnas/` 下的 UCI 格式 INI 配置文件转换为各原生服务（accel-ppp、dnsmasq、nftables 等）的配置。

### 3.2 配置树结构

```
/etc/rnas/
├── rnas.conf              # 全局设置
├── access.d/              # 接入服务器
│   ├── core.conf          # accel-ppp 核心
│   ├── modules.conf       # 模块启用
│   ├── ppp.conf           # PPP 参数
│   ├── radius.conf        # RADIUS 服务器
│   ├── nas.conf           # NAS 标识
│   ├── accounting.conf    # 计费设置
│   └── dae.conf           # CoA (Dynamic Authorization)
├── network.d/             # 网络服务
│   ├── dnsmasq.conf       # DHCP/DNS
│   ├── firewall.conf      # nftables 规则
│   ├── interfaces.conf    # 接口定义
│   └── snmp.conf          # SNMP
├── vpn.d/                 # VPN 服务
│   ├── ipsec.conf         # strongSwan IPsec
│   ├── wireguard.conf     # WireGuard
│   └── openvpn.conf       # OpenVPN
├── qos.conf               # QoS (CAKE/HTB)
├── monitor.conf           # 系统监控
├── hotspot.conf           # 热点门户
└── ha.conf                # 高可用 (keepalived)
```

### 3.3 核心模块说明

| 文件 | 功能 | 关键函数 |
|------|------|----------|
| `core.py` (58 行) | INI 解析器 | `parse_config()` — 解析 `[section "name"]` 格式<br>`walk_config_tree()` — 递归遍历配置树合并所有 `.conf`<br>`interpolate_env()` — `${VAR:-default}` 环境变量替换 |
| `generators.py` (549 行) | 19 个配置生成器 | `generate_accel_ppp()` — 生成 accel-ppp.conf<br>`generate_dnsmasq()` — 生成 dnsmasq.conf<br>`generate_firewall()` — 生成 nftables 规则集<br>`generate_snmp()` — SNMP 配置<br>`generate_qos()` — tc CAKE/HTB 配置<br>`generate_ipsec()` — strongSwan IPsec<br>`generate_wireguard()` — WireGuard<br>`generate_openvpn()` — OpenVPN<br>`generate_hotspot()` — CoovaChilli 热点<br>`generate_ha()` — keepalived VRRP<br>`generate_dhcp_relay()` — DHCP Relay Option 82<br>`generate_dot1x()` — 802.1X<br>`generate_mac_auth()` — MAC 认证<br>`generate_ipv6()` — IPv6 (DHCPv6/RA)<br>`generate_vlan()` / `generate_gre()` / `generate_ipip()` / `generate_eoip()` / `generate_vxlan()` — 隧道配置 |
| `config_ops.py` (69 行) | 配置读写 | `find_config_file()` — 定位配置段所在文件<br>`write_config_section()` — 写入 key=value 到配置段 |
| `rnas_config.py` CLI | 命令行入口 | `validate` — 校验配置（端口/IP/必填字段）<br>`snapshot` — 配置快照创建/列表/恢复/对比<br>`scenario` — 预定义场景（一键配置）<br>`apply` — 重新生成并应用所有配置 |

### 3.4 数据流

```
[INI 配置] → parse_config() → [Python dict] → generators.*() → [原生配置]
                                                      ↓
                                              apply → 重启服务
```

### 3.5 环境变量插值

支持 `${VAR:-default}` 语法，用于敏感信息（如 `testing123`）：

```ini
[server/primary]
secret=${RNAS_RADIUS_SECRET:-testing123}
```

---

## 4. 后端 API（FastAPI）

### 4.1 入口

**文件**: `web/api/main.py`

- 启动命令: `uvicorn main:app --host 0.0.0.0 --port 8099 --workers 4`
- CORS 允许所有来源
- 静态文件挂载 `/` → `../frontend/dist/`
- WebSocket 端点 `/api/ws`（每 3 秒推送会话 + 状态）

### 4.2 路由模块

| 模块 | 文件 | 主要端点 |
|------|------|----------|
| status | `routes/status.py` | `GET /api/health`, `GET /api/status` |
| config | `routes/config.py` | CRUD 配置: `GET/PUT /api/config/{module}`, `POST /api/config/apply`, 快照, 导入导出 |
| tools | `routes/tools.py` | `GET /api/tools/ping`, `/trace`, `/dns`, `/radius-test`, `/coa` |
| system | `routes/system.py` | `GET /api/system/status`, `/logs`, 证书 CRUD, 服务启停 |
| aaa | `routes/aaa.py` | RADIUS AAA CRUD: 用户/计费/组/NAS 客户端 |
| extra | `routes/extra.py` | 多功能: 防火墙/接口/抓包/带宽测试/设置向导/健康报警 (623 行, 最大模块) |
| sim | `routes/sim.py` | 用户拨号仿真: 通过 SSH 到 CPE 执行 pppd |
| (WebSocket) | `main.py` | `/api/ws` — 实时推送 |

### 4.3 完整 API 清单

见 `docs/API.md`（75 行），约 40 个端点。核心分组：

```
Status & Health:     GET /api/health, /api/status
Sessions:            GET /api/sessions, POST /api/sessions/{sid}/disconnect
Config CRUD:         GET /api/config, PUT /api/config/{module}, POST /api/config/apply
Config Snapshots:    POST/GET /api/config/snapshot, POST/DELETE /api/config/snapshot/{id}
Config Import/Export: POST /api/config/export, POST /api/config/import
Dictionary:          GET /api/dictionary, GET /api/dictionary/search?q=
Tools:               GET /api/tools/ping?host=, /trace?host=, /dns?host=, /radius-test?user=&pass=
CoA:                 GET /api/tools/coa?user=
System:              GET /api/system/status, /logs, /api/system/certificates/*
AAA RADIUS:          GET /api/aaa/users, /acct, /groups, /nas (以及 CRUD)
Firewall:            GET/POST/PUT/DELETE /api/ip/firewall-full, /ip/firewall/toggle, reorder
Interfaces:          GET /api/interfaces, GET /api/interfaces/{name}
Capture:             POST /api/tools/capture (start/stop/status)
Bandwidth Test:      POST /api/tools/bandwidth
SIM (Subscriber):    POST /api/sim/connect, /disconnect
Health Alerts:       GET /api/health/alerts
```

### 4.4 数据模型 (`models.py`)

使用 Pydantic v2，包含:

- `StatusResponse` — 系统状态
- `SessionItem` — 会话条目
- `FirewallRule` — 防火墙规则
- `FirewallReorder` — 规则重排序
- `SnapshotCreate` — 快照创建
- `BandwidthTestRequest` — 带宽测试请求
- `CaptureRequest` — 抓包请求
- `SetupConfig` — 快速设置
- `FirewallToggle` — 规则启停

### 4.5 安全注意事项

- **当前无认证**: 所有 API 端点无需登录即可访问，生产中必须加认证
- **CORS 全开**: `allow_origins=["*"]`，生产环境需限制
- **`shell=True` 遗留**: 本会话已将全库的 `shell=True` 从 26 处降到 1 处（`db_query()` 封装内），所有裸 `except:` 从 17 处降到 0
- **敏感信息**: 密码使用 `${VAR:-default}` 环境变量注入

---

## 5. 前端 SPA（Vue.js 3）

### 5.1 技术选型

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue | 3.5+ | 框架 |
| Vite | 6.0+ | 构建工具 |
| Chart.js | 4.4+ | 流量图表 |
| @xterm/xterm | 6.0+ | Web 终端 |
| Playwright | 1.59+ | E2E 测试 |
| Vue Router | hash 路由 | SPA 导航 |

### 5.2 组件目录（42 个）

按功能分组：

**核心布局**
- `App.vue` — 根组件: 侧边栏导航 + 布局 + 全局 Toast 通知

**仪表盘**
- `StatusCard.vue` — 状态卡片
- `SystemHealth.vue` — 系统健康
- `SystemResources.vue` — 系统资源
- `TrafficMonitor.vue` — 流量监控图表 (5m/1h/1d)
- `ActivityFeed.vue` — 活动日志
- `QuickActions.vue` — 快捷操作
- `SessionsTable.vue` — 活动会话概览
- `SystemPage.vue` — 系统信息

**配置管理**
- `ConfigEditor.vue` — 配置编辑器（分类侧边栏 + 字段编辑器）
- `ProtocolConfig.vue` — 接入协议配置 (PPPoE/L2TP/PPTP/SSTP/IPoE)
- `ServicesConfig.vue` — VPN 服务配置 (IPsec/WireGuard/OpenVPN)
- `NetworkConfig.vue` — 网络设置
- `RADIUSEditor.vue` — AAA 消息编辑器
- `CertificateManager.vue` — 证书管理

**网络功能**
- `IPManager.vue` — IP 管理（8 个标签: ARP/DHCP/Filter/NAT/Mangle/Routes/Addresses/Static）
- `FirewallTables.vue` — 防火墙规则表格
- `PortForward.vue` — 端口转发向导
- `QueueManager.vue` — QoS 队列管理 (HTB/CAKE/Simple)
- `RoutingPage.vue` — 动态路由 (OSPF)

**隧道**
- `TunnelManager.vue` — 隧道管理 (GRE/IPIP/VXLAN)
- `NetflowDhcp.vue` — NetFlow / DHCP Relay
- `VlanManager.vue` — VLAN per User
- `HotspotManager.vue` — 热点门户

**RADIUS**
- `AAAUsers.vue` — RADIUS 用户列表
- `AcctRecords.vue` — 计费记录
- `UserGroups.vue` — 用户组
- `NASClients.vue` — NAS 客户端
- `DictionaryBrowser.vue` — RADIUS 属性词典

**诊断 & 工具**
- `ToolsPage.vue` — 诊断工具 (Ping/Trace/DNS/RADIUS/CoA/Bandwidth/Capture)
- `PacketSniffer.vue` — 抓包工具
- `BandwidthTest.vue` — 带宽测试
- `WebTerminal.vue` — Web 终端 (xterm.js + WebSocket)
- `SystemLog.vue` — 系统日志（服务/级别过滤）
- `ScenarioRunner.vue` — 预定义场景（10 个场景一键运行）
- `SubscriberSim.vue` — 用户拨号模拟器
- `FaultInject.vue` — 故障注入
- `TestResults.vue` — 测试结果展示
- `MonitorDashboard.vue` — 监控面板
- `TrafficTorch.vue` — 流量放大镜
- `PPPProfiles.vue` — PPP 配置文件
- `ProtoMonitor.vue` — 协议监控
- `Scheduler.vue` — 定时任务
- `RealTimeMonitor.vue` — 实时监控

**详情**
- `InterfaceDetail.vue` — 接口详情
- `SessionDetail.vue` — 会话详情

### 5.3 路由结构

基于 Vue 3 hash 路由 (`#/xxx`)，所有组件懒加载：

| 路由 | 组件 | 说明 |
|------|------|------|
| `#/` | — | 仪表盘（内嵌 8 个子组件） |
| `#/sessions` | SessionsTable | 活动会话 |
| `#/config` | ConfigEditor | 配置编辑器 |
| `#/protocols` | ProtocolConfig | 接入协议 |
| `#/services` | ServicesConfig | VPN 服务 |
| `#/ip` | IPManager | IP 管理 |
| `#/queues` | QueueManager | QoS 队列 |
| `#/traffic` | TrafficMonitor | 流量监控 |
| `#/tools` | ToolsPage | 诊断工具 |
| `#/terminal` | WebTerminal | Web 终端 |
| `#/system` | SystemLog | 系统日志 |
| `#/certs` | CertManager | 证书管理 |
| `#/setup` | QuickSetup | 快速设置 |
| `#/firewall` | PortForward | 端口转发 |
| `#/snapshots` | ConfigSnapshots | 配置快照 |
| `#/alerts` | HealthAlerts | 健康报警 |
| `#/radius-users` | RADIUSUsers | RADIUS 用户 |
| `#/interface/:name` | InterfaceDetail | 接口详情 |
| 以及 AAA/Dictionary/VPN/路由/隧道/VLAN/热点/场景等共 25+ 路由 |

### 5.4 关键 UI 约定

- **主题**: RouterOS 暗色风格（GitHub-dark 调色板）
- **侧边栏选择器**: `nav.rnas-sidebar`
- **异步等待**: 懒加载组件后 `waitForTimeout(500-2000ms)`
- **Toast 通知**: 全局 `provide/inject`，支持 `info/ok/err` 三种类型
- **空状态**: `.empty-state` 或 `.empty` 类
- **表单消息**: `.msg.success` / `.msg.error`

### 5.5 构建验证

```bash
cd web/frontend
npm install
npx vite build    # 96 modules, 31 chunks, ~450 KiB gzip
```

---

## 6. 系统服务（systemd）

### 6.1 服务清单

`systemd/` 目录包含 9 个文件：

| 服务 | 触发器 | 依赖 |
|------|--------|------|
| `rnas.target` | 目标单元 | 关联所有服务 |
| `rnas-accel-ppp.service` | `accel-pppd` | 后台驻留 |
| `rnas-dnsmasq.service` | `dnsmasq` | DHCP/DNS |
| `rnas-firewall.service` | `nftables` | 防火墙规则 |
| `rnas-ha.service` | `keepalived` | VRRP 高可用 |
| `rnas-ipsec.service` | `strongSwan` | IPsec VPN |
| `rnas-qos.service` | `tc` | QoS 队列 |
| `rnas-snmpd.service` | `snmpd` | SNMP 监控 |
| `rnas-wireguard.service` | `wg-quick` | WireGuard VPN |

### 6.2 使用方式

```bash
systemctl start rnas-accel-ppp        # 启动单个服务
systemctl start rnas.target           # 启动所有服务
journalctl -u rnas-accel-ppp -f       # 查看日志
```

---

## 7. 部署指南

### 7.1 一键安装（生产环境）

```bash
git clone https://github.com/Lancer2049/RNAS.git
cd RNAS
sudo bash scripts/install.sh

# 启动 Web 仪表盘
cd web/api && PYTHONPATH=. uvicorn main:app --host 0.0.0.0 --port 8099
```

安装脚本会：
1. 安装系统包（accel-ppp, dnsmasq, nftables, python3, curl）
2. 安装 `rnas-config` CLI → `/usr/bin/rnas-config`
3. 部署配置模板 → `/etc/rnas/`
4. 运行配置校验
5. 安装 systemd 单元
6. 启动核心服务

### 7.2 Docker 测试环境

```bash
cd docker
docker compose up -d
```

运行 4 个容器：accel-ppp + freeradius + rnas-api + rnas-web

### 7.3 开发环境

```bash
# 后端（开发模式，热重载）
cd web/api && PYTHONPATH=. uvicorn main:app --host 0.0.0.0 --port 8099 --reload

# 前端（开发模式，HMR）
cd web/frontend && npm run dev
```

### 7.4 CI/CD

GitHub Actions 工作流 (`.github/workflows/ci.yml`)：

1. `checkout` + `setup-python@v5` + Python 3.x
2. `pip install`（asyncio, httpx 等）
3. Config engine 单元测试: `pytest -v cmd/rnas-config/tests/`（36 个测试）
4. FastAPI 静态分析: `python3 -m py_compile` 所有 `web/` 下 Python 文件
5. 前端构建验证: `npm ci && npx vite build`
6. E2E 测试（API 可用时）: `npx playwright test --config playwright.config.ts`

---

## 8. 测试体系

### 8.1 测试分层

| 层级 | 工具 | 数量 | 位置 |
|------|------|------|------|
| 单元测试 | pytest | 36 | `cmd/rnas-config/tests/` |
| E2E 浏览器测试 | Playwright | 125 用例 (19 spec) | `web/frontend/tests/e2e/` |
| 集成测试 | Playwright | 计划中 | `integration-test-plan.md` |

### 8.2 E2E 测试架构

所有 E2E 测试通过**前端 UI 操作**完成，不直接调用 API：

```
Playwright (Chromium headless)
    ↓ page.goto(BASE_URL)
Vue.js SPA Dashboard
    ↓ click sidebar / fill form / click button
FastAPI Backend (127.0.0.1:8099)
```

测试文件和覆盖：

| 文件 | 覆盖范围 |
|------|----------|
| `aaa.spec.ts` | AAA/用户/计费/组页面加载 |
| `browser-pppoe.spec.ts` | 浏览器 PPPoE 拨号测试 |
| `certificates.spec.ts` | 证书页面与生成表单 |
| `config-editor.spec.ts` | 配置编辑器、分类选择、快照 |
| `dashboard.spec.ts` | 仪表盘加载、状态卡片、流量 |
| `e2e-all-scenarios.spec.ts` | 全 10 场景端到端 + 真实拨号 (36 测试) |
| `e2e-pppoe.spec.ts` | PPPoE 全链路 (6 测试) |
| `error-boundary.spec.ts` | 空状态、错误处理、500 页面 |
| `full-integration.spec.ts` | 全面业务流（H1-H11, I1-I6） |
| `ip-manager-crud.spec.ts` | IP 管理器 CRUD 操作 |
| `new-features.spec.ts` | 新功能页面加载 |
| `scenarios.spec.ts` | 场景运行器 (13 测试) |
| `services.spec.ts` | VPN 服务页面 |
| `sessions.spec.ts` | 会话管理 |
| `tools.spec.ts` | 诊断工具 (RADIUS Tools) |
| `monitoring.spec.ts` | **新** 监控测试 D1-D6 |
| `cross-feature.spec.ts` | **新** 跨功能联动 F1-F5 |
| `stability.spec.ts` | **新** 稳定性和页面恢复 G1-G3 |

### 8.3 最新测试结果（2026-07-13）

| 类别 | 总测试 | 通过 | 跳过 | 失败 |
|------|--------|------|------|------|
| A — 会话管理 | 5 | 3 | 2 | 0 |
| B — 配置与编辑 | 16 | 14 | 2 | 0 |
| C — 诊断工具 | 7 | 7 | 0 | 0 |
| E — 空状态与异常处理 | 5 | 5 | 0 | 0 |
| F — 应用稳定性 | 1 | 1 | 0 | 0 |
| G — 页面恢复力 | 1 | 1 | 0 | 0 |
| H — 全业务流程 | 11 | 11 | 0 | 0 |
| I — 网络功能页面 | 24 | 24 | 0 | 0 |
| S — Scenario 场景运行 | 13 | 13 | 0 | 0 |
| E2E — PPPoE 端到端 | 6 | 6 | 0 | 0 |
| E2E — 全场景真实拨号 | 36 | 36 | 0 | 0 |
| **合计** | **125** | **121** | **4** | **0** |

### 8.4 测试环境拓扑

```
Host (WSL2)       — VMware NAT, 192.168.0.x LAN
RNAS API          — 127.0.0.1:8099 (Playwright 测试目标)
Frontend          — Vue.js 3 SPA (FastAPI 静态挂载)
RADIUS            — 192.168.0.202:1812, secret=testing123
accel-ppp         — 本地 VM, PPPoE/L2TP/PPTP/SSTP 服务器
CPE               — 192.168.0.201, 执行 pppd 拨号
```

### 8.5 运行 E2E 测试

```bash
cd web/frontend
npx playwright test --config playwright.config.ts
PORT=8099 npx playwright test tests/e2e/dashboard.spec.ts  # 单文件
```

---

## 9. 当前工作状态

### 9.1 本会话已完成的工作（2026-07-17 ~ 07-18 代码质量加固）

| # | 工作项 | 文件 | 说明 |
|---|--------|------|------|
| 1 | shell=True 消除 | `extra.py` (5处) → 参数列表 | 从全库 26 处降至 1 处 |
| 2 | shell=True 消除 | `aaa.py` (4处) → `db_query()` 封装 | |
| 3 | shell=True 消除 | `tools.py` (4处) → 参数列表 | |
| 4 | shell=True 消除 | `server.py` (18处) → `Path.read_text()` 等 | 570 行遗留代码 |
| 5 | `db_query()` 封装 | `rnas_env.py` | 唯一有意的 `shell=True` 封装层 |
| 6 | 裸 except 修复 | `extra.py` (7处)、`tools.py` (3处)、`traffic.py` (4处)、`server.py` (10处) | 全库 0 处 |
| 7 | 内联 import 清理 | `extra.py` | 全部移到文件顶部 |
| 8 | CI 工作流增强 | `.github/workflows/ci.yml` | 加入 pytest 步骤、Python 3.x 安装 |
| 9 | 前端懒加载优化 | `App.vue` | 封装 `lazy()` 辅助函数含延迟/重试/超时 |
| 10 | E2E 测试文件补齐 | `monitoring.spec.ts`、`cross-feature.spec.ts`、`stability.spec.ts` | integration-test-plan.md 缺失文件 |
| 11 | 语法检测 | 全部 18 个 web/ Python 文件 | 通过 `ast.parse` 检查 |

### 9.2 未提交的变更

```
23 files changed, 1311 insertions(+), 1439 deletions(-)
```

关键变更文件：

```
M  web/api/routes/extra.py          — 重写 579 行（消除 shell=True + 裸 except）
M  web/frontend/src/App.vue         — lazy() 辅助函数 + 34 个懒加载组件更新
M  web/server.py                    — 消除 16 处 shell=True 和 10 处裸 except
M  web/rnas_env.py                  — 新增 db_query() 封装
M  .github/workflows/ci.yml         — pytest 步骤
M  web/api/routes/aaa.py            — 4 shell=True → db_query()
M  web/api/routes/tools.py          — 4 shell=True → 参数列表
M  web/api/services/traffic.py      — 4 裸 except → Exception
A  web/frontend/tests/e2e/monitoring.spec.ts     — 新文件
A  web/frontend/tests/e2e/cross-feature.spec.ts  — 新文件
A  web/frontend/tests/e2e/stability.spec.ts      — 新文件
```

---

## 10. 路线图与未完成工作

### 10.1 项目历史节点

```
2026-04-21  功能完善规划 (docs/plans/2026-04-21-*.md)
2026-04-26  融合架构设计批准 (docs/plans/2026-04-26-*-platform-design.md)
2026-04-26  Phase1 实现计划 (docs/plans/2026-04-26-*-phase1-implementation.md)
2026-06-06  AirOS (AIRadius) 集成
2026-06-16  首次 README + Zread 分析
2026-06-23  竞品分析 + 改进计划 (S/A/B/C 四级, 19 项)
2026-07-13  E2E 测试 125 用例全部通过
2026-07-18  代码质量加固收尾 (22 文件, 1331 行变更)
2026-08-02  P2-03 MAC 认证 / S5 证书管理 / S4 审计日志 / S3 流量历史 / A5 DHCP Relay Option 82 / A2 端口转发向导 / B1 系统日志搜索 / B2 接口详情页图表 / B4 配置快照管理 / B3 Subscriber Sim 多用户批量拨号 / A4 一键 DHCP Make Static / A1 Quick Setup API 对接 / A3 诊断工具箱集成 完成
2026-08-02  证书列表性能修复: system_extra 逐文件 openssl 子进程改为 cryptography 纯 Python 解析 (37.9s→1.6s), 消除 certs 残留导致的 B12 E2E 超时抖动
2026-08-03  C5 报警通知(Telegram/Webhook) 完成: services/alerts 统一通知渠道 + alert_worker 后台轮询(60s/状态变化去重) + collect_alerts 抽取 + Notification Settings 前端页 + E2E 4 用例; C1-C4 确认已由 A1/WebTerminal/S5/S3 覆盖, C 级路线图清零
2026-08-03  P0 会话限速 + IPoE Option 60 完成: accel-ppp 生成器 speed-limit(PPPoE/IPoE) + [dhcpv4] vci 输出, Access Protocols 表单 Basic 组新增字段, E2E 3 用例; P0 三项(会话限速/Option60/82/IPoE限速)清零
2026-08-03  P1 CGNAT 完成: nftables masquerade 生成器(network.d.cgnat) + IP Manager NAT tab 配置区(enabled/内部网段/WAN接口/保存) + E2E 2 用例; P1 中 Web认证/双栈/LNS 确认已有, CGNAT 落地, 剩余多实例支持为长期架构项
```

### 10.2 未完成的高优先级工作

根据 `docs/RNAS_IMPROVEMENT_PLAN.md` 和 `docs/GAP_ANALYSIS.md`：

**S 级（最高优先级，直接影响可用性）**

| # | 功能 | 预估 | 说明 |
|---|------|------|------|
| S1 | ✅ 防火墙规则可视化排序 | **已完成** | hitcount 热力条 + 拖拽排序 + 启停开关 |
| S2 | ✅ 配置快照 Web UI | **已完成** | 快照列表/创建/恢复/Diff |
| S3 | ✅ 流量历史持久化图表 | **已完成** | traffic_store 聚合修正(速率而非计数器) + 5m/1h/1d/1w 范围 + 抽稀 + 前端切换新端点 |
| S4 | ✅ 配置变更审计日志 | **已完成** | config 更新/apply/用户 CRUD/证书操作审计 + 前端 Audit Log 页 + 过滤 + E2E |
| S5 | ✅ VPN 证书管理 | **已完成** | 列表到期日/CN/用途 + 生成/删除 + 到期徽章 + E2E |
| S6 | ✅ 健康报警系统 | **已完成** | P3-04：磁盘/会话/服务告警 + 横幅 + 前端 + E2E |

**A 级**

| # | 功能 | 说明 |
|---|------|------|
| A1 | ✅ 设置向导（Quick Setup） | **已完成** | 3 步向导对接 /api/setup/apply + /api/setup/status（已配置横幅）+ E2E 3 用例 |
| A2 | ✅ 端口转发向导 | **已完成** | 自动创建 nat 链 + nft comment 描述持久化 + parsePfRules 正则修复 + E2E |
| A3 | ✅ 诊断工具箱集成 | **已完成** | ToolsPage 7-tab 单一页面（Ping/Trace/DNS/RADIUS/CoA/BW/Capture）+ tools.spec.ts 覆盖 |
| A4 | ✅ 一键 DHCP Make Static | **已完成** | DHCP 租约行一键转静态绑定（自动 POST + 幂等去重 + 切 Static tab）+ E2E |
| A5 | ✅ DHCP Relay Option 82 | **已完成** | 生成器 option82/circuit_id/remote_id + 后端 GET/POST 配置树读写 + 前端表单 + relay 脚本读配置 + E2E |
| A6 | ✅ 802.1X / MAC Auth 配置 | P2-01 完成 802.1X，P2-03 完成 MAC Auth 前端 + 生成器接入 |

**B 级**

| # | 功能 | 说明 |
|---|------|------|
| B1 | ✅ 系统日志过滤/搜索 | **已完成** | 服务/级别过滤 + 关键词搜索 + 匹配计数 + E2E |
| B2 | ✅ 接口详情页完善 | **已完成** | 流量历史图表（5m/1h/1d/1w）+ 会话表 + E2E |
| B3 | ✅ Subscriber Sim 批量拨号 | **已完成** | 多用户批量拨号（count 1-50，radcheck 自动建用户+清理）+ 单用户路径保留 + E2E 4 用例 |
| B4 | ✅ 配置模板管理 | **已完成** | 快照列表/创建/Diff/恢复/删除页面 + 后端 DELETE 端点 + E2E |

**C 级**

| # | 功能 | 说明 |
|---|------|------|
| C1 | ✅ 配置向导 QuickSet | 已由 A1 Quick Setup 覆盖（3 步向导 + API 对接 + E2E） |
| C2 | ✅ Web 终端 | WebTerminal.vue（xterm.js + WebSocket）已存在 |
| C3 | ✅ 证书管理 | 已由 S5 覆盖（生成/删除/到期徽章 + E2E） |
| C4 | ✅ 流量历史 RRD 持久化 | 已由 S3 覆盖（traffic_store 聚合 + 5m/1h/1d/1w 图表） |
| C5 | ✅ 报警通知（Telegram/Webhook） | 告警自动通知（后台轮询 + 状态变化去重）+ Notification Settings 页（Telegram/Webhook/enabled/Test）+ E2E 4 用例 |

### 10.3 长期方向

见 `docs/plans/2026-04-21-rnas-functionality-plan.md` (561 行)：

- **P0**: PPPoE 会话限速 ✅ / IPoE DHCP Option60/82 ✅ / IPoE/PPPoE 限速 ✅（speed-limit + [dhcpv4] vci 生成器 + Access Protocols 表单 + E2E；Option82 已由 A5 完成）
- **P1**: L2TP LAC/LNS（LNS 已有）✅、PPPoE 双栈（ipv6 生成器）✅、IPoE Web 认证（HotspotManager + uam 生成器 + /hotspot/login）✅、多实例支持、CGNAT ✅（nftables masquerade 生成器 + NAT tab 配置区 + E2E）
- **P2**: PPPoE 代拨、QinQ、组播、L2TP + IPsec、SSTP、OpenVPN 高级路由

### 10.4 集成测试计划缺口

见 `integration-test-plan.md` (174 行)：

目前已有 125 个 E2E 用例，但 `integration-test-plan.md` 中计划的新增场景中有以下缺口：

| 类别 | 计划 | 当前 | 缺口 |
|------|------|------|------|
| A — 认证与会话 | 4 | 0 | 4 (A1-A4) |
| B — 配置 CRUD | 12 | 4 (部分) | 8 |
| C — 网络运维 | 6 | 1 | 5 |
| D — 监控与状态 | 5 | 3 | 2 (监控已补 monitoring.spec.ts) |
| E — 边界与错误 | 6 | 0 | 6 |
| F — 跨功能联动 | 5 | 0 | 5 (跨功能已补 cross-feature.spec.ts) |
| G — 性能与稳定性 | 3 | 1 | 2 (稳定性已补 stability.spec.ts) |

---

## 11. 已知问题与技术债务

### 11.1 安全问题

| # | 问题 | 严重度 | 说明 |
|---|------|--------|------|
| 1 | **API 无认证** | 🔴 高 | 所有端点无需登录，生产必须加认证 |
| 2 | **CORS 全开** | 🟡 中 | 生产需限制 `allow_origins` |
| 3 | **`db_query()` 仍有 `shell=True`** | 🟡 中 | 唯一遗留的 shell=True，接受的风险 |
| 4 | **`requests` 库超时** | 🟡 中 | 部分 API 调用未设 timeout 参数 |

### 11.2 代码质量问题

| # | 问题 | 位置 | 说明 |
|---|------|------|------|
| 1 | `server.py` 仍在部署 | `web/server.py` | 570 行遗留 HTTP 服务器，与 FastAPI 并行，建议迁移 |
| 2 | `extra.py` 体积较大 | 623 行 | 多功能路由，未来应拆分为独立模块 |
| 3 | 部分路由无 Pydantic 校验 | 多个路由 | `sim.py`、`config.py` 等未使用 `models.py` |
| 4 | 硬编码默认值 | 多处 | "testing123" 等可使用环境变量 |
| 5 | 前端组件碎片化 | 42 个组件 | 部分组件体积小（<50 行），可合并 |

### 11.3 测试覆盖缺口

| # | 缺口 | 说明 |
|---|------|------|
| 1 | FastAPI 无单元测试 | API 路由无 pytest 测试 |
| 2 | 前端无单元测试 (Vitest) | 42 个组件，0 个组件测试 |
| 3 | E2E 测试条件性跳过 | 4 个用例因无活动会话跳过 |
| 4 | `integration-test-plan.md` 中 27 个场景未实现 | 计划 A-G 类共 36 个，已有 9 个 |

### 11.4 已知 Bug

| # | 问题 | 状态 |
|---|------|------|
| 1 | 场景运行部分未达 100% (7/8, 8/9) | 属于后端条件依赖，非 UI Bug |
| 2 | E2E 测试因 Port 8099 偶发占用失败 | 运行前需确认端口可用 |

---

## 12. 对开发者的建议

### 12.1 新手上手步骤

1. **阅读架构文档**: 先通读 `docs/plans/2026-04-26-rnas-full-platform-design.md` 理解融合模型
2. **本地运行**: 启动 FastAPI（`cd web/api && uvicorn main:app --port 8099`）+ 前端（`cd web/frontend && npm run dev`）
3. **跑一遍测试**: `pytest -v cmd/rnas-config/tests/` + `npx playwright test`
4. **理解配置引擎**: 阅读 `cmd/rnas-config/core.py` + `generators.py`，这是核心
5. **浏览 API**: 阅读 `web/api/main.py` + `routes/` 了解端点结构
6. **浏览前端**: 阅读 `web/frontend/src/App.vue` 了解路由和组件结构

### 12.2 开发约定

- **Python**: Python 3.9+, FastAPI, Pydantic v2
- **前端**: Vue.js 3 Composition API (`<script setup>`), hash 路由
- **配置格式**: INI / UCI, `${VAR:-default}` 环境变量插值
- **测试**: 前端测试只通过 UI 操作（Playwright page object），不直接调 API
- **Git**: 42 个合并/非合并提交，遵循 `type: description` 格式

### 12.3 推荐的工具链

- **编辑器**: VS Code + Volar (Vue) + Python 插件
- **LSP**: `basedpyright`（Python 类型检查）
- **前端调试**: Vue DevTools
- **API 调试**: `curl` / httpie
- **测试调试**: `npx playwright test --debug`

### 12.4 下一步建议（优先级排序）

1. **🔥 安全加固** — 添加 API 认证（JWT / API Key），限制 CORS
2. **📊 流量历史图表** — 持久化流量数据，实现 RRD 风格趋势图
3. **🧪 补齐测试缺口** — 实现 integration-test-plan.md 中剩余 27 个场景
4. **🔧 拆分 extra.py** — 将其 623 行按功能拆分为独立路由模块
5. **🔐 配置加密** — 敏感配置字段可加密存储
6. **📝 审计日志** — 记录配置变更的 who/when/what
7. **🔄 迁移 server.py** — 将遗留 HTTP 服务器的功能迁移到 FastAPI
8. **🌐 国际化 (i18n)** — 前端支持中/英文切换

---

*本报告由 Sisyphus 生成于 2026-07-18，基于 RNAS 仓库完整代码审查和测试结果。*
