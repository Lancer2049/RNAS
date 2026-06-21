# RNAS — RADIUS Network Access Server

**Standalone NAS simulation platform for x86 Linux — unified config engine, web dashboard, systemd-native.**

[![CI](https://github.com/Lancer2049/RNAS/actions/workflows/ci.yml/badge.svg)](https://github.com/Lancer2049/RNAS/actions/workflows/ci.yml)
[![Zread Analysis](https://img.shields.io/badge/Zread-Analysis-blue)](https://zread.ai/Lancer2049/RNAS)

RNAS deep-integrates **accel-ppp** with standard Linux networking (dnsmasq, nftables, tc, strongSwan, keepalived) under a unified `/etc/rnas/` configuration tree and a single-page web dashboard — no OpenWrt firmware required. Runs on any Debian/Ubuntu/UOS x86_64 host or VM.

> **Fusion, not aggregation**: accel-ppp and Linux services share one config tree, not packaged side-by-side. A single edit to `/etc/rnas/access.d/pppoe.conf` propagates to the accel-ppp daemon, nftables rules, and tc QoS queues.

---

## Quick Start

```bash
git clone https://github.com/Lancer2049/RNAS.git
cd RNAS
sudo bash scripts/install.sh

# Start the web dashboard
cd web/api && PYTHONPATH=. uvicorn main:app --host 0.0.0.0 --port 8099
```

Open `http://<host>:8099` to access the RouterOS-style dashboard.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Vue.js 3 SPA Dashboard                       │
│    37 components · 25+ pages · WebSocket real-time push      │
└────────────────────────┬────────────────────────────────────┘
                         │ REST + WebSocket
┌────────────────────────▼────────────────────────────────────┐
│                 FastAPI Backend (uvicorn 4 workers)          │
│  8 route modules: status · config · tools · system · aaa    │
│  · sim · extra · WebSocket /api/ws (3s push)                │
└────────────────────────┬────────────────────────────────────┘
                         │ accel-cmd / subprocess
┌────────────────────────▼────────────────────────────────────┐
│              Native Linux Services (systemd)                 │
│  accel-ppp · dnsmasq · nftables · tc (CAKE/fq_codel/HTB)   │
│  strongSwan · WireGuard · OpenVPN · keepalived · snmpd      │
└────────────────────────┬────────────────────────────────────┘
                         │ config generation
┌────────────────────────▼────────────────────────────────────┐
│              rnas-config (Python Config Engine)              │
│   INI parser → Tree walker → 12 native config generators    │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│              /etc/rnas/ Unified Config Tree                  │
│  access.d/ · network.d/ · vpn.d/ · wireless.d/ · scenarios/ │
│  dictionary/ (13 vendor VSAs)                                │
└─────────────────────────────────────────────────────────────┘
```

### Design Principles

| Principle | What It Means |
|-----------|---------------|
| **Fusion, not aggregation** | accel-ppp and Linux services share one config tree |
| **One config tree** | `/etc/rnas/` serves UCI-style INI config for all services |
| **systemd native** | 9 service units orchestrated by `rnas.target` |
| **Installable, not flashable** | `bash scripts/install.sh` on any x86 Linux, no firmware |

---

## Access Protocols (5/5 Verified)

| Protocol | Port | Auth | RADIUS Acct | CoA |
|----------|------|------|-------------|-----|
| **PPPoE** | Ethernet | PAP/CHAP/MPPE | ✅ Start/Stop | ✅ Disconnect-ACK |
| **PPTP** | TCP 1723 | MPPE | ✅ Start/Stop | ✅ Disconnect-ACK |
| **L2TP** | UDP 1701 | IPsec | ✅ Start/Stop | ✅ Disconnect-ACK |
| **SSTP** | TCP 443 | HTTPS/TLS | ✅ Start/Stop | Via DAE |
| **IPoE** | Ethernet | DHCP+ | ✅ Start/Stop | ✅ Disconnect-ACK |

## Network Services (10/10 Active)

| Service | Port | Role | Status |
|---------|------|------|--------|
| accel-ppp | 3799(DAE), 1723, 1701, 443 | Access concentrator | ✅ |
| Web API | 8099 | Management + dashboard | ✅ |
| QoS daemon | — | Traffic shaping (tc HTB) | ✅ |
| dnsmasq | 53 (DNS) | DHCP/DNS resolution | ✅ |
| strongSwan | 500/4500 | IPsec VPN | ✅ |
| WireGuard | 51820 | WireGuard VPN | ✅ |
| OpenVPN | 1194 | OpenVPN server | ✅ |
| keepalived | VRRP | High availability | ✅ |
| snmpd | 161 | SNMP monitoring | ✅ |

## RADIUS Dictionary Support (14 Vendor Categories)

| Vendor | Attributes | Use Case |
|--------|-----------|----------|
| **Standard (RFC)** | 192 | User-Name, NAS-IP-Address, Framed-IP-Address, Acct-Status-Type... |
| Huawei | 50 | ME60/NE40E BRAS simulation |
| H3C | 40 | vBRAS simulation |
| Cisco | 20+ | ASR/ISR testing |
| ZTE | 125 | ZTE BRAS testing |
| Juniper | 40 | MX series testing |
| MikroTik | — | RouterOS compatibility |
| Aruba | — | Wireless controller testing |
| Ericsson | — | Mobile backhaul |
| Arista | — | Data center switching |
| NVIDIA (Mellanox) | — | High-performance networking |
| Ruijie | — | Ruijie BRAS testing |
| Microsoft | — | MS-CHAPv2 attributes |
| WISPr | — | Hotspot/captive portal |

---

## Technology Stack

| Layer | Technology | Role |
|-------|-----------|------|
| Access Server | accel-ppp (source-built) | PPPoE/PPTP/L2TP/SSTP/IPoE server with RADIUS client |
| Config Engine | Python 3 (stdlib) | INI parser, tree walker, 12 native config generators |
| Management API | FastAPI 3.0 + uvicorn | REST endpoints, WebSocket real-time push |
| Frontend | Vue.js 3 + Vite | SPA dashboard, 37 components, RouterOS-style theme |
| RADIUS Server | FreeRADIUS 3.0 + PostgreSQL | Auth, accounting, CoA origin |
| DHCP/DNS | dnsmasq | DHCP server, DNS forwarding, relay support |
| Firewall | nftables | Packet filtering, NAT, port rules |
| QoS | tc (CAKE/fq_codel/HTB) | Per-user bandwidth shaping via RADIUS attributes |
| VPN | strongSwan, WireGuard, OpenVPN | IPsec, WireGuard, OpenVPN tunnel termination |
| HA | keepalived | VRRP virtual IP failover |
| Testing | Playwright, bash, Python | E2E, integration, regression, compatibility |

---

## Three-Node Test Topology

```
VM1 (CPE Client)     VM2 (RADIUS Server)     VM3 (RNAS NAS)
192.168.0.201        192.168.0.202           192.168.0.203
┌──────────────┐    ┌──────────────┐        ┌──────────────┐
│ pppd client  │    │ FreeRADIUS   │        │ accel-ppp    │
│ l2tp client  │◄──►│ PostgreSQL   │◄──────►│ FastAPI      │
│ sstp client  │    │ AIRadius Web│ RADIUS  │ Vue.js SPA   │
│ wg/ipsec     │    │ CoA origin   │ 1812/3 │ nftables     │
└──────────────┘    └──────────────┘        └──────────────┘
```

Test credentials: `testuser` / `testpass` in FreeRADIUS radcheck.

---

## Project Structure

```
RNAS/
├── cmd/rnas-config/              # Config engine
│   └── rnas_config.py            # INI parser → tree walker → 12 generators (770 lines)
├── cmd/rnas-dict/                # RADIUS dictionary tool
│   └── dictionary.py
├── web/
│   ├── api/                      # FastAPI backend (8 route modules)
│   │   ├── main.py               # App entry, WebSocket, hotspot login
│   │   ├── routes/               # status, config, aaa, tools, sim, extra, system
│   │   └── services/             # accel-cmd subprocess wrapper
│   ├── frontend/                 # Vue.js 3 SPA (37 components)
│   │   ├── src/App.vue           # RouterOS dark theme, hash routing, 25+ pages
│   │   └── src/components/       # IPManager, TrafficMonitor, SessionsTable, etc.
│   └── server.py                 # Stdlib HTTP server (fallback)
├── configs/                      # /etc/rnas/ config templates (21+ files)
│   ├── rnas.conf                 # Global settings
│   ├── access.d/                 # accel-ppp: core, radius, pppoe, ipoe, l2tp, ...
│   ├── network.d/                # interfaces, dhcp, firewall, ipv6, vlan
│   ├── vpn.d/                    # ipsec, wireguard, openvpn, gre, eoip, ipip, vxlan
│   ├── scenarios/                # 9 JSON test scenarios (home-broadband, enterprise-vpn, ...)
│   └── dictionary/               # 13 vendor VSA dictionaries + RFC standard
├── systemd/                      # 9 service units + rnas.target orchestration
├── scripts/                      # Installer + operational scripts
│   ├── install.sh                # One-command installer (6 steps)
│   ├── rnas-qosd.py              # QoS daemon
│   └── rnas-dhcp-relay.py        # DHCP relay agent
├── tests/                        # Protocol + regression + stress + compat
│   ├── run-all-tests.sh          # 5-protocol suite runner
│   ├── regression/               # 11/11 full regression
│   ├── stress/                   # Concurrent + fault injection (5 scenarios)
│   └── compat/                   # 13-vendor VSA compatibility
├── tools/                        # CLI diagnostics
│   ├── coa-test.sh               # CoA/Disconnect testing
│   ├── acct-verify.sh            # RFC 2866 accounting compliance
│   └── radius-capture.sh         # RADIUS packet capture
├── docker/                       # Docker test environment (4 containers)
│   └── docker-compose.yml        # accel-ppp, freeradius, api, web
├── docs/                         # Design docs + implementation plans + API reference
├── luci-app-rnas/                # Legacy LuCI app (v1, OpenWrt secondary target)
└── package/accel-ppp/            # OpenWrt package (secondary target)
```

---

## Testing

| Category | Scope | Pass Rate |
|----------|-------|-----------|
| **Regression** | PPPoE/PPTP/L2TP/SSTP/IPoE + Web + DB | 11/11 ✅ |
| **Stress (PPPoE)** | Concurrent dial-in (5 users) | 4/5 ✅ |
| **Fault Injection** | 5 scenarios (timeout, reject, packet loss) | 5/5 ✅ |
| **Vendor Compat** | 13-vendor VSA compatibility | ✅ |
| **Boot Verify** | Post-deployment AAA verification | 17/18 ✅ |
| **Playwright E2E** | Dashboard + full integration (32 tests) | 31/32 ✅ |
| **Config→Daemon** | Config generation → daemon startup | ✅ |

---

## Deployment Options

| Model | Method | Best For |
|-------|--------|----------|
| **Bare metal** | `sudo bash scripts/install.sh` | Production/lab on Debian/Ubuntu/UOS |
| **Docker Compose** | `docker compose up -d` | Quick local testing (4 containers) |
| **Source** | Clone + `uvicorn main:app --port 8099` | Development & debugging |

---

## Roadmap

| Phase | Feature | Status |
|-------|---------|--------|
| ✅ v1 | accel-ppp UCI + LuCI + CoA tools | Complete |
| ✅ v1 | Three-node AAA end-to-end verified | Complete |
| ✅ v2 | `/etc/rnas/` unified config + FastAPI + Vue.js dashboard | Complete |
| ✅ v2 | systemd units + install script | Complete |
| ✅ v2 | dnsmasq/nftables/tc QoS generators | Complete |
| ✅ v2 | strongSwan / WireGuard / OpenVPN | Complete |
| ✅ v2 | keepalived HA + SNMP monitoring | Complete |
| ✅ v3 | DHCP relay, RADIUS dicts (13 vendors), 802.1X, LAC/LNS | Complete |
| ✅ v3 | Fault injection, scenarios, WebSocket real-time dashboard | Complete |
| ✅ v3 | RouterOS-style UI, IP Manager (8 tabs), RADIUS protocol monitor | Complete |
| 🔜 v4 | Bandwidth Test tool, System Scheduler, NAT masquerade presets | In Progress |

---

## License

GPL-2.0 — see [LICENSE](LICENSE)

## Built On

- [accel-ppp](https://github.com/accel-ppp/accel-ppp) — High-performance VPN server
- [FastAPI](https://fastapi.tiangolo.com/) — Python web framework
- [Vue.js](https://vuejs.org/) — Frontend framework
- [FreeRADIUS](https://freeradius.org/) — RADIUS server
- [AIRadius](https://github.com/Lancer2049/AIRadius) — RADIUS web management UI (sibling project)

## Analysis

This project was analyzed by [Zread AI](https://zread.ai/Lancer2049/RNAS) — see [`ZREAD_ANALYSIS.md`](ZREAD_ANALYSIS.md) for the full report.
