# RNAS — RADIUS Network Access Server

**Standalone NAS simulation platform for x86 Linux — unified config engine, web dashboard, systemd-native.**

[![CI](https://github.com/Lancer2049/RNAS/actions/workflows/ci.yml/badge.svg)](https://github.com/Lancer2049/RNAS/actions/workflows/ci.yml)

RNAS deep-integrates **accel-ppp** with standard Linux networking (dnsmasq, nftables, tc, strongSwan) under a unified `/etc/rnas/` configuration tree and a single-page web dashboard — no OpenWrt firmware required. Runs on any Debian/Ubuntu/UOS x86_64 host or VM.

---

## 📊 Project Status

```
Phase 1 (Core Platform)   ████████████████████ 100%  Config engine + API + Dashboard
Phase 2 (Network + QoS)   ████████████████████ 100%  dnsmasq/nftables/tc/SNMP/DHCP relay
Phase 3 (VPN + Hotspot)   ████████████████████ 100%  strongSwan/WireGuard/OpenVPN/802.1X
Phase 4 (HA + Packaging)  ████████████████████ 100%  keepalived/logrotate/CI pipeline

v3 Extensions             ████████████████████ 100%  13 vendor dicts, LAC/LNS, scenarios, fault inject
```

---

## 🎯 Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                 RNAS Web Dashboard (Vue.js SPA)              │
│          Status │ Sessions │ Config │ Disconnect            │
├──────────────────────────────────────────────────────────────┤
│                    rnas-api (FastAPI)                        │
├──────────────────────────────────────────────────────────────┤
│                    rnas-config engine                        │
│        /etc/rnas/*.conf  ──generate──►  native configs       │
├──────────┬──────────┬──────────┬──────────┬─────────────────┤
│ accel-ppp│ dnsmasq  │ nftables │  tc/SQM  │  strongSwan/WG  │
│(PPPoE/   │(DHCP/DNS)│(firewall)│(CAKE/    │  keepalived     │
│ L2TP/IPoE│          │          │ fq_codel) │  CoovaChilli    │
├──────────┴──────────┴──────────┴──────────┴─────────────────┤
│              Standard x86 Linux Kernel + systemd            │
│          (Debian / Ubuntu / UOS — no firmware needed)        │
└──────────────────────────────────────────────────────────────┘
```

**Design principles:**
- **Fusion, not aggregation** — accel-ppp and Linux services share one config tree, not packaged side-by-side
- **One config tree** — `/etc/rnas/` serves UCI-style config for all services
- **systemd native** — services use systemd units, not procd or init scripts
- **Installable, not flashable** — `bash scripts/install.sh` on any x86 Linux

---

## 📁 Project Structure

```
RNAS/
├── cmd/rnas-config/                  # Unified config engine (Python)
│   └── rnas_config.py               #   INI parser + tree walker + accel-ppp generator
├── web/
│   ├── api/                          # FastAPI backend
│   │   ├── main.py                   #   App entry point
│   │   ├── routes/status.py          #   /api/status, /api/sessions, disconnect
│   │   ├── routes/config.py          #   /api/config CRUD
│   │   └── services/accel_cmd.py     #   accel-cmd subprocess wrapper
│   └── frontend/                     # Vue.js 3 SPA dashboard
│       ├── src/App.vue               #   Main layout with status + sessions
│       ├── src/components/
│       │   ├── StatusCard.vue        #   Uptime, CPU, mem, RADIUS state
│       │   └── SessionsTable.vue     #   Live table with disconnect action
│       └── vite.config.js
├── configs/                          # /etc/rnas/ config templates
│   ├── rnas.conf                     #   Global settings
│   ├── access.d/                     #   accel-ppp: core, radius, pppoe, ipoe, ...
│   └── network.d/                    #   interfaces, dhcp, firewall
├── systemd/                          # systemd unit files
│   ├── rnas.target                   #   Master target
│   ├── rnas-accel-ppp.service        #   accel-ppp daemon
│   ├── rnas-dnsmasq.service          #   DHCP/DNS
│   └── rnas-firewall.service         #   nftables firewall
├── tools/                            # CLI testing & monitoring
│   ├── coa-test.sh                   #   CoA/Disconnect test tool
│   ├── acct-verify.sh                #   RFC 2866 compliance checker
│   ├── radius-capture.sh             #   tcpdump for RADIUS ports
│   └── post-reboot-verify.sh         #   Post-deployment AAA verification
├── tests/                            # Test suites
│   └── integration/
│       └── test-config-to-daemon.sh  #   Config generation → daemon start
├── scripts/
│   ├── install.sh                    #   One-command installer
│   └── build/build-accel-ppp.sh      #   Source build script
├── luci-app-rnas/                    #   Legacy LuCI (v1, for OpenWrt)
├── package/accel-ppp/                #   OpenWrt package (secondary target)
├── docker/                           #   Docker test environments
└── docs/plans/                       #   Design & implementation plans
```

---

## 🔧 Quick Start

### Install on Debian/Ubuntu/UOS (x86_64)

```bash
git clone https://github.com/Lancer2049/RNAS.git
cd RNAS
sudo bash scripts/install.sh
```

### Start the web dashboard

```bash
# Start API
cd web/api
PYTHONPATH=. uvicorn main:app --host 0.0.0.0 --port 8099 &

# Start frontend dev server (or serve dist/ with nginx)
cd web/frontend
npm install && npm run dev
```

### Run tests

```bash
# Config → daemon integration test
bash tests/integration/test-config-to-daemon.sh

# CoA disconnect test
./tools/coa-test.sh disconnect -s 192.168.0.85 -r testing123 -u testuser

# Full PPPoE test suite
./tests/pppoe/test-pppoe.sh all
```

---

## 🚧 Roadmap

| Phase | Feature | Status |
|-------|---------|--------|
| ✅ v1 | accel-ppp UCI + LuCI + CoA tools | Complete |
| ✅ v1 | Three-node AAA end-to-end verified | Complete |
| ✅ v2 P1 | `/etc/rnas/` unified config + rnas-config engine | Complete |
| ✅ v2 P1 | FastAPI backend + Vue.js dashboard | Complete |
| ✅ v2 P1 | systemd units + install script | Complete |
| ✅ v2 P1 | dnsmasq/nftables config generators | Complete |
| ✅ v2 P2 | tc/SQM QoS integration | Complete |
| ✅ v2 P2 | strongSwan / WireGuard / OpenVPN | Complete |
| ✅ v2 P3 | keepalived HA + SNMP monitoring | Complete |
| ✅ v3 | DHCP relay, RADIUS dicts (13 vendors), 802.1X, LAC/LNS | Complete |
| ✅ v3 | Fault injection, compatibility test, scenarios, WebSocket | Complete |

---

## 🌐 Three-Node Test Topology

```
VM1: RNAS              192.168.0.84    UOS Desktop + accel-ppp (PPPoE Server)
VM2: FreeRADIUS+AIRadius 192.168.0.85  RADIUS Server + Web Management
VM3: CPE Client         192.168.0.82   Ubuntu (PPPoE/L2TP client)
```

---

## 📄 License

GPL-2.0 — see [LICENSE](LICENSE)

---

## 🙏 Built On

- [accel-ppp](https://github.com/accel-ppp/accel-ppp) — High-performance VPN server
- [FastAPI](https://fastapi.tiangolo.com/) — Python web framework
- [Vue.js](https://vuejs.org/) — Frontend framework
- [FreeRADIUS](https://freeradius.org/) — RADIUS server
- [AIRadius](https://github.com/Lancer2049/AIRadius) — RADIUS web management UI (sibling project)
