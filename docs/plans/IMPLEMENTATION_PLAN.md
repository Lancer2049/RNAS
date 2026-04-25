# RNAS-OpenWrt 详细开发实施计划

**版本**: 1.1  
**日期**: 2026-04-21 (更新)  
**状态**: 待审核  
**前提**: 规划文档已确认 (2026-04-21-rnas-functionality-plan.md v1.3)

---

## ⚠️ 架构整合说明 (重要)

### 代码底层融合原则

RNAS-OpenWrt涉及**两个独立开源项目的深度整合**：

| 项目 | 作者/来源 | 主要功能 | 整合方式 |
|------|----------|----------|----------|
| **OpenWrt** | OpenWrt社区 | 路由器固件、网络栈、LuCI | 基础平台 |
| **accel-ppp** | accel-ppp项目 | PPPoE/L2TP/IPoE服务端、RADIUS客户端 | 核心功能 |

**整合策略**：
1. **代码层面**：将accel-ppp作为OpenWrt的package进行编译和集成
2. **配置层面**：使用OpenWrt的UCI系统统一管理accel-ppp配置
3. **接口层面**：通过OpenWrt的init脚本和LuCI界面封装accel-ppp功能
4. **数据层面**：通过Socket/UCI/API暴露accel-ppp会话信息给管理界面

### CPE客户端模拟策略

本项目作为**NAS设备**，需要完整的端到端测试环境：

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   CPE模拟器     │────►│   RNAS-OpenWrt   │────►│   FreeRADIUS   │
│   (VM3)        │     │   (NAS设备)      │     │   (RADIUS服务器) │
└─────────────────┘     └─────────────────┘     └─────────────────┘
     客户端                    NAS                    服务端
```

**CPE模拟器(VM3)职责**：
- 模拟PPPoE客户端行为
- 模拟PPTP客户端行为
- 模拟L2TP客户端行为
- 模拟IPoE/DHCP客户端行为
- 产生真实的协议报文交互
- 支持批量并发测试

**VM3技术实现**：
- 独立虚拟机或容器
- 内置PPPoE/PPTP客户端工具
- 可配置的测试场景
- 结果收集和日志记录

---

## 🏗️ Phase 0: 代码底层融合 (第1周 - 前置准备)

在开始功能开发前，必须先完成OpenWrt和accel-ppp的代码融合：

### Task 0.1: OpenWrt构建环境搭建

**技术实现**:
```bash
# 克隆OpenWrt SDK
git clone https://github.com/openwrt/openwrt.git
cd openwrt
./scripts/feeds update -a
./scripts/feeds install -a
```

**验收条件**:
- 能成功编译基础OpenWrt镜像
- 能使用make menuconfig配置

---

### Task 0.2: accel-ppp源码集成

**技术实现**:
```bash
# 将accel-ppp作为本地package
cp -r /path/to/accel-ppp /openwrt/package/accel-ppp

# 配置编译
make menuconfig
# 选择 Network -> accel-ppp
```

**accel-ppp源码结构**:
```
accel-ppp/
├── accel-pppd/           # 核心守护进程
│   ├── chap-md5.c
│   ├── chap-ms-md5.c
│   ├── pppcp.c
│   ├── radius.c           # RADIUS客户端
│   └── ...
├── accel-cmd/           # 命令行工具
├── configs/             # 配置文件
└── src/               # Makefile等
```

**验收条件**:
- accel-ppp能成功编译
- 生成的ipk包可以安装

---

### Task 0.3: UCI配置接口封装

**技术实现**:
- 使用OpenWrt的UCI系统管理accel-ppp配置
- 创建 `/etc/config/accel-ppp` UCI配置文件

**UCI配置示例**:
```bash
config accel-ppp 'global'
    option 'enable' '1'
    option 'thread_count' '4'

config accel-ppp 'pppoe'
    option 'interface' 'br-lan'
    option 'verbose' '1'

config accel-ppp 'radius'
    option 'auth_server' '192.168.1.1'
    option 'auth_secret' 'testing123'
    option 'acct_port' '1813'
```

**验收条件**:
- UCI命令能正确读取/写入accel-ppp配置
- 配置变更能重启服务生效

---

### Task 0.4: Init脚本创建

**技术实现**:
```bash
# /etc/init.d/accel-ppp
#!/bin/sh /etc/rc.common
START=90
STOP=10

start() {
    accel-pppd -c /etc/accel-ppp.conf
}

stop() {
    killall accel-pppd
}
```

**验收条件**:
- `/etc/init.d/accel-ppp enable` 能启用自启动
- 服务能正确启动/停止

---

### Task 0.5: VM3 CPE模拟器准备

**技术实现**:
- 准备独立的VM或容器作为CPE客户端
- 安装必要工具：`ppp`, `pptp`, `pppoe`, `dhcpcd`

**VM3工具清单**:
| 工具 | 用途 |
|------|------|
| pppoe-setup | PPPoE客户端配置 |
| pptp-setup | PPTP客户端配置 |
| pppd | PPP守护进程 |
| tcpdump | 协议抓包 |

**验收条件**:
- VM3能与RNAS建立PPPoE/PPTP会话
- 能发送/接收协议报文

---

## 📋 开发概览

| 阶段 | 周数 | 核心交付物 | 状态 |
|------|------|------------|------|
| Phase 1 | 第1-2周 | RADIUS Accounting + CoA | 待开发 |
| Phase 2 | 第3周 | 会话管理API | 待开发 |
| Phase 3 | 第4周 | IPoE支持 | 待开发 |
| Phase 4 | 第5周 | 协议完整测试 | 待开发 |
| Phase 5 | 第6周 | WiFi AC仿真 | 待开发 |
| Phase 6 | 第7周 | 网络组件集成 | 待开发 |
| Phase 7 | 第8-9周 | LuCI管理界面 | 待开发 |
| Phase 8 | 第10周 | 测试验证 | 待开发 |

---

## 🎯 Phase 1: RADIUS核心功能 (第1-2周)

### Week 1: RADIUS Accounting完善

#### Task 1.1: 完善Acct-Start报文发送

**技术实现**:
- 检查 `/home/lancer/projects/RNAS-OpenWrt/configs/pppoe.conf` 配置
- 确保 `[acct]` 段存在且配置正确
- 验证 `interim-interval=300` 已设置

**配置文件检查点**:
```ini
[acct]
interim-interval=300
# 确保启用计费
```

**验收条件**:
- 用户PPPoE/IPoE登录时，RADIUS服务器收到Acct-Start报文
- 报文包含必要属性: User-Name, NAS-IP-Address, Acct-Status-Type=Start, Acct-Session-Id

**测试方法**:
1. 启动测试RADIUS服务器 (例如使用 `radiusd` 或 socat模拟)
2. 使用 `tcpdump -i any port 1813` 捕获计费报文
3. 使用现有测试脚本发起PPPoE会话
4. 验证捕获到的Acct-Start报文

---

#### Task 1.2: 完善Acct-Stop报文发送

**技术实现**:
- 确保会话正常结束时发送Acct-Stop
- 确保异常断开时也能发送Acct-Stop

**验收条件**:
- 用户主动断开或被动断开时，RADIUS服务器收到Acct-Stop报文
- 报文包含: Acct-Status-Type=Stop, Acct-Terminate-Cause, 流量统计

---

#### Task 1.3: 实现Interim-Update

**技术实现**:
- 配置 `interim-interval=300` (默认300秒)
- 确保accel-ppp在会话活跃期间定期发送Accounting Interim

**验收条件**:
- 每300秒发送一次Acct-Update报文
- 报文包含实时流量统计 (Acct-Input-Octets, Acct-Output-Octets)

---

#### Task 1.4: 验证流量统计正确性

**技术实现**:
- 对比accel-ppp日志中的流量统计与实际RADIUS报文中的数值

**验收条件**:
- Acct-Stop报文中的Octets与实际会话期间流量一致

---

#### Task 1.5: 验证时长统计正确性

**验收条件**:
- Acct-Session-Time在Acct-Stop中准确反映会话时长

---

#### Task 1.6: 实现Acct-Terminate-Cause

**RADIUS Terminate-Cause值**:
| 值 | 含义 |
|----|------|
| 1 | User Request |
| 2 | Lost Carrier |
| 3 | Lost Service |
| 4 | Idle Timeout |
| 5 | Session Timeout |
| 6 | Admin Reset |
| 7 | Admin Reboot |
| 8 | Port Error |
| 9 | NAS Error |
| 10 | NAS Request |
| 11 | NAS Reboot |
| 12 | Port Unneeded |
| 13 | Port Preempted |
| 14 | Service Unavailable |
| 15 | Callback |
| 16 | User Error |
| 17 | Host Request |

**验收条件**:
- 不同断开场景发送正确的Terminate-Cause值

---

### Week 2: CoA动态授权

#### Task 2.1: 实现CoA-Request监听

**技术实现**:
- 检查 `[coa]` 配置段
- 确保 `enable-coa=yes` 和 `radius-coa-port=3799`

**配置文件**:
```ini
[coa]
enable-coa=yes
radius-coa-port=3799
```

**验收条件**:
- 端口3799处于监听状态
- 能接收来自RADIUS服务器的CoA-Request

**测试方法**:
```bash
# 验证端口监听
netstat -tulpn | grep 3799

# 使用coa-test.sh发送测试请求
./tools/coa-test.sh test -s 192.168.1.1 -r testing123
```

---

#### Task 2.2: 实现Session-Timeout修改

**技术实现**:
- CoA请求中包含Session-Timeout (属性25)时，accel-ppp应更新会话超时

**验收条件**:
- 发送CoA-Request (属性25=新超时值)后，会话在新超时后断开

---

#### Task 2.3: 实现带宽限制

**技术实现**:
- 通过RADIUS属性实现带宽限制
- 上行: `RATE_LIMIT` (属性26.2) 或厂商私有属性
- 下行: 类似配置

**验收条件**:
- CoA限速后，用户带宽符合新限制

---

#### Task 2.4: 实现Disconnect-Request

**技术实现**:
- 接收Disconnect-Request后立即终止会话

**验收条件**:
- 发送CoA Disconnect后，用户会话立即断开

---

#### Task 2.5: 实现IP地址池切换

**技术实现**:
- 支持 `Framed-Pool` (属性26) 动态切换地址池

**验收条件**:
- CoA请求切换地址池后，用户获取新IP地址

---

#### Task 2.6: CoA测试工具完善

**现有工具**:
- `/home/lancer/projects/RNAS-OpenWrt/tools/coa-test.sh`

**需要增强**:
- 支持更多CoA场景测试
- 添加日志输出和结果验证

---

## 🎯 Phase 2: 会话管理 (第3周)

### Task 3.1: 会话列表API

**技术实现**:
- 利用accel-ppp的IPC接口或socket获取会话列表
- 或使用 `accel-cmd show sessions` 命令输出解析

**验收条件**:
- 获取当前所有在线会话 (用户名, IP, MAC, 连接时长)

---

### Task 3.2: 会话详情API

**验收条件**:
- 获取单个会话的详细信息: 流量(上行/下行), 时长, NAS-IP, NAS-Port

---

### Task 3.3: 强制下线API

**技术实现**:
- 使用 `accel-cmd kick <session_id>` 或 `accel-cmd terminate <session_id>`

**验收条件**:
- API调用后指定会话被终止

---

### Task 3.4: 会话限速API

**技术实现**:
- 调用accel-ppp的带宽控制接口

**验收条件**:
- 动态修改会话的上行/下行带宽

---

### Task 3.5: 并发限制

**技术实现**:
- 在accel-ppp配置或数据库层面实现

**验收条件**:
- 同一账号超过限制后，新登录被拒绝

---

### Task 3.6: 会话监控脚本

**技术实现**:
- 创建 `/home/lancer/projects/RNAS-OpenWrt/tools/session-monitor.sh` 增强版

**验收条件**:
- 实时输出在线会话列表，支持刷新

---

## 🎯 Phase 3: IPoE支持 (第4周)

### Task 4.1: IPoE服务器配置

**技术实现**:
- 使用 `/home/lancer/projects/RNAS-OpenWrt/configs/ipoe.conf` 配置模板
- 确保 `[ipoe]` 段配置正确

**配置文件**:
```ini
[ipoe]
verbose=1
username=format=ipoe
#interface=eth0
```

---

### Task 4.2: Option60识别

**技术实现**:
- 在RADIUS请求中包含Vendor-Specific-Option60

**验收条件**:
- 能识别不同厂商的DHCP请求

---

### Task 4.3: Option82插入

**技术实现**:
- 在DHCP请求中插入Option82信息

**验收条件**:
- RADIUS请求包含Circuit-ID和Remote-ID

---

### Task 4.4: IPoE RADIUS属性

**验收条件**:
- NAS-Port-Type=IPoE (虚拟)
- Framed-IP-Address正确

---

### Task 4.5: IPoE计费

**验收条件**:
- 与PPPoE相同的计费流程 (Start/Stop/Interim)

---

### Task 4.6: DHCP客户端测试

**技术实现**:
- 创建或增强测试脚本

**验收条件**:
- 能模拟IPoE用户进行测试

---

## 🎯 Phase 4: 协议完整测试 (第5周)

### Task 5.1-5.7: 协议测试

| 任务 | 验收条件 |
|------|----------|
| L2TP完整测试 | LAC/LNS隧道成功建立 |
| PPTP完整测试 | MPPE加密正常 |
| PPPoE双栈 | IPv4+IPv6同时在线 |
| IPoE双栈 | DHCPv4+DHCPv6 |
| 认证协议测试 | PAP/CHAP/MS-CHAP正常工作 |
| 协议一致性验证 | 符合RFC2865/2866 |
| 协议报文抓包验证 | tcpdump验证报文格式正确 |

---

## 🎯 Phase 5: WiFi AC仿真与无线功能 (第6周)

### Task 5.1: OpenWrt无线配置模板

**技术实现**:
- 创建 `/home/lancer/projects/RNAS-OpenWrt/configs/wireless` 模板

**配置文件示例**:
```ini
config wifi-device 'radio0'
    option type 'mac80211'
    option channel '36'
    option hwmode '11a'
    option htmode 'VHT80'

config wifi-iface
    option device 'radio0'
    option mode 'ap'
    option ssid 'RNAS-Test'
    option encryption 'wpa2'
    option key 'testpassword'
```

---

### Task 5.2: AC仿真核心框架

**技术实现**:
- 创建独立脚本管理AP仿真逻辑
- 支持AP注册、配置下发、心跳检测

---

### Task 5.3: WiFi RADIUS认证集成

**技术实现**:
- 支持802.1X (EAP) 认证
- RADIUS属性映射WiFi场景

**WiFi特有RADIUS属性**:
| 属性 | 说明 |
|------|------|
| NAS-Port-Type | Wireless-802.11 (19) |
| Calling-Station-Id | 用户MAC |
| Called-Station-Id | AP MAC |
| WLAN-Group-Id | SSID组ID |

---

### Task 5.4: WiFi计费流程实现

**验收条件**:
- WiFi用户上线发送Acct-Start
- WiFi用户下线发送Acct-Stop
- 周期性Acct-Update

---

### Task 5.5: WiFi CoA测试支持

**验收条件**:
- 限速、踢人等CoA操作在WiFi场景正常工作

---

### Task 5.6-5.8: 高级WiFi功能

| 任务 | 验收条件 |
|------|----------|
| 多SSID/VLAN测试 | 不同SSID对应不同VLAN |
| 简化控制协议仿真 | CAPWAP-like控制消息 |
| 漫游测试场景支持 | 802.11r基础 |

---

## 🎯 Phase 6: 网络组件集成 (第7周)

### Task 6.1: FreeRADIUS集成

**验收条件**:
- 与FreeRADIUS服务器完成完整AAA流程

---

### Task 6.2: OpenLDAP集成

**验收条件**:
- 用户认证通过LDAP目录服务

---

### Task 6.3: Windows AD集成

**验收条件**:
- 用户认证通过Active Directory

---

### Task 6.4: RADIUS代理转发

**验收条件**:
- 支持上游RADIUS服务器转发

---

### Task 6.5: 多组件联动测试

**验收条件**:
- RADIUS + LDAP 联合认证测试通过

---

## 🎯 Phase 7: LuCI管理界面 (第8-9周)

### 页面清单

| 页面 | 功能 | 优先级 |
|------|------|--------|
| 仪表盘 | 系统概览、协议状态、在线数 | P1 |
| 会话管理 | 在线列表、强制下线 | P1 |
| RADIUS配置 | 服务器、密钥、属性 | P0 |
| 协议配置 | PPPoE/L2TP/IPoE | P0 |
| 用户管理 | 本地用户CRUD | P0 |
| 组件集成 | LDAP/AD连接配置 | P1 |
| 协议监控 | 报文统计、日志 | P0 |
| 测试工具 | 批量测试控制 | P0 |

---

## 🎯 Phase 8: 测试验证 (第10周)

### Task 8.1: 自动化测试脚本

**验收条件**:
- 回归测试脚本覆盖所有P0功能

---

### Task 8.2: 协议一致性测试

**验收条件**:
- RFC2865/2866符合性验证通过

---

### Task 8.3: 组件集成测试

**验收条件**:
- FreeRADIUS/LDAP集成测试通过

---

### Task 8.4: 压力测试

**验收条件**:
- 100+并发会话测试通过

---

### Task 8.5: 文档完善

**验收条件**:
- 用户手册和开发文档完整

---

## 📦 交付物清单

### 配置文件 (configs/)
- [ ] `pppoe.conf` - PPPoE服务器配置 (已有)
- [ ] `ipoe.conf` - IPoE服务器配置 (已有)
- [ ] `l2tp.conf` - L2TP服务器配置 (已有)
- [ ] `wireless` - WiFi配置模板 (新建)
- [ ] `radius-client.conf` - RADIUS客户端配置 (新建)

### 脚本 (scripts/, tools/)
- [ ] `session-monitor.sh` - 会话监控 (增强)
- [ ] `coa-test.sh` - CoA测试工具 (增强)
- [ ] `wifi-ac-sim.sh` - WiFi AC仿真脚本 (新建)
- [ ] `test-*.sh` - 各协议测试脚本 (增强)

### 文档 (docs/)
- [ ] `IMPLEMENTATION_PLAN.md` - 本实施计划
- [ ] `USER_GUIDE.md` - 用户手册 (新建)
- [ ] `API_REFERENCE.md` - API参考 (新建)

### LuCI插件 (luci-app-rnas/)
- [ ] 仪表盘页面
- [ ] 会话管理页面
- [ ] RADIUS配置页面
- [ ] 协议配置页面
- [ ] 用户管理页面
- [ ] WiFi配置页面 (新建)
- [ ] 测试工具页面

---

## 🔄 依赖关系

```
Phase 1 (RADIUS)
    ↓
Phase 2 (会话管理) - 依赖Phase 1
    ↓
Phase 3 (IPoE) - 依赖Phase 1
    ↓
Phase 4 (协议测试) - 依赖Phase 2, 3
    ↓
Phase 5 (WiFi AC) - 依赖Phase 1, 4
    ↓
Phase 6 (组件集成) - 独立
    ↓
Phase 7 (LuCI) - 依赖Phase 1-6
    ↓
Phase 8 (测试验证) - 依赖全部
```

---

## ⚠️ 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| accel-ppp配置限制 | 某些功能无法实现 | 使用脚本辅助实现 |
| WiFi驱动兼容性 | 硬件依赖 | 使用通用驱动配置模板 |
| RADIUS服务器配置 | 需要外部配合 | 提供完整配置示例 |
| 测试环境搭建 | 需要多组件 | 使用Docker容器化 |

---

*文档版本: 1.0*  
*创建日期: 2026-04-21*  
*等待用户审核后开始实施*
