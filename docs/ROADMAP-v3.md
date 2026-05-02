# RNAS v3 — 功能路线图

> 对标：华三 vBRAS、华为 ME60/NE40E、RouterOS、OpenWrt  
> 定位：网络工程师仿真测试平台 + RADIUS 服务器协议开发辅助工具

## 一、已完成 (v2)

| 模块 | 功能 | 状态 |
|------|------|------|
| 接入协议 | PPPoE/PPTP/L2TP/SSTP/IPoE + CoA | ✅ 全部端到端验证 |
| AAA | RADIUS auth/acct/CoA + FreeRADIUS PostgreSQL 存储 | ✅ |
| 配置引擎 | `/etc/rnas/` 21 模板 + 10 生成器 | ✅ |
| Web 仪表板 | 7 标签页 (概览/会话/网络/配置/服务/工具/系统) | ✅ |
| VPN 服务 | strongSwan/WireGuard/OpenVPN | ✅ |
| 网络基础 | dnsmasq/nftables/tc cake QoS/HA keepalived | ✅ |
| 监控 | SNMP 161 | ✅ |
| 自动化测试 | 11/11 回归 + 8/8 Playwright + 17/18 启动验证 | ✅ |
| QoS | 分级带宽 (iptables MARK + tc HTB) | ✅ |

## 二、v3.0 — 仿真测试核心能力 (Phase 1)

对标 RouterOS 和商业 BRAS 的仿真测试功能。

| 编号 | 功能 | 参考 | 说明 |
|------|------|------|------|
| P1-01 | DHCP Relay | RouterOS/华为 | DHCP 中继到 VM2 RADIUS，支持 Option 82 |
| P1-02 | RADIUS 属性字典 | 华为 VSA | 内置常用厂商字典 (华为/MikroTik/Cisco)，Web 界面可编辑 |
| P1-03 | 并发压力测试 | vBRAS | 模拟 N 个用户同时拨号，测量认证延迟和成功率 |
| P1-04 | 会话持久化 | 华为 | 重启 accel-ppp 后恢复活跃会话 (通过 radacct) |
| P1-05 | 流量生成器 | RouterOS BTest | 内建 iperf-like 工具，测每个会话的实际带宽 |
| P1-06 | CoA 批量操作 | 网管系统 | 批量 Disconnect/CoA，支持 CSV 导入用户列表 |
| P1-07 | 协议录制回放 | — | 录制 RADIUS/PPP 报文交互，支持回放分析和调试 |

## 三、v3.1 — 协议扩展 (Phase 2)

补充商业 BRAS 支持的协议和认证方式。

| 编号 | 功能 | 参考 | 说明 |
|------|------|------|------|
| P2-01 | 802.1X 认证 | 华为 BRAS | EAP-PEAP/EAP-TLS + RADIUS，需要 hostapd |
| P2-02 | Captive Portal (Hotspot) | RouterOS/CoovaChilli | Web 认证门户 + RADIUS 后端，自定义登录页 |
| P2-03 | MAC 认证 (MAC-Auth) | 华为 | 根据 MAC 地址自动认证，适用于 IPTV/物联网 |
| P2-04 | L2TP LAC 模式 | 华为/华三 | RNAS 作为 L2TP 客户端连接到上游 LNS |
| P2-05 | IPv6 双栈 | 华为 | PPPoE/IPoE 同时分配 IPv4 和 IPv6 地址 (IA_NA + IA_PD) |
| P2-06 | GRE/IPIP 隧道 | RouterOS | 支持 GRE/IPIP 隧道终结，适配 VPN 测试 |

## 四、v3.2 — 管理增强 (Phase 3)

对标商业 BRAS 的运维管理能力。

| 编号 | 功能 | 参考 | 说明 |
|------|------|------|------|
| P3-01 | REST API 完善 | RouterOS API | 完整 CRUD 接口：用户/会话/配置/统计 |
| P3-02 | CLI 命令行 | 华三/华为 CLI | `rnas-cli` 交互式命令行，支持 tab 补全 |
| P3-03 | 实时流量图 | RouterOS Torch | Web 仪表板实时显示每用户/每协议的吞吐量 |
| P3-04 | 告警系统 | 华为/网管 | 基于阈值的告警 (会话数/认证失败率/带宽) |
| P3-05 | Syslog/NetFlow | 华为 | 结构化日志输出，NetFlow v5/v9 流数据导出 |
| P3-06 | 配置导入导出 | RouterOS | 一键导出/导入全部配置 (JSON/YAML)，支持 Git 版本控制 |
| P3-07 | WebSocket 实时推送 | 现代 Web | Dashboard 通过 WebSocket 推送实时数据，替代轮询 |

## 五、v3.3 — 高级仿真 (Phase 4)

专业网络仿真和协议分析工具。

| 编号 | 功能 | 参考 | 说明 |
|------|------|------|------|
| P4-01 | RADIUS 协议编辑器 | — | 可视化构建 RADIUS 报文，发送并查看响应，支持自定义属性 |
| P4-02 | 故障注入 | — | 模拟网络故障：丢包/延迟/RADIUS 超时/认证拒绝 |
| P4-03 | 协议兼容性测试 | — | 自动测试 RADIUS 服务器对各种客户端/属性的兼容性 |
| P4-04 | 场景编排 | — | 预设测试场景 (家庭宽带/企业 VPN/IPTV)，一键启动 |
| P4-05 | 性能基准 | iPerf/BTest | 内置性能测试框架，生成可对比的基准报告 |
| P4-06 | Docker 化部署 | — | RNAS 打包为 Docker 镜像，支持 docker-compose 一键启动全家桶 |

## 六、优先级排序

### 🔴 立即 (本周)
```
P1-01 DHCP Relay     — 完善 IPoE 场景
P1-02 RADIUS 字典    — 协议开发基础能力
P2-01 802.1X         — 企业网络测试核心需求
P3-06 配置导入导出    — 快速搭建测试环境
```

### 🟡 短期 (本月)
```
P1-03 并发测试        P1-05 流量生成器
P2-05 IPv6 双栈       P3-07 WebSocket
P4-06 Docker 化       P2-03 MAC 认证
```

### 🟢 中期
```
P1-07 协议录播        P2-02 Hotspot
P3-01 REST API        P3-03 实时流量图
P4-01 RADIUS 编辑器   P4-04 场景编排
```

### ⚪ 长期
```
P2-04 L2TP LAC        P2-06 GRE 隧道
P3-02 CLI             P3-04 告警
P4-02 故障注入        P4-03 兼容性测试
```

## 七、每项验收标准

每个 P 级任务完成后必须：
1. 端到端手动验证通过
2. Playwright 测试 (如有 UI) 通过
3. 自动化回归脚本追加相关测试项
4. Git 提交 + Push

---

*生成日期: 2026-05-02 | 版本: v3.0-draft*
