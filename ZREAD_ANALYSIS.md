# RNAS 项目分析报告

> 来源：https://zread.ai/Lancer2049/RNAS
> Zread AI 自动分析生成（部分深层内容需订阅）

---

## 概述

RNAS（RADIUS Network Access Server）是一个**面向 x86 Linux 的独立 NAS 模拟平台**，深度整合 accel-ppp 与 Linux 标准网络服务（dnsmasq、nftables、tc、strongSwan、keepalived），统一配置树位于 `/etc/rnas/`，提供 Web Dashboard 和 FastAPI 管理 API。

与 OpenWrt 方案不同，RNAS 无需刷写固件——通过一键安装脚本部署在任何 Debian/Ubuntu/UOS x86_64 主机或虚拟机上，全部运行于 systemd 之下。

### 解决什么问题

测试 RADIUS 认证、计费和 CoA 通常需要商业 BRAS 硬件或 OpenWrt 上的复杂多软件包配置。RNAS 将这一切整合为单一可安装平台：一个配置树驱动 12 个配置生成器，5 种接入协议通过 accel-ppp 同时运行，Vue.js Dashboard 提供实时会话可视化——全都在标准 Linux 虚拟机上完成。

核心理念：**融合而非聚合**——accel-ppp 和 Linux 服务共享一个配置树。

## 关键数据

| 指标 | 数值 |
|------|------|
| 接入协议 | 5/5 已验证 (PPPoE, PPTP, L2TP, SSTP, IPoE) |
| 网络服务 | 10/10 在线 |
| RADIUS 字典 | 14 厂商类别, 693 属性 (192 标准 + 501 VSA) |
| 测试场景 | 9 预设 JSON 场景 |
| 前端组件 | 37 个 Vue 组件, 25+ 页面 |
| Playwright E2E | 31/32 通过 |
| 配置生成器 | 12 个原生格式生成器 |

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Vue.js 3 SPA Dashboard                   │
│              37 组件 · 25+ 页面 · WebSocket 实时推送         │
├────────────────────────┬────────────────────────────────────┤
│                  FastAPI Backend (uvicorn 4 workers)         │
│  8 路由模块 · WebSocket /api/ws (3秒推送)                   │
├────────────────────────┬────────────────────────────────────┤
│              原生 Linux 服务 (systemd)                       │
│  accel-ppp · dnsmasq · nftables · tc · strongSwan ·  WG     │
├────────────────────────┬────────────────────────────────────┤
│              rnas-config (Python 配置引擎)                   │
│   INI 解析器 → 树遍历器 → 12 个原生配置生成器               │
├────────────────────────┬────────────────────────────────────┤
│              /etc/rnas/ 统一配置树                           │
└─────────────────────────────────────────────────────────────┘
```

## 项目结构

```
RNAS/
├── cmd/rnas-config/         # 配置引擎 (770行 Python)
├── cmd/rnas-dict/           # RADIUS 字典工具
├── web/
│   ├── api/                 # FastAPI 后端 (8路由模块)
│   │   ├── main.py          # 入口, WebSocket, 热榜登录
│   │   ├── routes/          # status, config, aaa, tools, extra...
│   │   └── services/        # accel-cmd 子进程包装
│   ├── frontend/            # Vue.js 3 SPA (37组件)
│   └── server.py            # 标准库 HTTP 服务器(备用)
├── configs/                 # /etc/rnas/ 配置模板
│   ├── access.d/            # accel-ppp 协议配置
│   ├── network.d/           # 网络服务配置
│   ├── vpn.d/               # VPN 隧道配置
│   ├── scenarios/           # 9 个 JSON 测试场景
│   └── dictionary/          # 13 厂商 VSA 字典 + RFC
├── systemd/                 # 9 服务单元 + rnas.target
├── scripts/                 # 安装 + 运维脚本
├── tests/                   # 回归 + 压力 + 兼容测试
├── tools/                   # CLI 诊断工具
├── docker/                  # Docker 测试环境 (4容器)
└── docs/                    # 设计文档 + API 参考
```

## RADIUS 字典统计

| 来源 | 属性数 | 说明 |
|------|--------|------|
| RFC 标准 | 192 | User-Name, NAS-IP, Framed-IP, Acct-Status-Type... |
| ZTE | 125 | ZTE BRAS 测试 |
| Huawei | 50 | ME60/NE40E BRAS 仿真 |
| H3C | 40 | vBRAS 仿真 |
| Juniper | 40 | MX 系列测试 |
| Ruijie | 40 | 锐捷 BRAS 测试 |
| Cisco | 20+ | ASR/ISR 测试 |
| 其他厂商 | 各约 20 | MikroTik, Aruba, Ericsson, Arista... |

## 测试覆盖

| 类别 | 通过率 |
|------|--------|
| 回归测试 | 11/11 ✅ |
| 压力测试 (PPPoE) | 4/5 ✅ |
| 故障注入 (5场景) | 5/5 ✅ |
| 厂商兼容 (13厂商) | ✅ |
| 启动验证 | 17/18 ✅ |
| Playwright E2E | 31/32 ✅ |

## 部署方式

| 方式 | 命令 | 适用 |
|------|------|------|
| 裸机安装 | `sudo bash scripts/install.sh` | 生产/实验室 |
| Docker | `docker compose up -d` | 快速测试 |
| 源码运行 | `uvicorn main:app --port 8099` | 开发调试 |

## 设计原则

1. **融合而非聚合** — accel-ppp 和 Linux 服务共享一个配置树
2. **单一配置树** — `/etc/rnas/` UCI 风格 INI 配置
3. **systemd 原生** — 9 服务单元由 `rnas.target` 编排
4. **可安装而非刷写** — 无需固件，`bash scripts/install.sh` 即装即用

---

> 完整深度分析需 zread 订阅。访问 https://zread.ai/Lancer2049/RNAS 获取最新内容。
