# RNAS 功能完善规划 (详细版)

**版本**: 1.3  
**日期**: 2026-04-21 (更新)  
**状态**: 规划中  
**定位**: 网络协议仿真与组件集成测试平台 (集成WiFi AC仿真)  
**参考**: H3C vBRAS, 赛特斯FlexBNG, 华为/天翼家庭网关

---

## ⚠️ 项目定位 (重要)

RNAS **不是**要做一个真正的商业NAS设备，而是：

| 对比项 | 商业NAS | RNAS |
|--------|---------|--------------|
| **核心目标** | 流量转发与用户管理 | **协议仿真与组件集成测试** |
| **用户群体** | 终端用户 | 测试/开发/运维人员 |
| **功能重点** | 带宽管理/QoS/限速 | **产生真实协议报文** |
| **价值体现** | 网络接入服务 | **协议测试/验证/调试** |

**RNAS的核心价值：**
- 模拟NAS产生**真实的**协议报文（PPPoE/L2TP/DHCP/RADIUS）
- 与各种网络组件**联动测试**（FreeRADIUS/LDAP/AD）
- 验证NAS设备和RADIUS服务器的**协议正确性**
- 支持**压力测试**和**自动化测试**

---

## 2. 功能模块详细规划

### 2.1 协议接入层 (Access Protocol)

#### 2.1.1 PPPoE 服务器 (P0 - 核心)

| 功能项 | 说明 | 参考厂商 | 优先级 |
|--------|------|----------|--------|
| PPPoE服务器基础 | 终结PPPoE会话，分配IP地址 | 华为/华三/赛特斯 | ✅ 已实现 |
| 多实例支持 | 支持多个PPPoE实例/VLAN隔离 | H3C vBRAS | P1 |
| PPPoE代拨 | PPPoE透传，代为拨号 | 华为MA5600 | P2 |
| PPPoEoVLAN | QinQ嵌套VLAN接入 | H3C | P2 |
| PPPoE双栈 | IPv4/IPv6同时拨号 | 华为/华三 | P1 |
| PPPoE + NAT | 配合CGNAT实现地址转换 | 赛特斯 | P2 |
| PPPoE会话限速 | 基于会话的上下行限速 | 所有厂商 | P0 |
| PPPoE业务策略 | CAR/GTS/LR流量控制 | H3C | P1 |

#### 2.1.2 IPoE 服务器 (P0 - 重点)

| 功能项 | 说明 | 参考厂商 | 优先级 |
|--------|------|----------|--------|
| IPoE基础 | DHCP+认证，零配置接入 | 华为/华三 | P0 |
| DHCP选项识别 | Option60/82用户识别 | 华为/华三 | P0 |
| IPoE Web认证 | DHCP+Web Portal | H3C vBRAS | P1 |
| Session级IPoE | 每次DHCP会话独立认证 | H3C | P1 |
| IPoE双栈 | IPv6 PD + IPv4 | 华为/华三 | P1 |
| IPoE组播 | IGMP Proxy/Snooping | 华为/华三 | P2 |
| IPoE限速 | 基于会话的带宽控制 | 所有厂商 | P0 |

#### 2.1.3 L2TP 服务器 (P1)

| 功能项 | 说明 | 参考厂商 | 优先级 |
|--------|------|----------|--------|
| L2TP基础 | L2TP隧道建立 | 华为/华三 | ✅ 配置存在 |
| L2TP + IPSec | L2TP over IPSec | 华为 | P2 |
| L2TP LAC | L2TP访问集中器 | H3C vBRAS | P1 |
| L2TP LNS | L2TP网络服务器 | 华为/华三 | P1 |
| L2TP转控分离 | CP/DP分离架构 | H3C vBRAS | P2 |

#### 2.1.4 PPTP 服务器 (P1)

| 功能项 | 说明 | 参考厂商 | 优先级 |
|--------|------|----------|--------|
| PPTP基础 | PPTP隧道 | 华为/华三 | ✅ 已实现 |
| MPPE加密 | 128-bit加密 | 华为/华三 | P1 |

#### 2.1.5 其他协议 (P2)

| 功能项 | 说明 | 优先级 |
|--------|------|--------|
| SSTP | HTTPS隧道VPN | P2 |
| OpenVPN | OpenVPN兼容 | P2 |
| WireGuard | 现代VPN协议 | P2 |

---

### 2.2 RADIUS 协议层 (P0 - 核心)

#### 2.2.1 认证 (Authentication)

| 功能项 | 说明 | 参考厂商 | 优先级 |
|--------|------|----------|--------|
| PAP认证 | 明文密码认证 | 所有 | ✅ 已实现 |
| CHAP认证 | 质询握手认证 | 所有 | ✅ 已实现 |
| MS-CHAPv2 | Microsoft CHAP | 华为/华三 | P0 |
| EAP-MD5 | EAP封装 | 华为/华三 | P1 |
| EAP-TLS | 证书认证 | 华为/华三 | P2 |
| 代理认证 | RADIUS Proxy | 赛特斯 | P2 |

#### 2.2.2 计费 (Accounting) - P0重点

| 功能项 | 说明 | 参考厂商 | 优先级 |
|--------|------|----------|--------|
| Accounting-Start | 会话开始 | 所有 | P0 |
| Accounting-Stop | 会话结束 | 所有 | P0 |
| Interim-Update | 周期更新(300s) | 华为/华三/赛特斯 | P0 |
| Acct-Input-Octets | 上行流量 | 所有 | P0 |
| Acct-Output-Octets | 下行流量 | 所有 | P0 |
| Acct-Input-Packets | 上行报文数 | 所有 | P0 |
| Acct-Output-Packets | 下行报文数 | 所有 | P0 |
| Acct-Session-Time | 会话时长 | 所有 | P0 |
| Acct-Terminate-Cause | 终止原因码 | 华为/华三 | P0 |
| Acct-Session-Id | 会话ID | 所有 | P0 |
| NAS-Port-Type | 接入类型(PPPoE/IPoE) | 华为/华三 | P0 |
| NAS-Identifier | 设备标识 | 华为/华三 | P0 |
| NAS-IP-Address | NAS IP地址 | 所有 | P0 |
| Calling-Station-Id | 用户MAC | 华为/华三 | P1 |
| Called-Station-Id | NAS端口标识 | 华为/华三 | P1 |

#### 2.2.3 动态授权 (CoA) - P0重点

| 功能项 | 说明 | 参考厂商 | 优先级 |
|--------|------|----------|--------|
| CoA-Request | 动态授权请求 | 华为/华三/赛特斯 | P0 |
| Disconnect-Request | 强制下线 | 华为/华三/赛特斯 | P0 |
| Session-Timeout | 会话超时(属性25) | 华为/华三 | P0 |
| Framed-Pool | IP地址池(属性26) | 华为/华三 | P0 |
| Framed-IP-Address | 静态IP(属性27) | 华为/华三 | P0 |
| Framed-Route | 下发路由(属性28) | 华为/华三 | P1 |
| Bandwidth-Quota | 流量配额 | 赛特斯 | P1 |
| QoS-Profile | QoS策略下发 | 赛特斯 | P1 |
| Re-authenticate | 重新认证 | 华为/华三 | P1 |

#### 2.2.4 RADIUS属性扩展

| 功能项 | 说明 | 优先级 |
|--------|------|--------|
| H3C私有属性(25506) | H3C AV-Pair | P1 |
| 华为私有属性(2011) | 华为CAR/QoS | P1 |
| 微软私有属性(311) | MS-CHAP属性 | P2 |

---

### 2.3 认证集成 (Authentication Backend)

| 功能项 | 说明 | 参考厂商 | 优先级 |
|--------|------|----------|--------|
| 本地用户文件 | /etc/accel-ppp.conf | - | P0 |
| SQLite本地库 | 本地SQLite认证 | 华为 | P0 |
| FreeRADIUS转发 | 转发到外部RADIUS | 赛特斯 | P0 |
| LDAP集成 | OpenLDAP认证 | 华为/华三 | P1 |
| Windows AD | Active Directory | 华为/华三 | P1 |
| RADIUS代理 | 上游RADIUS中继 | 赛特斯 | P2 |
| TACACS+ | 企业级认证 | 华三 | P2 |

---

### 2.4 会话管理 (Session Management) - P0核心

#### 2.4.1 会话控制

| 功能项 | 说明 | 参考厂商 | 优先级 |
|--------|------|----------|--------|
| 会话列表 | 实时在线用户 | 华为/华三 | P0 |
| 会话详情 | 连接时长/流量/IP | 华为/华三 | P0 |
| 强制下线 | 手动断开 | 华为/华三/赛特斯 | P0 |
| 会话限速 | 上行/下行带宽 | 华为/华三/赛特斯 | P0 |
| 会话超时 | 基于RADIUS属性 | 华为/华三 | P0 |
| 并发限制 | 同账号多设备 | 华为/华三 | P1 |
| 流量配额 | 流量到限断连 | 赛特斯 | P1 |
| 时长配额 | 时长到限断连 | 赛特斯 | P1 |
| Idle-Timeout | 空闲超时 | 华为/华三 | P1 |

#### 2.4.2 用户隔离与管理

| 功能项 | 说明 | 优先级 |
|--------|------|--------|
| VLAN隔离 | 802.1Q VLAN | P1 |
| 端口隔离 | 用户间隔离 | P1 |
| IP-MAC绑定 | 绑定防冒用 | P1 |
| 用户组策略 | 组级别限速 | P1 |

---

### 2.5 IP地址管理 (IP Address Management)

| 功能项 | 说明 | 参考厂商 | 优先级 |
|--------|------|----------|--------|
| 静态地址池 | 固定IP段 | 华为/华三 | P0 |
| 动态地址池 | DHCP分配 | 华为/华三 | P0 |
| 多个地址池 | 按VLAN/域选择 | 华为/华三 | P0 |
| IPv6地址池 | PD前缀池 | 华为/华三 | P1 |
| IPv4/IPv6双栈 | 同时分配 | 华为/华三 | P1 |
| 地址保留 | 静态绑定 | 华为/华三 | P1 |
| 地址冲突检测 | ARP防冒用 | 华为/华三 | P1 |

---

### 2.6 网络功能仿真 (Network Function Emulation) - P0核心

| 功能项 | 说明 | 优先级 |
|--------|------|--------|
| 真实协议报文 | 产生标准RADIUS/PPPoE/DHCP报文 | P0 |
| 协议交互日志 | 完整记录协议握手过程 | P0 |
| 多协议并发 | 同时支持PPPoE/IPoE/L2TP | P0 |
| 协议参数定制 | 可配置报文参数 | P0 |
| 协议一致性 | 符合RFC标准 | P0 |

#### 2.6.1 协议仿真精度

| 指标 | 目标 | 说明 |
|------|------|------|
| RADIUS属性 | 100%标准 | 符合RFC2865/2866 |
| PPPoE会话 | 完整协商 | Discovery/PAD/PCM |
| DHCP交互 | 四步交互 | Discover/Offer/Request/ACK |
| L2TP隧道 | 完整建立 | UDP+IPSec可选 |

#### 2.6.2 网络组件集成

| 组件 | 说明 | 优先级 |
|------|------|--------|
| FreeRADIUS | 外部RADIUS服务器 | P0 |
| OpenLDAP | LDAP目录服务认证 | P1 |
| Windows AD | Active Directory | P1 |
| RADIUS代理 | 上游RADIUS转发 | P2 |
| RADIUS_client库 | libradius封装 | P0 |

---

### 2.7 流量与QoS

| ~~功能项~~ | ~~说明~~ | ~~参考厂商~~ | ~~优先级~~ |
|-----------|----------|--------------|------------|
| ~~CAR限速~~ | ~~单用户限速~~ | ~~华为/华三~~ | ~~P0~~ |
| ~~GTS流整形~~ | ~~流量整形~~ | ~~华为/华三~~ | ~~P1~~ |
| ~~LR链路复用~~ | ~~链路复用~~ | ~~华为/华三~~ | ~~P1~~ |
| ~~FIFO队列~~ | ~~先进先出~~ | ~~华为/华三~~ | ~~P1~~ |
| ~~WFQ队列~~ | ~~加权公平队列~~ | ~~华为/华三~~ | ~~P2~~ |
| ~~CBQ队列~~ | ~~基于类队列~~ | ~~华为/华三~~ | ~~P2~~ |
| ~~WRED~~ | ~~随机早期检测~~ | ~~华为/华三~~ | ~~P2~~ |
| ~~HQoS~~ | ~~分层QoS~~ | ~~赛特斯/华三~~ | ~~P2~~ |

> ⚠️ **说明**: QoS是商业NAS的核心功能，但与RNAS的仿真测试平台定位不符，已移除。

---

### 2.7 协议监控与日志 (Protocol Monitoring & Logging)

| 功能项 | 说明 | 优先级 |
|--------|------|--------|
| 协议会话数 | 当前PPPoE/IPoE/L2TP会话 | P0 |
| 协议报文统计 | 收发报文数/错误数 | P0 |
| RADIUS日志 | Auth/Acct/CoA交互记录 | P0 |
| PPPoE日志 | Discovery/PAD/PCM握手 | P0 |
| DHCP日志 | 四步交互日志 | P0 |
| 会话详情 | 用户IP/MAC/时长/流量 | P0 |
| 协议抓包 | tcpdump/Wireshark集成 | P0 |
| 计费日志 | 流量/时长记录 | P0 |
| 系统日志 | 操作/告警 | P0 |
| 日志轮转 | 自动清理 | P1 |

---

### 2.8 管理界面 (Management)

#### 2.8.1 LuCI插件 (P0)

| 页面 | 功能 | 优先级 |
|------|------|--------|
| 仪表盘 | 系统概览/在线数/流量 | P0 |
| 会话管理 | 在线列表/强制下线 | P0 |
| 地址池管理 | IP池配置 | P0 |
| 用户管理 | 本地用户CRUD | P0 |
| RADIUS配置 | 服务器/密钥 | P0 |
| 协议配置 | PPPoE/L2TP/PPTP | P0 |
| CoA操作 | 限速/踢人 | P0 |
| 统计报表 | 流量/会话统计 | P1 |
| 系统设置 | 网络/日志/备份 | P1 |

#### 2.8.2 命令行工具

| 工具 | 功能 | 优先级 |
|------|------|--------|
| accel-cmd | 会话管理 | P0 |
| radtest | RADIUS测试 | P0 |
| coa-test | CoA测试 | P0 |
| session-monitor | 会话监控 | P0 |

#### 2.8.3 REST API

| 接口 | 功能 | 优先级 |
|------|------|--------|
| GET /sessions | 会话列表 | P1 |
| GET /sessions/:id | 会话详情 | P1 |
| POST /sessions/:id/kick | 强制下线 | P1 |
| POST /sessions/:id/limit | 限速 | P1 |
| GET /stats | 统计信息 | P1 |
| POST /users | 创建用户 | P1 |

---

### 2.9 WiFi AC仿真与无线功能 (WiFi AC Emulation & Wireless)

#### 2.9.1 OpenWrt基础无线功能 (P0 - 继承)
| 功能项 | 说明 | 优先级 |
|--------|------|--------|
| AP模式 | 作为无线接入点 | ✅ OpenWrt原生 |
| Client模式 | 作为无线客户端 | ✅ OpenWrt原生 |
| 多SSID | 多个虚拟AP | ✅ OpenWrt原生 |
| VLAN隔离 | 不同SSID对应不同VLAN | ✅ OpenWrt原生 |
| WPA2/WPA3 | 无线安全 | ✅ OpenWrt原生 |
| 802.11ac/ax | WiFi 5/6 | ✅ 硬件支持 |

#### 2.9.2 AC控制器仿真 (P0 - 核心)
| 功能项 | 说明 | 优先级 |
|--------|------|--------|
| AC仿真核心 | 仿真WiFi AC控制平面 | P0 |
| AP管理仿真 | AP发现、配置、状态监控 | P0 |
| 用户会话管理 | WiFi用户认证/计费会话 | P0 |
| RADIUS代理集成 | 处理WiFi用户RADIUS请求 | P0 |
| 简化控制协议 | 模拟CAPWAP-like控制流 | P1 |
| 802.1X/EAP支持 | 企业级WiFi认证 | P0 |
| 漫游测试支持 | 802.11r/k/v仿真 | P1 |

#### 2.9.3 WiFi协议测试能力 (P0 - 测试重点)
| 测试场景 | 说明 | 优先级 |
|----------|------|--------|
| WiFi RADIUS认证 | 802.1X/EAP认证流程 | P0 |
| WiFi计费流程 | Start/Stop/Interim Update | P0 |
| WiFi CoA测试 | 动态授权在无线场景 | P0 |
| 多SSID测试 | 不同SSID不同策略 | P1 |
| VLAN隔离测试 | 无线用户VLAN隔离 | P1 |
| 漫游切换测试 | 用户在不同AP间切换 | P1 |
| 负载均衡测试 | 多AP用户分布 | P2 |

#### 2.9.4 配置管理
| 配置项 | 说明 | 优先级 |
|--------|------|--------|
| wireless配置模板 | OpenWrt标准配置 | P0 |
| AC仿真配置 | AP管理、用户策略 | P0 |
| 测试场景配置 | WiFi测试参数 | P0 |
| RADIUS属性映射 | WiFi特有属性处理 | P0 |

---

### 2.10 测试工具 (Testing Tools)

| 工具 | 功能 | 优先级 |
|------|------|--------|
| 批量PPPoE客户端 | 100+并发 | P0 |
| radtest | RADIUS认证测试 | P0 |
| coa-test | CoA功能测试 | P0 |
| PPPoE客户端模拟 | 多种场景 | P0 |
| DHCP/IPoE客户端 | DHCP测试 | P0 |
| L2TP客户端 | L2TP测试 | P1 |
| 流量发生器 | 带宽压测 | P1 |
| 协议抓包 | tcpdump/Wireshark | P1 |
| 自动测试脚本 | 回归测试 | P1 |

---

## 3. 详细任务清单

### Phase 1: RADIUS核心功能 (第1-2周)

#### Week 1: RADIUS Accounting完善

| # | 任务 | 验收标准 | 优先级 |
|---|------|----------|--------|
| 1.1 | 完善Acct-Start报文发送 | 用户上线时发送Start | P0 |
| 1.2 | 完善Acct-Stop报文发送 | 用户下线时发送Stop | P0 |
| 1.3 | 实现Interim-Update | 300秒周期性更新 | P0 |
| 1.4 | 验证流量统计正确性 | Octets与实际一致 | P0 |
| 1.5 | 验证时长统计正确性 | Session-Time准确 | P0 |
| 1.6 | 实现Acct-Terminate-Cause | 记录终止原因 | P0 |

#### Week 2: CoA动态授权

| # | 任务 | 验收标准 | 优先级 |
|---|------|----------|--------|
| 2.1 | 实现CoA-Request监听 | 端口3799监听 | P0 |
| 2.2 | 实现Session-Timeout修改 | 属性25生效 | P0 |
| 2.3 | 实现带宽限制 | 上行/下行限速 | P0 |
| 2.4 | 实现Disconnect-Request | 强制踢人 | P0 |
| 2.5 | 实现IP地址池切换 | 属性26生效 | P0 |
| 2.6 | CoA测试工具完善 | 支持多种CoA | P0 |

### Phase 2: 会话管理 (第3周)

| # | 任务 | 验收标准 | 优先级 |
|---|------|----------|--------|
| 3.1 | 会话列表API | 实时在线用户 | P0 |
| 3.2 | 会话详情API | 流量/时长/IP | P0 |
| 3.3 | 强制下线API | accel-cmd kick | P0 |
| 3.4 | 会话限速API | 动态修改带宽 | P0 |
| 3.5 | 并发限制 | 账号多设备控制 | P1 |
| 3.6 | 会话监控脚本 | 实时监控输出 | P0 |

### Phase 3: IPoE支持 (第4周)

| # | 任务 | 验收标准 | 优先级 |
|---|------|----------|--------|
| 4.1 | IPoE服务器配置 | DHCP+认证 | P0 |
| 4.2 | Option60识别 | 识别厂商标识 | P0 |
| 4.3 | Option82插入 | 中继代理信息 | P0 |
| 4.4 | IPoE RADIUS属性 | NAS-Port-Type=IPoE | P0 |
| 4.5 | IPoE计费 | Start/Stop | P0 |
| 4.6 | DHCP客户端测试 | 模拟IPoE用户 | P0 |

### Phase 4: 协议完整测试 (第5周)

| # | 任务 | 验收标准 | 优先级 |
|---|------|----------|--------|
| 5.1 | L2TP完整测试 | LAC/LNS隧道建立 | P1 |
| 5.2 | PPTP完整测试 | MPPE加密 | P1 |
| 5.3 | PPPoE双栈 | IPv4+IPv6 | P1 |
| 5.4 | IPoE双栈 | DHCPv6+DHCPv4 | P1 |
| 5.5 | 认证协议测试 | PAP/CHAP/MS-CHAP | P0 |
| 5.6 | 协议一致性验证 | RFC2865/2866符合 | P0 |
| 5.7 | 协议报文抓包验证 | tcpdump验证报文 | P0 |

### Phase 5: WiFi AC仿真与无线功能 (第6周)

| # | 任务 | 验收标准 | 优先级 |
|---|------|----------|--------|
| 5.1 | OpenWrt无线配置模板 | 标准wireless配置 | P0 |
| 5.2 | AC仿真核心框架 | AP管理、用户会话 | P0 |
| 5.3 | WiFi RADIUS认证集成 | 802.1X/EAP支持 | P0 |
| 5.4 | WiFi计费流程实现 | Start/Stop/Interim | P0 |
| 5.5 | WiFi CoA测试支持 | 无线场景动态授权 | P0 |
| 5.6 | 多SSID/VLAN测试 | 不同SSID不同策略 | P1 |
| 5.7 | 简化控制协议仿真 | CAPWAP-like控制流 | P1 |
| 5.8 | 漫游测试场景支持 | 802.11r/k/v基础 | P1 |

### Phase 6: 网络组件集成 (第7周)

| # | 任务 | 验收标准 | 优先级 |
|---|------|----------|--------|
| 6.1 | FreeRADIUS集成 | 完整AAA流程 | P0 |
| 6.2 | OpenLDAP集成 | LDAP认证 | P1 |
| 6.3 | Windows AD集成 | AD认证 | P1 |
| 6.4 | RADIUS代理转发 | 上游转发 | P2 |
| 6.5 | 多组件联动测试 | RADIUS+LDAP | P1 |
| 6.6 | 协议报文抓包验证 | tcpdump验证 | P0 |

### Phase 7: LuCI管理界面 (第8-9周)

| # | 任务 | 验收标准 | 优先级 |
|---|------|----------|--------|
| 7.1 | 仪表盘页面 | 协议状态/组件连接 | P1 |
| 7.2 | 会话管理页面 | 协议会话列表 | P1 |
| 7.3 | RADIUS配置 | 服务器/属性配置 | P0 |
| 7.4 | 协议配置 | PPPoE/L2TP/IPoE | P0 |
| 7.5 | 用户管理 | 本地用户CRUD | P0 |
| 7.6 | 组件集成配置 | LDAP/AD连接 | P1 |
| 7.7 | 协议监控 | 报文统计/日志 | P0 |
| 7.8 | 测试工具页面 | 批量测试控制 | P0 |

### Phase 8: 测试验证 (第10周)

| # | 任务 | 验收标准 | 优先级 |
|---|------|----------|--------|
| 8.1 | 自动化测试脚本 | 回归测试 | P1 |
| 8.2 | 协议一致性测试 | RFC验证 | P0 |
| 8.3 | 组件集成测试 | FreeRADIUS/LDAP | P0 |
| 8.4 | 压力测试 | 100+并发 | P0 |
| 8.5 | 文档完善 | 用户/开发文档 | P1 |

---

## 4. 验收标准

### 4.1 功能验收

| 功能 | 验收条件 |
|------|----------|
| PPPoE认证 | 客户端成功认证并获取IP |
| IPoE认证 | DHCP+认证成功获取IP |
| RADIUS Accounting | Start/Stop/Interim正确 |
| CoA限速 | 动态修改带宽生效 |
| CoA踢人 | 强制下线生效 |
| 会话列表 | 实时显示在线用户 |
| WiFi认证 | 802.1X/EAP认证成功 |
| WiFi计费 | WiFi用户Start/Stop正确 |
| 批量测试 | 100+并发拨号成功 |

### 4.2 性能指标

| 指标 | 目标 |
|------|------|
| 并发会话 | 500+ |
| 吞吐量 | >100Mbps |
| RADIUS响应 | <100ms |
| 内存占用 | <200MB |

### 4.3 稳定性

| 指标 | 目标 |
|------|------|
| 连续运行 | 72小时无崩溃 |
| 异常恢复 | 自动恢复 |

---

## 5. 技术参考

### 5.1 厂商功能对照

| 功能 | H3C vBRAS | 赛特斯FlexBNG | 华为MA5600 | RNAS目标 |
|------|-----------|---------------|------------|----------|
| PPPoE | ✅ | ✅ | ✅ | ✅ |
| IPoE | ✅ | ✅ | ✅ | P0实现 |
| L2TP | ✅ | ✅ | ✅ | P1完善 |
| RADIUS Auth | ✅ | ✅ | ✅ | ✅ |
| RADIUS Acct | ✅ | ✅ | ✅ | P0完善 |
| CoA | ✅ | ✅ | ✅ | P0实现 |
| 会话限速 | ✅ | ✅ | ✅ | ✅ |
| QoS | ✅ | ✅ | ✅ | P1 |
| LDAP | ✅ | ✅ | ✅ | P1 |
| WiFi AC仿真 | ✅ (部分) | ✅ | ✅ (部分) | P0实现 |
| WiFi协议测试 | ✅ | ✅ | ✅ | P0实现 |
| LuCI | 自研 | 自研 | TR069(不实现) | 自研(LuCI) |

### 5.2 RADIUS属性参考

| 属性号 | 名称 | 用途 |
|--------|------|------|
| 1 | User-Name | 用户名 |
| 2 | User-Password | 密码(PAP) |
| 3 | CHAP-Password | CHAP密码 |
| 4 | NAS-IP-Address | NAS IP |
| 5 | NAS-Port | NAS端口 |
| 6 | Service-Type | 服务类型 |
| 7 | Framed-Protocol | 帧协议 |
| 8 | Framed-IP-Address | 用户IP |
| 9 | Framed-Netmask | 用户掩码 |
| 10 | Framed-Route | 用户路由 |
| 11 | Framed-Pool | 地址池 |
| 25 | Session-Timeout | 会话超时 |
| 26 | Framed-Compression | 压缩 |
| 27 | Framed-MTU | MTU |
| 28 | Framed-Route | 路由 |
| 31 | Calling-Station-Id | MAC |
| 32 | Called-Station-Id | 端口 |
| 40 | Acct-Status-Type | 计费类型 |
| 41 | Acct-Delay-Time | 延迟 |
| 42 | Acct-Input-Octets | 输入字节 |
| 43 | Acct-Output-Octets | 输出字节 |
| 44 | Acct-Session-Id | 会话ID |
| 45 | Acct-Authentic | 认证方式 |
| 46 | Acct-Session-Time | 会话时间 |
| 47 | Acct-Input-Packets | 输入报文 |
| 48 | Acct-Output-Packets | 输出报文 |
| 49 | Acct-Terminate-Cause | 终止原因 |
| 60 | Acct-Input-Gigawords | 输入GB |
| 61 | Acct-Output-Gigawords | 输出GB |

---

*文档版本: 1.3*  
*创建日期: 2026-04-21 (更新)*  
*参考资料: H3C vBRAS配置手册, 赛特斯FlexBNG白皮书, 华为MA5600技术文档*