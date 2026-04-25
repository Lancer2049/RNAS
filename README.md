# RNAS — RADIUS Network Access Server

**OpenWrt-based software NAS with accel-ppp deep integration.**

A specialized OpenWrt distribution that embeds accel-ppp as a fully native service — appearing not as a third-party add-on, but as if it were built into OpenWrt from day one. Provides RADIUS AAA (Authentication, Authorization, Accounting) and CoA for PPPoE/IPoE/L2TP/PPTP access protocols.

---

## 📊 Project Status

```
Phase 0 (Code Integration)  ████████████████████ 100%  UCI + procd + package build
Phase 1 (RADIUS Core)       ████████████████████ 100%  CoA tools + accounting verify + test suite
Phase 2 (E2E Testing)       ██████░░░░░░░░░░░░░░  30%  Awaiting real OpenWrt deployment
Phase 3 (LuCI Web UI)       ████░░░░░░░░░░░░░░░░  20%  Skeleton exists, needs live data wiring
Phase 4 (Image Build)       ██░░░░░░░░░░░░░░░░░░  10%  Package builds, no bootable image yet
```

---

## 🎯 Architecture

```
┌──────────────┐   PPPoE/IPoE    ┌────────────────────┐   RADIUS    ┌──────────────┐
│   CPE Client │ ──────────────→ │       RNAS         │ ─────────→ │  FreeRADIUS  │
│   (VM3)      │                 │  (OpenWrt + accel)  │ ←───────── │  + AIRadius  │
└──────────────┘                 └────────────────────┘    CoA      └──────────────┘
                                        │
                                  ┌─────▼─────┐
                                  │  LuCI Web │   Port 80/443
                                  │  accel-cmd│
                                  └───────────┘
```

RNAS is **not** a general-purpose NAS or router. It is a **RADIUS NAS appliance**:
- Terminates PPPoE/IPoE/L2TP/PPTP connections from CPE clients
- Authenticates users via RADIUS (forwarding to FreeRADIUS or equivalent)
- Sends complete RADIUS Accounting records (Start/Interim/Stop)
- Accepts CoA (Change of Authorization) and Disconnect-Request via port 3799

---

## 📁 Project Structure

```
RNAS/
├── README.md
├── package/                          # OpenWrt package build system
│   └── accel-ppp/
│       ├── Makefile                  # Standard OpenWrt package definition
│       └── patches/001-openwrt-compat.patch
├── root/                             # OpenWrt filesystem overlay (UCI + init)
│   └── etc/
│       ├── config/rnas               # UCI configuration
│       ├── init.d/accel-ppp          # procd service (hot-reload via SIGHUP)
│       └── uci-defaults/rnas         # First-boot defaults
│   └── usr/sbin/accel-ppp-uci        # UCI → accel-ppp.conf translator
├── luci-app-rnas/                    # LuCI web management interface
│   └── luasrc/
├── configs/                          # Protocol config templates
│   ├── pppoe.conf
│   ├── ipoe.conf
│   └── l2tp.conf
├── tools/                            # CLI testing & monitoring tools
│   ├── coa-test.sh                   # CoA/Disconnect test tool
│   ├── acct-verify.sh                # RFC 2866 accounting compliance check
│   ├── radius-capture.sh             # tcpdump wrapper for RADIUS ports
│   └── session-monitor.sh            # Real-time session display
├── tests/                            # Test suites
│   ├── pppoe/test-pppoe.sh           # 10-test PPPoE suite
│   ├── radius/                       # FreeRADIUS test config
│   └── run-all-tests.sh
└── scripts/
    ├── build/build-accel-ppp.sh       # Source build script
    └── deploy/install-vm3-cpe.sh     # CPE client provisioning
```

---

## ✅ What Works (Phase 0+1)

### Deep Integration (Phase 0)
- **UCI Configuration** — All accel-ppp settings managed via `uci set rnas.xxx.yyy`, not hand-edited config files
- **procd Init** — `service accel-ppp start/stop/reload`, with SIGHUP hot-reload
- **OpenWrt Package** — Standard `package/accel-ppp/Makefile` for `make package/accel-ppp/compile`
- **UCI Translator** — `accel-ppp-uci generate` auto-generates native accel-ppp.conf from UCI
- **First-boot Ready** — `uci-defaults/rnas` pre-configures PPPoE + RADIUS on factory reset

### RADIUS Tools (Phase 1)
- **CoA Test** (`tools/coa-test.sh`) — 6 sub-commands: disconnect, bandwidth, timeout, data-limit, test, show
- **Accounting Verify** (`tools/acct-verify.sh`) — RFC 2866/2867 compliance checker
- **RADIUS Capture** (`tools/radius-capture.sh`) — Live capture on ports 1812/1813/3799
- **PPPoE Test Suite** (`tests/pppoe/test-pppoe.sh`) — 10 real tests with tcpdump verification
- **VM3 CPE Deploy** (`scripts/deploy/install-vm3-cpe.sh`) — Ubuntu provisioning as PPPoE/L2TP client
- **FreeRADIUS Test Config** (`tests/radius/`) — Pre-configured test users + virtual server

### LuCI Web Interface (Phase 3 — partial)
- **7-page skeleton** — Overview, RADIUS Settings, Protocol Config, IP Pool, Sessions, CoA Control, Status
- **Controller logic** — Session terminate + CoA disconnect actions wired
- **Status API** — Returns uptime, session count, protocol state

---

## 🔧 Quick Start

### Build from Source

```bash
git clone https://github.com/Lancer2049/RNAS.git
cd RNAS

# Build accel-ppp from source (standalone, no SDK needed)
./scripts/build/build-accel-ppp.sh

# Build as OpenWrt package (requires OpenWrt SDK)
./scripts/build/build-accel-ppp.sh --sdk /path/to/openwrt-sdk
```

### Test on Existing Linux

```bash
# Install accel-ppp (Ubuntu/Debian)
sudo apt install accel-ppp

# Or use our build output
cp build/accel-ppp/install/usr/sbin/accel-pppd /usr/local/sbin/
cp build/accel-ppp/install/usr/sbin/accel-cmd  /usr/local/sbin/

# Run with test config
accel-pppd -c configs/pppoe.conf -d
```

### Run Tests

```bash
# Full PPPoE test suite
./tests/pppoe/test-pppoe.sh all

# CoA disconnect test
./tools/coa-test.sh disconnect -s 192.168.0.85 -r testing123 -u testuser

# Accounting compliance check
./tools/acct-verify.sh verify
```

---

## 🚧 In Progress / Planned

| Feature | Status | Priority |
|---------|--------|----------|
| Bootable OpenWrt image with accel-ppp baked in | Not started | 🔴 P0 |
| LuCI: live session list from accel-cmd output | Not started | 🔴 P0 |
| LuCI: real CoA/logs/metrics wiring | Not started | 🔴 P0 |
| IPoE protocol testing | Config only | 🟡 P1 |
| L2TP protocol testing | Config only | 🟡 P1 |
| Multi-protocol QoS | Removed (not in scope) | ⬜ |
| WiFi AC emulation | Planned | 🟢 P2 |

---

## 🌐 Three-Node Test Architecture

```
VM1: RNAS              192.168.0.x      OpenWrt + accel-ppp (PPPoE Server + RADIUS Client)
VM2: FreeRADIUS+AIRadius 192.168.0.85    RADIUS Server + Web Management
VM3: CPE Client         192.168.0.82    Ubuntu (PPPoE/L2TP client + testing)
```

See `tests/radius/README.md` for FreeRADIUS test configuration.

---

## 📄 License

GPL-2.0 — see [LICENSE](LICENSE)

---

## 🙏 Built On

- [accel-ppp](https://github.com/accel-ppp/accel-ppp) — High-performance VPN server
- [OpenWrt](https://openwrt.org/) — Embedded Linux distribution
- [FreeRADIUS](https://freeradius.org/) — RADIUS server
- [AIRadius](https://github.com/Lancer2049/AIRadius) — Web management UI (sibling project)
