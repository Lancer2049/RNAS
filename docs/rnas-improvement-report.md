# RNAS 软路由对标分析与改进建议

> **版本:** v1.0 | **日期:** 2026-06-23
> **对标项目:** pfSense · OPNsense · MikroTik RouterOS · OpenWrt · VyOS
> **用途:** 供 opencode 进行 RNAS 项目改进的实施参考

---

## 目录

1. [执行摘要](#1-执行摘要)
2. [RNAS 项目现状概览](#2-rnas-项目现状概览)
3. [2025-2026 主流软路由生态调研](#3-2025-2026-主流软路由生态调研)
4. [多维对比矩阵](#4-多维对比矩阵)
5. [差距分析与改进建议](#5-差距分析与改进建议)
6. [架构优化措施](#6-架构优化措施)
7. [实施路线图](#7-实施路线图)
8. [总结](#8-总结)

---

## 1. 执行摘要

RNAS（Reliable Network Access Server）是一个面向 ISP/运营商场景的开源网络接入服务器平台，基于 Python 3.12 + FastAPI + Vue.js 3 构建，底层依赖 accel-ppp 实现多协议接入（PPPoE/L2TP/PPTP/SSTP/IPoE）。项目在**协议覆盖广度**和**配置引擎设计**上具有显著优势，支持 13 家厂商 VSA、IPv6 双栈、VRRP 高可用和完整的测试金字塔。

然而，对标 pfSense、OPNsense、RouterOS v7、OpenWrt 24.10 和 VyOS 等成熟项目，RNAS 在**数据可视化**、**交互效率**和**系统管理**三个维度存在明显差距。本报告基于 2025-2026 年最新软路由生态调研，提出覆盖 S/A/B/C 四个优先级的 19 项改进建议，以及 7 项架构优化措施，预估总投入 32-37 人天，分三个阶段实施。

**核心结论：** RNAS 的技术底座（accel-ppp + nftables + FastAPI + INI 配置引擎）选型合理且架构清晰，主要短板集中在 Web 管理界面的可视化深度和运维便利性上。S 级和 A 级的 6 项改进（预估 8-10 天）即可显著提升可用性，使其接近 pfSense 的体验水平。

---

## 2. RNAS 项目现状概览

### 2.1 技术架构

RNAS 采用五层分层架构，将配置管理、协议接入、网络服务和运维管理解耦为独立子系统：

| 层级 | 技术组件 | 职责 |
|------|----------|------|
| 管理层 | Vue.js 3 前端 + FastAPI REST API + rnas-config CLI | Web 仪表盘、API 接口、命令行配置 |
| 控制层 | INI 配置引擎 + WebSocket 实时推送 + systemd 编排 | 配置解析/生成/验证、实时数据推送 |
| 接入层 | accel-ppp（PPPoE/L2TP/PPTP/SSTP/IPoE） | 多协议用户接入与认证 |
| 服务层 | dnsmasq + nftables + tc(QoS) + StrongSwan/WG/OVPN + Keepalived | DHCP/DNS、防火墙、限速、VPN、高可用 |
| 基础设施层 | FreeRADIUS + PostgreSQL + Linux Kernel | AAA 认证计费、数据持久化、内核网络栈 |

### 2.2 核心能力清单

- **多协议接入:** PPPoE、L2TP、PPTP、SSTP、IPoE（DHCP 触发），通过 accel-ppp 统一管理
- **AAA 与 RADIUS:** 完整认证/授权/计费，CoA 动态授权，13 家厂商 VSA 支持
- **配置引擎:** INI 配置树 + 环境变量插值 + 场景覆盖 + 快照/回滚
- **网络服务:** DHCP/DNS、nftables 防火墙、CAKE/HTB QoS、IPv6 双栈、动态 VLAN
- **VPN 与隧道:** IPsec、WireGuard、OpenVPN、GRE、IPIP、EoIP、VXLAN
- **高可用与测试:** Keepalived VRRP 主备切换、集成/压力/故障注入测试套件

### 2.3 API 路由架构

| 模块 | 前缀 | 核心端点 | 功能 |
|------|------|----------|------|
| status.py | `/api/status` | GET /api/status, /api/interfaces | 服务状态、会话列表、接口统计 |
| config.py | `/api/config` | GET/PUT /api/config/{module} | 配置获取/更新/验证 |
| tools.py | `/api/tools` | POST /api/tools/ping, /traceroute | Ping、Traceroute 诊断 |
| system.py | `/api/system` | GET /api/system/services | 服务列表、重启 |
| aaa.py | `/api/aaa` | POST /api/aaa/auth-test, /coa | RADIUS 认证测试、CoA、断开 |
| extra.py | `/api/extra` | GET /api/extra/logs | 日志查询、IP/DHCP/防火墙管理 |

### 2.4 关键短板

- AAA Users API 返回空（数据在 FreeRADIUS 文件/SQL 中但未对接）
- 防火墙规则仅纯文本显示（无拖拽排序/命中计数）
- 无流量历史图、无配置 Web UI、无健康报警、无证书管理

---

## 3. 2025-2026 主流软路由生态调研

### 3.1 OpenWrt 24.10（2025 年 2 月发布）

OpenWrt 24.10 是自 23.05 分支以来包含 5400+ 次提交的重大稳定版本。核心更新：

- **Linux 内核 6.6:** 从 23.05 的内核 5.15/6.1 升级至 6.6 LTS，带来更好的硬件兼容性和安全补丁
- **初始 Wi-Fi 7 支持:** 初步支持 802.11be（Wi-Fi 7）标准，为下一代无线网络做好准备
- **MPTCP（多路径 TCP）:** 支持多路径 TCP，提升网络连接的可靠性和带宽利用率
- **LLDP 优化:** 改进链路层发现协议支持，增强网络环境识别能力
- **LuCI 改进:** UCI 配置系统、cbi 自动表单生成、luci-app-* 模块化包体系持续完善
- **nftables 防火墙:** fw4 防火墙完全基于 nftables，支持区域化配置和流量整形

### 3.2 pfSense CE 2.7+ / Plus

pfSense 是 Netgate 推出的企业级防火墙软件，分为 CE（社区版，免费）和 Plus（付费版）。核心特性：

- **WireGuard 原生集成:** 从 2.6 开始内置 WireGuard VPN 支持，配置简便
- **RRDtool 流量历史:** 提供 1h/24h/7d/30d/1y 多时间维度流量历史折线图
- **Widget 化 Dashboard:** 可自由拖拽排列的仪表盘小组件系统
- **配置备份/回滚:** XML 配置文件 + 历史版本 + 一键恢复
- **FreeRADIUS 包:** 内置 FreeRADIUS 包，提供用户/计费管理 GUI
- **防火墙规则拖拽排序:** 每条规则一行，拖拽改变顺序，彩色标记启用状态
- **诊断工具一站式页面:** Ping/Traceroute/DNS Lookup/Packet Capture 集中管理

### 3.3 OPNsense 24.x / 25.x

OPNsense 是 2015 年从 pfSense 分支出来的项目，采用 MVC 架构（Phalcon 框架）。核心优势：

- **原生 REST API:** 每个 UI 操作背后都是 API 调用，Swagger 文档完备
- **Netdata 集成:** 内置实时系统监控，Health 报警机制
- **Reporting 子系统:** 按时间范围查询历史数据，自成体系的报表系统
- **configctl CLI:** 通过 CLI 执行任意 API 操作，前后端分离最佳实践
- **入侵检测/预防（IDS/IPS）:** 内置 Suricata 集成
- **插件系统:** 模块化插件架构，可按需安装功能扩展
- **审计日志:** 完整的操作审计追踪

### 3.4 MikroTik RouterOS v7+

RouterOS v7 是 MikroTik 的重大版本升级，引入了全新的 BGP/OSPF 实现和容器支持。核心特性：

- **WireGuard 全面支持:** 7.x 版本全面支持 WireGuard VPN，性能优异
- **容器（Container）支持:** v7.18 支持在路由器上运行 Docker 容器
- **REST API:** 提供 RESTful API 接口，支持 JSON 格式
- **QuickSet 向导:** 首次启动一键配置 LAN/WAN/PPPoE/RADIUS
- **Torch 实时流量分析:** 按 IP/端口/协议实时分析流量构成
- **多级 Drill-Down:** Interface 列表 → 点击进入详情 → 实时流量/状态页
- **WinBox + WebFig + CLI:** 三种管理界面，原生桌面应用 + Web + 命令行
- **Graphing 工具:** 接口/队列/防火墙规则的实时和历史流量图

### 3.5 VyOS 1.4+（Sagitta）

VyOS 是基于 Debian GNU/Linux 的开源软路由，提供类似 Cisco IOS/Juniper JUNOS 的 CLI 体验。核心特性：

- **配置事务模型:** configure → set → commit → save，支持配置回滚和版本化 commit
- **compare/rollback 命令:** 配置差异对比和一键回滚
- **操作模式/配置模式分离:** 查看 vs 修改的权限边界清晰
- **配置即代码:** 支持版本控制和自动化部署
- **gRPC/HTTP API:** 提供编程接口用于自动化管理

---

## 4. 多维对比矩阵

### 4.1 功能维度对比

| 功能域 | pfSense | OPNsense | RouterOS | VyOS | OpenWrt | RNAS 当前 |
|--------|---------|----------|----------|------|---------|-----------|
| 配置回滚 | ✅ XML backup+restore | ✅ Config revisions | ✅ /system backup | ✅ commit/rollback | ❌ | ⚠️ CLI snapshot 无 UI |
| 流量历史图 | ✅ RRD 多时段 | ✅ Reporting graphs | ✅ /tool graphing | ❌ | ⚠️ collectd | ❌ |
| 防火墙规则排序 | ✅ 拖拽排序 | ✅ 拖拽排序 | ✅ 数字优先级 | ✅ rule 编号 | ✅ 数字优先级 | ❌ 纯文本 |
| 端口转发向导 | ✅ NAT wizard | ✅ 同左 | ✅ CLI 配置 | ❌ | ✅ 转发模板 | ❌ |
| RADIUS 用户管理 | ✅ FreeRADIUS GUI | ✅ FreeRADIUS GUI | ✅ /radius | ❌ | ✅ freeradius3 | ⚠️ API 返回空 |
| PPPoE 服务器 | ✅ accel-ppp | ✅ accel-ppp | ✅ 原生支持 | ❌ | ✅ accel-ppp | ✅ 有但无向导 |
| DHCP 静态绑定 | ✅ 一键绑定 | ✅ 一键绑定 | ✅ Make Static | ⚠️ 文件配置 | ✅ 类似 | ⚠️ API 无一键 |
| 证书管理 | ✅ System→Certs | ✅ Trust→Certs | ✅ /certificate | ❌ | ✅ CA 管理 | ❌ |
| Web 终端 | ✅ Diagnostics | ✅ Shell | ✅ /terminal | ✅ 原生 CLI | ✅ ttyd | ❌ |
| 健康报警 | ⚠️ 基本 | ✅ Monit+通知 | ✅ watchdog | ❌ | ❌ | ❌ |
| 实时会话图 | ✅ status_graph | ✅ Reporting | ✅ 浮动窗口 | ⚠️ 基本 | ❌ | ⚠️ 有表格无图 |
| 配置向导 | ✅ Setup wizard | ✅ Setup wizard | ✅ QuickSet | ❌ | ❌ | ❌ |
| 诊断工具箱 | ✅ 一站式 | ✅ Diagnostics | ✅ /tools | ✅ operational | ✅ 系统→工具 | ⚠️ 分散多页 |
| API 优先 | ⚠️ 部分 | ✅ 原生 REST | ✅ REST API | ✅ gRPC/HTTP | ✅ ubus RPC | ✅ FastAPI 有缺口 |
| 插件/包系统 | ✅ Package Mgr | ✅ Plugins | ⚠️ 可扩展 | ❌ | ✅ opkg | ❌ |
| IDS/IPS | ✅ Suricata 包 | ✅ 内置 Suricata | ❌ | ❌ | ⚠️ 可用包 | ❌ |
| 容器支持 | ❌ | ❌ | ✅ v7.18+ | ❌ | ⚠️ Docker | ❌ |

### 4.2 RNAS 独有优势

尽管在 Web 管理层面存在差距，RNAS 在以下方面具有对标项目不具备或较弱的优势：

- **ISP/运营商级接入能力:** 同时支持 PPPoE + L2TP + PPTP + SSTP + IPoE 五种接入协议，pfSense/OPNsense 主要面向防火墙/VPN 场景，接入协议覆盖不如 RNAS
- **13 家厂商 VSA 支持:** 内置 Cisco/Juniper/MikroTik/Huawei/ZTE 等 13 家厂商的 RADIUS VSA 解析，运营商多厂商环境适配能力强
- **INI 配置引擎:** 统一的 INI 配置树 + 环境变量插值 + 场景覆盖，比 pfSense 的 XML 配置更适合 DevOps 和容器化部署
- **完整的测试金字塔:** 从单元测试到压力测试、故障注入测试的完整测试体系，OpenWrt/RouterOS 均不具备同等测试覆盖
- **QoS CAKE 算法:** 支持先进的 CAKE 队列管理算法，比 pfSense 的传统 HFSC/ALTQ 更现代
- **动态 VLAN 分配:** 基于 RADIUS 属性的动态 VLAN 分配，企业网络隔离能力强

---

## 5. 差距分析与改进建议

基于对标分析，以下改进建议按优先级分为 S/A/B/C 四个层级。S 级直接影响可用性，A 级提升专业感，B 级完善运维体验，C 级面向未来方向。

### S-Tier（最高优先级 — 直接影响可用性）

#### S1: 防火墙规则可视化排序管理

**现状:** 仅有纯文本 nftables 规则显示，无法拖拽排序、无法直观看到规则命中计数。

**方案:**
- 后端: 增强 `GET /api/ip/firewall-full`，返回每条规则的 `handle` + `packet_count` + `byte_count` + `position`
- 前端: 拖拽排序（SortableJS），hitcount 彩色柱状条，规则启/禁用开关
- 利用 nftables 的 `nft -j list ruleset` JSON 输出获取计数器

**后端实现示例:**
```python
# web/api/routers/extra.py
@router.get("/ip/firewall-full")
async def get_firewall_full():
    """返回带计数器的完整防火墙规则列表"""
    result = subprocess.run(
        ["nft", "-j", "list", "ruleset"],
        capture_output=True, text=True, timeout=10
    )
    ruleset = json.loads(result.stdout)
    rules = []
    position = 0
    for obj in ruleset.get("nftables", []):
        if "rule" in obj:
            rule = obj["rule"]
            rules.append({
                "handle": rule.get("handle"),
                "chain": rule.get("chain"),
                "expr": rule.get("expr", []),
                "position": position,
                "packet_count": _extract_counter(rule, "packets"),
                "byte_count": _extract_counter(rule, "bytes"),
                "enabled": True  # 从 comment 或标记位解析
            })
            position += 1
    return {"rules": rules}

def _extract_counter(rule, field):
    """从规则表达式中提取计数器值"""
    for expr in rule.get("expr", []):
        if isinstance(expr, dict) and "counter" in expr:
            return expr["counter"].get(field, 0)
    return 0
```

**前端实现示例:**
```vue
<!-- web/frontend/src/components/IPManager.vue -->
<template>
  <div class="firewall-rules">
    <draggable
      v-model="rules"
      item-key="handle"
      @end="onDragEnd"
      handle=".drag-handle"
    >
      <template #item="{ element, index }">
        <div class="rule-row" :class="{ disabled: !element.enabled }">
          <span class="drag-handle">⋮⋮</span>
          <el-switch v-model="element.enabled" @change="toggleRule(element)" />
          <span class="rule-position">{{ index + 1 }}</span>
          <span class="rule-expr">{{ formatRule(element.expr) }}</span>
          <div class="hitcount-bar">
            <div class="bar" :style="{ width: hitPercent(element) + '%' }"></div>
            <span>{{ formatBytes(element.byte_count) }}</span>
          </div>
        </div>
      </template>
    </draggable>
  </div>
</template>
```

**参考:** pfSense firewall rules table
**预估:** 2 人天 | **组件:** `IPManager.vue` + `routes/extra.py`

---

#### S2: 配置备份/快照/回滚 Web UI

**现状:** CLI 已支持 `rnas-config snapshot`，但无法通过 Web 界面操作。

**方案:**
- 后端: `GET /api/config/snapshots` 列表、`POST /api/config/snapshot` 创建、`POST /api/config/snapshot/{name}/restore`
- 前端: System → Snapshots 页面，显示快照列表 + 创建/恢复按钮 + diff 对比
- 借鉴 VyOS 的 commit/rollback 事务语义，增加配置变更预览

**后端实现示例:**
```python
# web/api/routers/config.py
import shutil
from datetime import datetime
from pathlib import Path

SNAPSHOT_DIR = Path("/etc/rnas/.snapshots")

@router.get("/config/snapshots")
async def list_snapshots():
    """列出所有配置快照"""
    snapshots = []
    if SNAPSHOT_DIR.exists():
        for snap in sorted(SNAPSHOT_DIR.iterdir()):
            stat = snap.stat()
            snapshots.append({
                "name": snap.name,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "size": stat.st_size
            })
    return {"snapshots": snapshots}

@router.post("/config/snapshot")
async def create_snapshot(name: str = None):
    """创建配置快照"""
    if not name:
        name = f"snapshot-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    target = SNAPSHOT_DIR / name
    shutil.copytree("/etc/rnas", target)
    return {"status": "created", "name": name}

@router.post("/config/snapshot/{name}/restore")
async def restore_snapshot(name: str):
    """恢复配置快照"""
    source = SNAPSHOT_DIR / name
    if not source.exists():
        raise HTTPException(404, f"Snapshot '{name}' not found")
    # 先备份当前配置
    await create_snapshot(f"pre-restore-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    shutil.rmtree("/etc/rnas")
    shutil.copytree(source, "/etc/rnas")
    # 重新生成并应用配置
    subprocess.run(["rnas-config", "validate", "--root", "/etc/rnas/"])
    subprocess.run(["systemctl", "restart", "rnas.target"])
    return {"status": "restored", "name": name}

@router.get("/config/snapshot/{name}/diff")
async def diff_snapshot(name: str):
    """对比快照与当前配置的差异"""
    source = SNAPSHOT_DIR / name
    result = subprocess.run(
        ["diff", "-ru", str(source), "/etc/rnas"],
        capture_output=True, text=True
    )
    return {"diff": result.stdout}
```

**参考:** pfSense Diagnostics → Backup & Restore / VyOS commit rollback
**预估:** 1.5 人天 | **组件:** `SystemPage.vue` + `routes/config.py`

---

### A-Tier（高优先级 — 提升专业感）

#### A1: 接口实时流量图（RRD 风格）

**现状:** TrafficMonitor 有实时速率表格和 Chart.js 会话图，但缺每个接口的历史速率折线图（5 分钟 / 1 小时 / 1 天 / 1 周）。

**方案:**
- 后端: 新增 `/api/interfaces/history?name=ens33&range=1h`，后端定时轮询 `/sys/class/net/{iface}/statistics/`，存储环形缓冲区
- 前端: Chart.js 多时间段选择（5m / 1h / 1d / 1w），叠加 RX/TX 双线，平滑曲线
- 可选: 引入 SQLite 或 RRDtool 做持久化存储，支持更长历史

**后端实现示例:**
```python
# web/api/routers/extra.py
import time
from collections import deque
from threading import Thread

# 环形缓冲区: {iface: {timestamp, rx_bytes, tx_bytes}}
traffic_history = {}
HISTORY_MAX = 2016  # 7天 * 288(5分钟间隔)

class TrafficCollector(Thread):
    """后台线程: 每5秒采集接口流量"""
    def __init__(self):
        super().__init__(daemon=True)
        self.last_stats = {}

    def run(self):
        while True:
            self.collect()
            time.sleep(5)

    def collect(self):
        for iface in self.get_interfaces():
            stats = self.read_stats(iface)
            now = time.time()
            if iface in self.last_stats:
                prev = self.last_stats[iface]
                dt = now - prev['ts']
                rx_rate = (stats['rx'] - prev['rx']) / dt
                tx_rate = (stats['tx'] - prev['tx']) / dt
                if iface not in traffic_history:
                    traffic_history[iface] = deque(maxlen=HISTORY_MAX)
                traffic_history[iface].append({
                    'ts': now, 'rx_rate': rx_rate, 'tx_rate': tx_rate
                })
            self.last_stats[iface] = {'ts': now, 'rx': stats['rx'], 'tx': stats['tx']}

    def read_stats(self, iface):
        base = f"/sys/class/net/{iface}/statistics"
        with open(f"{base}/rx_bytes") as f:
            rx = int(f.read())
        with open(f"{base}/tx_bytes") as f:
            tx = int(f.read())
        return {'rx': rx, 'tx': tx}

# 启动采集器
collector = TrafficCollector()
collector.start()

@router.get("/interfaces/history")
async def get_interface_history(name: str, range: str = "1h"):
    """获取接口历史流量数据"""
    range_seconds = {"5m": 300, "1h": 3600, "1d": 86400, "1w": 604800}
    seconds = range_seconds.get(range, 3600)
    now = time.time()
    cutoff = now - seconds

    history = traffic_history.get(name, [])
    data = [
        {
            "timestamp": point['ts'],
            "rx_bps": point['rx_rate'] * 8,  # 转换为 bits
            "tx_bps": point['tx_rate'] * 8
        }
        for point in history if point['ts'] >= cutoff
    ]
    return {"interface": name, "range": range, "data": data}
```

**参考:** pfSense RRD graphs / RouterOS Graphs / OPNsense Reporting
**预估:** 3 人天 | **组件:** `TrafficMonitor.vue` + `routes/extra.py`

---

#### A2: 端口转发向导

**现状:** NAT tab 有手动添加规则的表单，但缺少标准端口转发引导界面。

**方案:**
- 前端: NAT tab 增加 Port Forward 子 tab，表单: 协议(TCP/UDP) → 外部端口 → 内部 IP → 内部端口 → 描述
- 后端: 自动生成 `dnat to` 规则，调用 `POST /api/ip/firewall`
- 支持批量导入（CSV）和常用端口预设（HTTP/HTTPS/SSH/RDP）

**前端实现示例:**
```vue
<!-- web/frontend/src/components/PortForwardWizard.vue -->
<template>
  <div class="port-forward-wizard">
    <h3>端口转发向导</h3>
    <el-form :model="form" label-width="120px">
      <el-form-item label="协议">
        <el-select v-model="form.protocol">
          <el-option label="TCP" value="tcp" />
          <el-option label="UDP" value="udp" />
          <el-option label="TCP/UDP" value="tcpudp" />
        </el-select>
      </el-form-item>
      <el-form-item label="外部端口">
        <el-input-number v-model="form.externalPort" :min="1" :max="65535" />
      </el-form-item>
      <el-form-item label="内部 IP">
        <el-input v-model="form.internalIP" placeholder="192.168.1.100" />
      </el-form-item>
      <el-form-item label="内部端口">
        <el-input-number v-model="form.internalPort" :min="1" :max="65535" />
      </el-form-item>
      <el-form-item label="描述">
        <el-input v-model="form.description" placeholder="Web Server" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="submit">添加转发规则</el-button>
      </el-form-item>
    </el-form>

    <!-- 预设快捷按钮 -->
    <div class="presets">
      <el-button size="small" @click="preset('http')">HTTP (80→80)</el-button>
      <el-button size="small" @click="preset('https')">HTTPS (443→443)</el-button>
      <el-button size="small" @click="preset('ssh')">SSH (22→22)</el-button>
      <el-button size="small" @click="preset('rdp')">RDP (3389→3389)</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'

const form = ref({
  protocol: 'tcp',
  externalPort: 80,
  internalIP: '',
  internalPort: 80,
  description: ''
})

const submit = async () => {
  // 自动生成 nftables dnat 规则
  const rule = `${form.value.protocol} dport ${form.value.externalPort} dnat to ${form.value.internalIP}:${form.value.internalPort}`
  await axios.post('/api/ip/firewall', {
    action: 'add',
    chain: 'prerouting',
    rule: rule,
    comment: form.value.description
  })
}

const preset = (type) => {
  const presets = {
    http: { externalPort: 80, internalPort: 80, description: 'HTTP Web Server' },
    https: { externalPort: 443, internalPort: 443, description: 'HTTPS Web Server' },
    ssh: { externalPort: 22, internalPort: 22, description: 'SSH Access' },
    rdp: { externalPort: 3389, internalPort: 3389, description: 'Remote Desktop' }
  }
  Object.assign(form.value, presets[type])
}
</script>
```

**参考:** pfSense Firewall → NAT → Port Forward
**预估:** 1 人天 | **组件:** `IPManager.vue` (NAT tab)

---

#### A3: DHCP 一键静态绑定

**现状:** Static tab 允许手动添加 MAC→IP 绑定，但需手动输入所有信息。DHCP Leases tab 显示当前租约，但无法一键转换。

**方案:**
- 前端: DHCP Leases tab 每行加 "Make Static" 按钮，点击自动填充 MAC/IP/hostname 到添加表单
- 后端: `POST /api/ip/dhcp-static` 已支持，增加 `POST /api/ip/dhcp-lease/{mac}/make-static` 便捷端点

**后端实现示例:**
```python
# web/api/routers/extra.py
@router.post("/ip/dhcp-lease/{mac}/make-static")
async def make_static(mac: str):
    """将当前 DHCP 租约转换为静态绑定"""
    # 从 dnsmasq leases 文件读取租约信息
    leases = parse_dnsmasq_leases("/var/lib/misc/dnsmasq.leases")
    lease = leases.get(mac)
    if not lease:
        raise HTTPException(404, f"Lease for {mac} not found")

    # 读取当前静态绑定配置
    config = load_config("network.d.dhcp")
    static_leases = config.get("static_leases", "")

    # 添加新的静态绑定
    new_entry = f"{mac},{lease['ip']},{lease['hostname']}"
    if static_leases:
        static_leases += f";{new_entry}"
    else:
        static_leases = new_entry

    # 更新配置并重新生成
    config["static_leases"] = static_leases
    save_config("network.d.dhcp", config)
    subprocess.run(["rnas-config", "generate", "dnsmasq",
                    "-o", "/var/run/rnas/dnsmasq.conf"])
    subprocess.run(["systemctl", "restart", "rnas-dnsmasq"])

    return {"status": "created", "mac": mac, "ip": lease["ip"],
            "hostname": lease["hostname"]}
```

**参考:** RouterOS IP → DHCP Server → Leases → Make Static
**预估:** 0.5 人天 | **组件:** `IPManager.vue` (DHCP tab)

---

#### A4: 系统日志可视化

**现状:** SystemLog 组件原始显示 journalctl 输出，无按级别颜色高亮。

**方案:**
- 前端: 日志行按 ERROR(红) / WARN(黄) / INFO(白) / DEBUG(灰) 着色
- 后端: 已支持 `unit=` 和 `level=` 过滤参数，前端加多选 filter chips
- 加日志统计: 过去 24h 各级别日志数量迷你图（sparkline）
- 参考 RouterOS 的 Log 按 Topic 筛选功能

**前端实现示例:**
```vue
<!-- web/frontend/src/components/SystemLog.vue -->
<template>
  <div class="system-log">
    <!-- 级别统计 sparkline -->
    <div class="log-stats">
      <div v-for="level in levels" :key="level.name" class="stat-chip"
           :class="level.class">
        <span class="count">{{ level.count }}</span>
        <span class="label">{{ level.name }}</span>
      </div>
    </div>

    <!-- 过滤器 -->
    <div class="filters">
      <el-select v-model="filterUnit" placeholder="服务单元" multiple filterable>
        <el-option v-for="u in units" :key="u" :label="u" :value="u" />
      </el-select>
      <el-checkbox-group v-model="filterLevels">
        <el-checkbox label="err">ERROR</el-checkbox>
        <el-checkbox label="warning">WARN</el-checkbox>
        <el-checkbox label="info">INFO</el-checkbox>
        <el-checkbox label="debug">DEBUG</el-checkbox>
      </el-checkbox-group>
    </div>

    <!-- 日志列表 -->
    <div class="log-list">
      <div v-for="line in logLines" :key="line.id"
           class="log-line" :class="levelClass(line.level)">
        <span class="timestamp">{{ line.timestamp }}</span>
        <span class="unit">{{ line.unit }}</span>
        <span class="message">{{ line.message }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
const levelClass = (level) => ({
  'err': 'level-error',
  'warning': 'level-warn',
  'info': 'level-info',
  'debug': 'level-debug'
}[level] || 'level-info')
</script>

<style scoped>
.log-line.level-error { color: #f85149; }
.log-line.level-warn { color: #d29922; }
.log-line.level-info { color: #e6edf3; }
.log-line.level-debug { color: #7d8590; }
</style>
```

**预估:** 0.5 人天 | **组件:** `SystemLog.vue`

---

### B-Tier（中优先级 — 完善运维体验）

#### B1: 诊断工具一站式页面

**现状:** Ping、Traceroute、Bandwidth Test、Packet Sniffer、CoA Test 分散在 Tools 和 RADIUS Tools 等多个页面。

**方案:** 合并为单一 Diagnostics 页面，左侧 tab 切换：Ping / Traceroute / DNS Lookup / Packet Capture / Bandwidth Test / CoA Test。

**参考:** pfSense Diagnostics 菜单
**预估:** 2 人天 | **组件:** `ToolsPage.vue` + `routes/tools.py`

---

#### B2: 接口 Drill-Down 详情页

**现状:** 点击接口无反应，只能在外层表格查看。

**方案:** 点击接口名 → 进入接口详情页，显示：
- 基本信息 (MAC/MTU/状态/IP)
- 实时速率 Chart.js 图（最后 5 分钟）
- 报文分布饼图（TCP/UDP/ICMP/Other）
- 错误计数器折线图
- 关联的活跃 Session 列表

**参考:** RouterOS Interface → detail
**预估:** 3 人天 | **组件:** `InterfaceDetail.vue` (new) + `routes/extra.py`

---

#### B3: 服务健康报警

**现状:** 无主动通知机制。

**方案:**
- 后端: `GET /api/system/health/alerts` 检查各服务状态，返回 down 的服务列表 + 持续时间
- 前端: Topbar 加告警铃铛图标，红色标记异常服务数量；点击展开详情
- 简单报警规则: 服务 down 超过 30 秒 → 状态标记为 ERR
- 可选: 集成 Monit 或自定义健康检查脚本

**后端实现示例:**
```python
# web/api/routers/system.py
import subprocess
from datetime import datetime, timedelta

SERVICES = [
    "rnas-accel-ppp", "rnas-dnsmasq", "rnas-firewall",
    "rnas-qos", "rnas-ipsec", "rnas-wireguard", "rnas-ha"
]

# 记录服务异常开始时间
service_down_since = {}

@router.get("/system/health/alerts")
async def get_health_alerts():
    """获取服务健康告警"""
    alerts = []
    now = datetime.now()

    for svc in SERVICES:
        result = subprocess.run(
            ["systemctl", "is-active", svc],
            capture_output=True, text=True
        )
        state = result.stdout.strip()

        if state != "active":
            if svc not in service_down_since:
                service_down_since[svc] = now
            duration = now - service_down_since[svc]
            if duration > timedelta(seconds=30):
                alerts.append({
                    "service": svc,
                    "state": state,
                    "down_since": service_down_since[svc].isoformat(),
                    "duration_seconds": int(duration.total_seconds()),
                    "severity": "critical" if duration > timedelta(minutes=5) else "warning"
                })
        else:
            service_down_since.pop(svc, None)

    return {
        "total_alerts": len(alerts),
        "critical": len([a for a in alerts if a["severity"] == "critical"]),
        "alerts": alerts
    }
```

**参考:** OPNsense Health / RouterOS /system watchdog
**预估:** 1.5 人天 | **组件:** `App.vue` (topbar) + `routes/system.py`

---

#### B4: RADIUS 用户管理 GUI

**现状:** AAA Users API 返回空（数据在 FreeRADIUS 文件/SQL 中），前端 AAAEditor 可发 RADIUS 请求但无用户列表。

**方案:**
- 后端: `GET /api/aaa/users` 从 FreeRADIUS PostgreSQL 数据库读取 radcheck/radreply 表，显示用户+属性列表
- 前端: 用户列表 → 添加/编辑/删除用户 → RADIUS 属性管理（支持 13 家厂商 VSA）
- 增加用户批量导入/导出（CSV）和计费记录查询

**后端实现示例:**
```python
# web/api/routers/aaa.py
import asyncpg

async def get_db_connection():
    """获取 PostgreSQL 连接"""
    return await asyncpg.connect(
        host="127.0.0.1", port=5432,
        database="radius", user="radius", password="radius"
    )

@router.get("/aaa/users")
async def list_users():
    """查询 FreeRADIUS 用户列表"""
    conn = await get_db_connection()
    try:
        # 查询 radcheck 表获取用户及其认证属性
        rows = await conn.fetch("""
            SELECT username, attribute, op, value
            FROM radcheck
            ORDER BY username
        """)
        users = {}
        for row in rows:
            uname = row['username']
            if uname not in users:
                users[uname] = {"username": uname, "check_attrs": [], "reply_attrs": []}
            users[uname]["check_attrs"].append({
                "attribute": row['attribute'],
                "op": row['op'],
                "value": row['value']
            })

        # 查询 radreply 表获取回复属性
        reply_rows = await conn.fetch("""
            SELECT username, attribute, op, value
            FROM radreply
            ORDER BY username
        """)
        for row in reply_rows:
            uname = row['username']
            if uname in users:
                users[uname]["reply_attrs"].append({
                    "attribute": row['attribute'],
                    "op": row['op'],
                    "value": row['value']
                })

        return {"users": list(users.values()), "total": len(users)}
    finally:
        await conn.close()

@router.post("/aaa/users")
async def create_user(user: UserCreate):
    """创建 RADIUS 用户"""
    conn = await get_db_connection()
    try:
        await conn.execute(
            "INSERT INTO radcheck (username, attribute, op, value) VALUES ($1, $2, $3, $4)",
            user.username, "Cleartext-Password", ":=", user.password
        )
        # 添加回复属性
        for attr in user.reply_attrs:
            await conn.execute(
                "INSERT INTO radreply (username, attribute, op, value) VALUES ($1, $2, $3, $4)",
                user.username, attr.attribute, attr.op, attr.value
            )
        return {"status": "created", "username": user.username}
    finally:
        await conn.close()

@router.delete("/aaa/users/{username}")
async def delete_user(username: str):
    """删除 RADIUS 用户"""
    conn = await get_db_connection()
    try:
        await conn.execute("DELETE FROM radcheck WHERE username = $1", username)
        await conn.execute("DELETE FROM radreply WHERE username = $1", username)
        return {"status": "deleted", "username": username}
    finally:
        await conn.close()
```

**参考:** pfSense FreeRADIUS package / OPNsense FreeRADIUS plugin
**预估:** 2.5 人天 | **组件:** `AAAUsers.vue` + `routes/aaa.py`

---

### C-Tier（未来方向 — 长期演进）

#### C1: 配置向导（QuickSet）

首次启动引导配置: WAN IP / LAN 网段 / RADIUS 服务器 / PPPoE 参数 / 管理员密码。3 步完成基本配置。

**参考:** RouterOS QuickSet
**预估:** 2 人天

---

#### C2: Web 终端

在浏览器内提供 shell 访问，基于 xterm.js + WebSocket。可用于运维调试。

**实现示例:**
```python
# web/api/routers/terminal.py
from fastapi import WebSocket
import pty
import os

@router.websocket("/ws/terminal")
async def terminal_websocket(websocket: WebSocket):
    """Web 终端 WebSocket 端点"""
    await websocket.accept()

    # 创建伪终端
    master, slave = pty.openpty()

    pid = os.fork()
    if pid == 0:
        # 子进程: 启动 shell
        os.setsid()
        os.dup2(slave, 0)
        os.dup2(slave, 1)
        os.dup2(slave, 2)
        os.execvp("/bin/bash", ["/bin/bash"])
    else:
        # 父进程: 转发数据
        import select
        while True:
            r, _, _ = select.select([master, websocket], [], [])
            if master in r:
                data = os.read(master, 1024)
                await websocket.send_text(data.decode())
            if websocket in r:
                data = await websocket.receive_text()
                os.write(master, data.encode())
```

**参考:** pfSense Diagnostics → Command Prompt / OpenWrt ttyd
**预估:** 1.5 人天

---

#### C3: 证书管理

SSL/TLS 证书的生成/导入/管理界面，用于 SSTP/OpenVPN/HTTPS。支持 CA 管理、证书签名请求(CSR)、证书吊销列表(CRL)。

**参考:** pfSense System → Certificates
**预估:** 2 人天

---

#### C4: 流量历史 RRD 数据持久化

超过实时窗口的历史流量数据持久化到磁盘（SQLite 或 RRDtool），支持按天/周/月/年查看趋势。可选集成 Prometheus + Grafana 做专业级监控。

**预估:** 2.5 人天

---

#### C5: 报警通知渠道

邮件 / Webhook / Telegram Bot 通知。服务异常、会话超限、认证失败率异常时自动推送告警。

**预估:** 2 人天

---

#### C6: 插件/包系统

借鉴 OpenWrt 的 opkg + luci-app-* 模式和 OPNsense 的插件系统，实现模块化功能扩展。允许第三方开发插件包，按需安装。

**预估:** 3 人天

---

#### C7: IDS/IPS 集成

集成 Suricata 或 Zeek 实现入侵检测/预防，参考 OPNsense 的内置 IDS/IPS 功能。提供规则管理、告警查看、流量分析。

**预估:** 3 人天

---

## 6. 架构优化措施

除功能补齐外，RNAS 在架构层面也有以下优化空间，可提升系统性能、安全性和可维护性。

### 6.1 WebSocket 帧大小限制修复（紧急）

**问题:** 当前标准库 HTTP 服务器的 `send_websocket_frame` 方法将消息截断为最大 125 字节，这远不足以传输完整的会话列表 JSON。

**优化:** 实现 RFC 6455 的扩展帧长度支持。

```python
# 当前实现（有 bug）
def send_websocket_frame(self, message):
    msg_bytes = message.encode()
    length = min(len(msg_bytes), 125)  # 截断！数据丢失
    frame = b'\x81' + bytes([length]) + msg_bytes[:length]

# 修复后（支持完整 RFC 6455）
def send_websocket_frame(self, message):
    msg_bytes = message.encode()
    length = len(msg_bytes)
    if length < 126:
        frame = b'\x81' + bytes([length]) + msg_bytes
    elif length < 65536:
        frame = b'\x81' + bytes([126]) + length.to_bytes(2, 'big') + msg_bytes
    else:
        frame = b'\x81' + bytes([127]) + length.to_bytes(8, 'big') + msg_bytes
    self.wfile.write(frame)
    self.wfile.flush()
```

**优先级:** 紧急 | **预估:** 0.5 人天

---

### 6.2 CORS 安全策略收紧

**问题:** 当前 CORS 配置使用 `allow_origins=["*"]`，生产环境存在安全风险。

**优化:** 限制为特定域名，或通过配置文件动态管理允许的源。

```python
# web/api/main.py
# 当前（不安全）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 优化后
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.get("web", "allowed_origins",
                             "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

**优先级:** 高 | **预估:** 0.5 人天

---

### 6.3 accel-cmd 子进程调用优化

**问题:** 当前通过 `subprocess.run` 调用 `accel-cmd`，每次调用都有进程创建开销，高频查询时性能瓶颈明显。

**优化:**
- 使用 accel-ppp 的 TCP 管理接口（默认端口 2000）建立持久连接，通过 socket 直接发送命令
- 实现连接池和命令队列，减少进程创建开销
- 对 `show sessions` 等高频查询实现增量更新（只返回变化的会话）

```python
# web/api/accel_cmd.py
import socket
import threading

class AccelCmdClient:
    """accel-ppp TCP 管理接口持久连接客户端"""

    def __init__(self, host="127.0.0.1", port=2000):
        self.host = host
        self.port = port
        self._sock = None
        self._lock = threading.Lock()

    def connect(self):
        """建立持久连接"""
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect((self.host, self.port))
        # 读取欢迎信息
        self._sock.recv(4096)

    def execute(self, command):
        """执行命令并返回结果"""
        with self._lock:
            if not self._sock:
                self.connect()
            try:
                self._sock.sendall((command + "\n").encode())
                # 读取直到收到结束标记
                result = b""
                while True:
                    chunk = self._sock.recv(4096)
                    result += chunk
                    if b"\n" in chunk and not chunk.strip().endswith(b"#"):
                        break
                return result.decode()
            except (ConnectionError, BrokenPipeError):
                self._sock = None
                self.connect()
                return self.execute(command)

# 全局单例
accel_client = AccelCmdClient()

def run_accel_cmd(args):
    """替代原 subprocess.run 的持久连接版本"""
    command = " ".join(args)
    return accel_client.execute(command)
```

**优先级:** 中 | **预估:** 1.5 人天

---

### 6.4 配置验证增强

**问题:** 当前配置验证规则较为基础，缺少语义级校验。

**优化:**
- 增加 IP 地址段冲突检测（PPP 池与静态分配地址段重叠）
- RADIUS 服务器连通性预检（配置应用前自动测试 1812 端口可达性）
- 防火墙规则冲突检测（重复规则、矛盾规则）
- VPN 证书有效性检查（过期预警、私钥匹配验证）
- 借鉴 VyOS 的 `commit` 语义: 验证通过后才应用，失败自动回滚

```python
# cmd/rnas_config.py
class ConfigValidator:
    """增强的配置验证器"""

    def validate_all(self, config):
        """执行所有验证规则"""
        errors = []
        warnings = []

        errors.extend(self._check_ip_pool_conflicts(config))
        errors.extend(self._check_firewall_conflicts(config))
        warnings.extend(self._check_radius_connectivity(config))
        warnings.extend(self._check_cert_validity(config))

        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    def _check_ip_pool_conflicts(self, config):
        """检测 IP 地址池冲突"""
        errors = []
        ppp_pool = config.get("access.d.core", "ip_pool", "")
        static_leases = config.get("network.d.dhcp", "static_leases", "")

        # 解析并检测重叠
        ppp_ranges = self._parse_ip_range(ppp_pool)
        for lease in static_leases.split(";"):
            if lease.strip():
                parts = lease.strip().split(",")
                if len(parts) >= 2:
                    ip = parts[1]
                    if self._ip_in_ranges(ip, ppp_ranges):
                        errors.append(
                            f"静态绑定 IP {ip} 与 PPP 地址池重叠"
                        )
        return errors

    def _check_radius_connectivity(self, config):
        """检测 RADIUS 服务器连通性"""
        warnings = []
        server = config.get("access.d.radius", "auth_server", "127.0.0.1")
        port = int(config.get("access.d.radius", "auth_port", "1812"))

        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2)
        try:
            sock.connect((server, port))
        except socket.timeout:
            warnings.append(f"RADIUS 服务器 {server}:{port} 不可达")
        finally:
            sock.close()
        return warnings
```

**优先级:** 中 | **预估:** 1.5 人天

---

### 6.5 时序数据存储层

**问题:** 当前无持久化的时序数据存储，流量历史、会话统计等数据重启后丢失。

**优化方案:**

| 方案 | 适用场景 | 优点 | 缺点 |
|------|----------|------|------|
| RRDtool | 接口流量历史 | 固定大小，低资源 | 仅适合数值时序 |
| SQLite | 会话记录、认证日志 | 零配置嵌入式 | 并发写入受限 |
| Prometheus+Grafana | 大规模专业监控 | 功能强大 | 资源消耗较高 |

**推荐:** 短期使用 RRDtool + SQLite 组合（低资源、快速实现），长期可选 Prometheus + Grafana。

**优先级:** 中 | **预估:** 2 人天

---

### 6.6 API 认证与权限控制

**问题:** 当前 API 无认证机制，任何能访问 8099 端口的请求都可以操作。

**优化:**
- 实现 JWT 或 API Key 认证，参考 OPNsense 的 API Key/Secret 机制
- 基于角色的访问控制（RBAC）: 管理员/操作员/只读用户
- 操作模式/配置模式分离（参考 VyOS）: 只读模式无法修改配置
- API 请求审计日志，记录所有修改操作

```python
# web/api/auth.py
from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
import jwt
from datetime import datetime, timedelta

API_KEY_HEADER = APIKeyHeader(name="X-API-Key")
SECRET_KEY = "your-secret-key"  # 应从配置读取

# 角色权限映射
ROLE_PERMISSIONS = {
    "admin": ["read", "write", "execute", "admin"],
    "operator": ["read", "write", "execute"],
    "readonly": ["read"]
}

async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    """验证 API Key 并返回用户信息"""
    user = validate_api_key(api_key)
    if not user:
        raise HTTPException(401, "Invalid API Key")
    return user

def require_permission(permission: str):
    """权限检查依赖"""
    async def check_permission(user = Depends(verify_api_key)):
        if permission not in ROLE_PERMISSIONS.get(user["role"], []):
            raise HTTPException(403, f"Permission '{permission}' denied")
        return user
    return check_permission

# 使用示例
@router.get("/config/{module}", dependencies=[Depends(require_permission("read"))])
async def get_config(module: str):
    ...

@router.put("/config/{module}", dependencies=[Depends(require_permission("write"))])
async def update_config(module: str, config: dict):
    ...
```

**优先级:** 高 | **预估:** 2 人天

---

### 6.7 前端性能优化

**问题:** Vue.js 前端在会话数量大时可能出现渲染卡顿。

**优化:**
- 会话列表使用虚拟滚动（vue-virtual-scroller），支持万级会话流畅渲染
- WebSocket 数据推送使用增量更新（diff patch），减少前端重渲染
- Chart.js 图表使用 `animation: false` 和 `decimation` 插件优化大数据集渲染
- 前端路由懒加载，减少首屏加载时间

**优先级:** 低 | **预估:** 1 人天

---

## 7. 实施路线图

### 7.1 三阶段实施计划

改进建议按三个阶段实施，每个阶段聚焦不同优先级的目标：

```
Phase A (1-2 周) — 接近 pfSense 可用性
├── S1 防火墙规则拖拽排序        (2d)
├── S2 配置快照 Web UI          (1.5d)
├── A1 接口流量图(RRD风格)       (3d)
├── A2 端口转发向导             (1d)
├── A3 DHCP 一键静态绑定        (0.5d)
└── A4 日志可视化               (0.5d)
                                 小计: 8.5 天

Phase B (2-4 周) — 运维体验完善
├── B1 诊断工具一站式           (2d)
├── B2 接口 Drill-Down 详情页   (3d)
├── B3 健康报警                 (1.5d)
└── B4 RADIUS 用户管理 GUI      (2.5d)
                                 小计: 9 天

Phase C (长期) — 长期竞争力
├── C1 配置向导 QuickSet        (2d)
├── C2 Web 终端                (1.5d)
├── C3 证书管理                 (2d)
├── C4 流量历史持久化           (2.5d)
├── C5 报警通知                 (2d)
├── C6 插件系统                 (3d)
└── C7 IDS/IPS 集成             (3d)
                                 小计: 16 天
```

### 7.2 投入估算汇总

| 阶段 | 功能数 | 后端改动 | 前端改动 | 预估人天 | 目标 |
|------|--------|---------|---------|---------|------|
| Phase A (S+A) | 6 | 小-中 | 中 | 8-10 | 接近 pfSense 可用性 |
| Phase B (B) | 4 | 中 | 中-大 | 9-10 | 运维体验完善 |
| Phase C (C) | 7 | 大 | 大 | 15-17 | 长期竞争力 |
| **合计** | **17** | - | - | **32-37** | - |

### 7.3 架构优化并行实施

以下架构优化措施可与功能改进并行推进，不阻塞主线路线图：

| 优化项 | 优先级 | 预估 | 建议时机 |
|--------|--------|------|----------|
| WebSocket 帧大小修复 | 紧急 | 0.5d | 立即（bug 修复） |
| CORS 安全策略收紧 | 高 | 0.5d | Phase A 前 |
| API 认证与权限控制 | 高 | 2d | Phase A 并行 |
| accel-cmd 持久连接 | 中 | 1.5d | Phase B 并行 |
| 配置验证增强 | 中 | 1.5d | Phase B 并行 |
| 时序数据存储层 | 中 | 2d | Phase C 并行 |
| 前端性能优化 | 低 | 1d | Phase C 并行 |

---

## 8. 总结

RNAS 当前处于**工具能用**的阶段，其技术底座选型（accel-ppp + nftables + FastAPI + INI 配置引擎）合理且架构清晰，在 ISP/运营商级多协议接入、13 家厂商 VSA 支持、完整测试金字塔等方面具有独特优势。

对标 pfSense、OPNsense、RouterOS v7、OpenWrt 24.10 和 VyOS 等成熟项目，差距主要集中在三个方面：

1. **数据可视化** — 没有流量历史图、没有防火墙命中计数可视化、没有日志级别高亮
2. **交互效率** — 没有拖拽排序、没有一键绑定、没有端口转发向导、没有 drill-down
3. **系统管理** — 没有配置 Web UI、没有健康报警、没有证书管理、没有 API 认证

**行动建议:** 优先完成 Phase A 的 6 项 S/A 级改进（预估 8-10 天），同时紧急修复 WebSocket 帧大小 bug 和 CORS 安全策略。Phase A 完成后，RNAS 的可用性和专业感将提升一个档次，接近 pfSense 的体验水平。Phase B 和 Phase C 可根据资源和需求逐步推进。

此外，OpenWrt 24.10 带来的 Wi-Fi 7 初步支持、MPTCP 和内核 6.6 升级，以及 RouterOS v7.18 的容器支持，代表了软路由生态的最新趋势。RNAS 可在中长期规划中考虑 Wi-Fi 7 适配、MPTCP 支持和容器化部署能力，保持技术前瞻性。

---

## 附录: 改进项快速索引（供 opencode 参考）

| ID | 标题 | 优先级 | 组件 | 预估 |
|----|------|--------|------|------|
| S1 | 防火墙规则可视化排序管理 | S | `IPManager.vue` + `routes/extra.py` | 2d |
| S2 | 配置备份/快照/回滚 Web UI | S | `SystemPage.vue` + `routes/config.py` | 1.5d |
| A1 | 接口实时流量图（RRD 风格） | A | `TrafficMonitor.vue` + `routes/extra.py` | 3d |
| A2 | 端口转发向导 | A | `IPManager.vue` (NAT tab) | 1d |
| A3 | DHCP 一键静态绑定 | A | `IPManager.vue` (DHCP tab) | 0.5d |
| A4 | 系统日志可视化 | A | `SystemLog.vue` | 0.5d |
| B1 | 诊断工具一站式页面 | B | `ToolsPage.vue` + `routes/tools.py` | 2d |
| B2 | 接口 Drill-Down 详情页 | B | `InterfaceDetail.vue` (new) + `routes/extra.py` | 3d |
| B3 | 服务健康报警 | B | `App.vue` (topbar) + `routes/system.py` | 1.5d |
| B4 | RADIUS 用户管理 GUI | B | `AAAUsers.vue` + `routes/aaa.py` | 2.5d |
| C1 | 配置向导（QuickSet） | C | `SetupWizard.vue` (new) | 2d |
| C2 | Web 终端 | C | `WebTerminal.vue` (new) + `routes/terminal.py` | 1.5d |
| C3 | 证书管理 | C | `Certificates.vue` (new) + `routes/certs.py` | 2d |
| C4 | 流量历史 RRD 数据持久化 | C | `routes/extra.py` + 存储层 | 2.5d |
| C5 | 报警通知渠道 | C | `routes/notifications.py` | 2d |
| C6 | 插件/包系统 | C | `PluginManager.vue` + `routes/plugins.py` | 3d |
| C7 | IDS/IPS 集成 | C | `IDSPage.vue` (new) + `routes/ids.py` | 3d |
| O1 | WebSocket 帧大小修复 | 紧急 | `web/server.py` | 0.5d |
| O2 | CORS 安全策略收紧 | 高 | `web/api/main.py` | 0.5d |
| O3 | API 认证与权限控制 | 高 | `web/api/auth.py` (new) | 2d |
| O4 | accel-cmd 持久连接 | 中 | `web/api/accel_cmd.py` | 1.5d |
| O5 | 配置验证增强 | 中 | `cmd/rnas_config.py` | 1.5d |
| O6 | 时序数据存储层 | 中 | 新增存储模块 | 2d |
| O7 | 前端性能优化 | 低 | 前端全局 | 1d |
