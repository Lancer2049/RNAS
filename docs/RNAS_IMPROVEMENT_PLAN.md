# RNAS 改进计划（合并版）

> **对标项目:** pfSense · OPNsense · MikroTik RouterOS · OpenWrt · VyOS
> **版本:** v1.0 | **日期:** 2026-06-23
> **来源:** `docs/rnas-improvement-report.md` + `docs/COMPETITIVE_ANALYSIS.md`

---

## 执行摘要

RNAS 技术底座（accel-ppp + nftables + FastAPI + Vue.js 3）选型合理，主要短板在**数据可视化**、**交互效率**、**系统管理**三个维度。

对标成熟项目，S级和A级的6项改进（预估8-10天）即可显著提升可用性，接近 pfSense 体验水平。

---

## 多维对比矩阵

| 功能域 | pfSense | OPNsense | RouterOS | VyOS | OpenWrt | RNAS |
|--------|---------|----------|----------|------|---------|------|
| 配置回滚 | ✅ XML backup | ✅ Config rev | ✅ /system backup | ✅ commit/rb | ❌ | ⚠️ CLI 无 UI |
| 流量历史图 | ✅ RRD graphs | ✅ Reporting | ✅ /tool graphing | ❌ | ⚠️ collectd | ❌ |
| 防火墙规则排序 | ✅ 拖拽 | ✅ 拖拽 | ✅ priority | ✅ priority | ✅ priority | ❌ 纯文本 |
| 端口转发向导 | ✅ wizard | ✅ wizard | ✅ /ip fw nat | ❌ | ✅ 模板 | ❌ |
| RADIUS 用户管理 | ✅ FreeRADIUS GUI | ✅ FreeRADIUS GUI | ✅ /radius | ❌ | ✅ freeradius3 | ⚠️ API 空 |
| DHCP 一键静态绑定 | ✅ | ✅ | ✅ Make Static | ⚠️ | ✅ | ⚠️ POST 无一键 |
| 证书管理 | ✅ System→Certs | ✅ Trust→Certs | ✅ /certificate | ❌ | ✅ CA | ❌ |
| Web 终端 | ✅ Command | ✅ Shell | ✅ /terminal | ✅ CLI | ✅ ttyd | ❌ |
| 健康报警 | ⚠️ 基本 | ✅ Monit | ✅ watchdog | ❌ | ❌ | ❌ |
| 诊断工具箱 | ✅ 一站式 | ✅ 菜单 | ✅ /tools | ✅ op mode | ✅ 工具 | ⚠️ 分散 |
| API 优先 | ⚠️ 部分 | ✅ 原生 REST | ✅ REST API | ✅ gRPC | ✅ ubus | ✅ FastAPI |

---

## 改进清单

### S 级（最高优先级 — 直接影响可用性）

#### S1: 防火墙规则可视化排序管理

| 项目 | 内容 |
|------|------|
| **现状** | 纯文本 nftables 规则，无法拖拽排序、无命中计数可视化 |
| **方案** | 后端 `/api/ip/firewall-full` 返回 handle + packet/byte count；前端拖拽（SortableJS）+ hitcount 热力条 + 启/禁用开关 |
| **参考** | pfSense firewall_rules.php、RouterOS IP → Firewall |
| **组件** | `IPManager.vue` + `routes/extra.py` |
| **预估** | 2d |
| **完成** | ⬜ |

#### S2: 配置快照/回滚 Web UI

| 项目 | 内容 |
|------|------|
| **现状** | CLI 已支持 `rnas-config snapshot`，但 Web 界面无法操作 |
| **方案** | 后端 3 个端点 + 前端 System→Snapshots 页面（列表/创建/恢复/diff） |
| **参考** | pfSense Diagnostics → Backup & Restore |
| **组件** | `SystemPage.vue` + `routes/config.py` |
| **预估** | 1.5d |
| **完成** | ⬜ |

---

### A 级（高优先级 — 提升专业感）

#### A1: 接口实时流量折线图

| 项目 | 内容 |
|------|------|
| **现状** | TrafficMonitor 有实时速率表格和 Chart.js 会话图，缺 per-interface 历史折线图 |
| **方案** | 后端 `/api/interfaces/history` 定时采集 `/sys/class/net/*/statistics/`，前端 Chart.js 多时间段（5m/1h/1d）双线图 |
| **参考** | RouterOS Graphs、pfSense status_graph.php |
| **组件** | `TrafficMonitor.vue` + `routes/extra.py` |
| **预估** | 3d |
| **完成** | ⬜ |

#### A2: 端口转发向导

| 项目 | 内容 |
|------|------|
| **现状** | NAT tab 有手动添加规则，缺标准端口转发引导 |
| **方案** | NAT tab 新增 Port Forward 子 tab：协议→外部端口→内部IP:端口→自动生成 dnat 规则 |
| **参考** | pfSense Firewall → NAT → Port Forward |
| **组件** | `IPManager.vue` (NAT sub-tab) |
| **预估** | 1d |
| **完成** | ⬜ |

#### A3: DHCP 一键静态绑定

| 项目 | 内容 |
|------|------|
| **现状** | Static tab 可手动添加，DHCP Leases 只能看不能一键绑定 |
| **方案** | DHCP Leases 每行加 "Make Static" 按钮，自动填充 MAC/IP→添加表单 |
| **参考** | RouterOS IP → DHCP → Leases → Make Static |
| **组件** | `IPManager.vue` (DHCP tab) |
| **预估** | 0.5d |
| **完成** | ⬜ |

#### A4: 系统日志可视化

| 项目 | 内容 |
|------|------|
| **现状** | SystemLog 组件原始 journalctl 输出，无颜色高亮 |
| **方案** | 日志行按 ERROR(红)/WARN(黄)/INFO(白)/DEBUG(灰)着色 + 级别统计 + filter chips |
| **参考** | RouterOS Log、pfSense syslog.php |
| **组件** | `SystemLog.vue` |
| **预估** | 0.5d |
| **完成** | ⬜ |

---

### B 级（中优先级 — 补齐功能）

| # | 功能 | 参考 | 组件 | 预估 |
|---|------|------|------|------|
| B1 | 诊断一站式页面（Ping/Trace/DNS/Capture/BW/CoA） | pfSense Diagnostics | `ToolsPage.vue` | 2d |
| B2 | 接口 Drill-Down 详情（实时图/报文分布/错误/关联Session） | RouterOS Interface | 新建 `InterfaceDetail.vue` | 3d |
| B3 | 服务健康报警（Topbar 铃铛） | OPNsense Health | `App.vue` topbar | 1d |
| B4 | RADIUS 用户管理 GUI（增删改查 + VSA 属性） | pfSense FreeRADIUS | `AAAUsers.vue` + `routes/aaa.py` | 2d |

### C 级（长期方向）

| # | 功能 | 参考 | 预估 |
|---|------|------|------|
| C1 | 配置向导 QuickSet（首次启动 3 步配置） | RouterOS QuickSet | 3d |
| C2 | Web 终端（xterm.js + WebSocket） | RouterOS /terminal | 2d |
| C3 | 证书管理（SSL/TLS 生成/导入） | pfSense System→Certs | 2d |
| C4 | 流量历史 RRD 持久化 | pfSense RRD graphs | 3d |
| C5 | 报警通知（邮件/Telegram/Webhook） | OPNsense Monit | 2d |

---

## 实施路线图

```
Phase 1 (S+A) · 6项 · 8.5d
┌─────────────────────────────────────────────────────────┐
│ S1 防火墙拖拽+hitcount     │████████████████░░░░░░  ██d  │
│ S2 配置快照 Web UI          │████████░░░░░░░░░░░░░░  ██d  │
│ A1 接口流量折线图           │██████████████████░░░░  ███d │
│ A2 端口转发向导             │████████░░░░░░░░░░░░░░  ██d │
│ A3 DHCP 一键静态绑定        │████░░░░░░░░░░░░░░░░░░  0.5d│
│ A4 日志可视化               │████░░░░░░░░░░░░░░░░░░  0.5d│
└─────────────────────────────────────────────────────────┘

Phase 2 (B) · 4项 · 8d
┌─────────────────────────────────────────────────────────┐
│ B1 诊断一站式               │████████████████░░░░░░  ██d  │
│ B2 接口 Drill-Down          │████████████████████░░  ███d │
│ B3 健康报警                 │████████░░░░░░░░░░░░░░  ██d  │
│ B4 RADIUS 用户管理 GUI      │████████████████░░░░░░  ██d  │
└─────────────────────────────────────────────────────────┘
```

---

## 实施顺序

严格按以下顺序执行，每项完成后运行 Playwright 验证无回归：

```
S1 → S2 → A1 → A2 → A3 → A4 → [Playwright 验证] → B1 → B2 → B3 → B4
```

---

**下一步:** S1 防火墙规则拖拽排序 + hitcount 可视化。
