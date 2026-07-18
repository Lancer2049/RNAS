# RNAS Full-Platform Architecture Design (Revised)

**Date**: 2026-04-26
**Status**: Approved — Fusion Model
**Target**: RNAS v2.0 — Integrated NAS simulation platform on x86 Linux

---

## 0. Architecture Philosophy: Fusion, Not Aggregation

RNAS does **NOT** build on top of OpenWrt as a base OS. Instead, it is a
**standalone NAS platform for x86 Linux/VM**, deeply integrating:

- **accel-ppp** (access server core)
- **OpenWrt design patterns** (UCI config model, LuCI web UI paradigm, service orchestration)
- **Standard Linux networking** (netfilter, tc, dnsmasq, strongSwan, keepalived)

The integration is at the **configuration and management layer**, not at the
OS/firmware layer. Users install RNAS on their existing Linux or VM, not flash
a new firmware.

```
┌──────────────────────────────────────────────────────────────┐
│                 RNAS Unified Web Console                     │
│     (LuCI-inspired, fully integrated single application)     │
├──────────────────────────────────────────────────────────────┤
│                  RNAS Configuration Engine                   │
│   /etc/rnas/*.conf  ←  UCI-format, unified schema          │
├──────────┬──────────┬──────────┬──────────┬─────────────────┤
│ accel-ppp│ dnsmasq  │ strongSwan│tc/SQM   │ keepalived/VRRP │
│(PPPoE/   │(DHCP/DNS)│ WireGuard│(CAKE/   │ CoovaChilli     │
│ L2TP/    │ nftables │ OpenVPN  │ fq_codel)│ snmpd/netflow   │
│ IPoE)    │(firewall)│          │          │                 │
├──────────┴──────────┴──────────┴──────────┴─────────────────┤
│                Standard x86 Linux Kernel                    │
│        (Debian/Ubuntu/UOS — no OpenWrt firmware needed)      │
└──────────────────────────────────────────────────────────────┘
```

### Key Design Rules

1. **One config tree**: `/etc/rnas/` contains all configuration. No scattered OpenWrt UCI files.
2. **One web console**: A single web app manages everything. Not separate LuCI modules.
3. **Systemd native**: Services use systemd units, not procd scripts.
4. **Installable, not flashable**: `apt install rnas` or a bootstrap script. No firmware build needed.
5. **OpenWrt-inspired, not OpenWrt-dependent**: UCI format, LuCI MVC pattern, service abstraction — but running on standard Linux.

---

## 1. Unified Configuration Tree: `/etc/rnas/`

All services share a single configuration namespace. No separate UCI files per service.

### Schema

```
/etc/rnas/
├── rnas.conf              # Global settings
├── access.d/              # Access server configs
│   ├── core.conf          # accel-ppp core: threads, logging, modules
│   ├── radius.conf        # RADIUS server/auth/acct/CoA
│   ├── ppp.conf           # PPP global parameters (MTU, LCP, auth)
│   ├── pppoe.conf         # PPPoE: interface, AC-name, service-name
│   ├── ipoe.conf          # IPoE: interface, DHCP relay
│   ├── l2tp.conf          # L2TP: interface, port
│   ├── pptp.conf          # PPTP: interface
│   ├── sstp.conf          # SSTP: interface, port, SSL
│   ├── ip-pool.conf       # IP address pools
│   └── coa.conf           # CoA/Disconnect settings
├── network.d/             # L3 network configs
│   ├── interfaces.conf    # VLANs, bridges, IP assignments
│   ├── dhcp.conf          # DHCP server/relay scopes
│   └── firewall.conf      # nftables zone rules
├── qos.conf               # Traffic control: per-user, per-class
├── vpn.d/                 # VPN terminations
│   ├── ipsec.conf         # strongSwan IPsec/IKEv2
│   ├── wireguard.conf     # WireGuard peers
│   └── openvpn.conf       # OpenVPN server
├── hotspot.conf           # CoovaChilli captive portal
├── monitor.conf           # SNMP, NetFlow, syslog
├── ha.conf                # VRRP keepalived
└── users.conf             # Local user database (fallback when RADIUS unavailable)
```

### Format

UCI-style key=value with sections, parsable by a unified config reader:

```ini
# /etc/rnas/access.d/radius.conf
[server "primary"]
auth_host = 192.168.0.85
auth_port = 1812
acct_host = 192.168.0.85
acct_port = 1813
secret = ${RNAS_RADIUS_SECRET}
timeout = 30
retries = 3
interim_interval = 300
nas_identifier = rnas

[coa]
enabled = yes
port = 3799
allowed_clients = 192.168.0.85
```

```ini
# /etc/rnas/qos.conf
[global]
enabled = yes
algorithm = cake
interface = ens33

[default]
rate = 100mbit
ceil = 200mbit

[per_user]
enabled = yes
default_rate = 10mbit
radius_attr = WISPr-Bandwidth-Max-Up
```

```ini
# /etc/rnas/vpn.d/ipsec.conf
[global]
enabled = yes
auth = radius

[tunnel "site-a"]
remote = 10.0.0.1
local_subnet = 192.168.100.0/24
remote_subnet = 10.1.0.0/24
```

---

## 2. Configuration Engine: `rnas-config`

A unified binary/script that:

1. **Reads** `/etc/rnas/` tree
2. **Validates** cross-service constraints (e.g., DHCP range must not overlap IP pool)
3. **Generates** native configs for each service:
   - `rnas-config generate accel-ppp` → `/var/run/rnas/accel-ppp.conf`
   - `rnas-config generate dnsmasq` → `/var/run/rnas/dnsmasq.conf`
   - `rnas-config generate strongswan` → `/var/run/rnas/ipsec.conf`
   - `rnas-config generate tc` → applies tc rules directly
4. **Reloads** affected services via systemd:
   - `rnas-config apply` → regenerates + reloads changed services

This replaces the scattered `accel-ppp-uci` translator with a single config engine.

---

## 3. Service Management: systemd

Every service gets a systemd unit:

```
rnas.target                 # Master target, pulls in enabled services
├── rnas-accel-ppp.service  # accel-ppp daemon
├── rnas-dnsmasq.service    # DHCP/DNS
├── rnas-firewall.service   # nftables rules
├── rnas-qos.service        # tc rules
├── rnas-ipsec.service      # strongSwan
├── rnas-wireguard.service  # WireGuard
├── rnas-openvpn.service    # OpenVPN
├── rnas-chilli.service     # CoovaChilli
├── rnas-snmpd.service      # SNMP agent
├── rnas-netflow.service    # NetFlow export
├── rnas-keepalived.service # VRRP
└── rnas-web.service        # Web management panel
```

Start/stop everything: `systemctl start rnas.target`
Start only access: `systemctl start rnas-accel-ppp`

---

## 4. Web Console Architecture

### Backend: `rnas-api` (Python/FastAPI or Go)

Reads config and runtime state, exposes unified REST API:

```
GET  /api/v1/status                    # Overall health
GET  /api/v1/sessions                  # Live sessions from accel-cmd
POST /api/v1/sessions/{id}/disconnect  # CoA Disconnect
GET  /api/v1/qos/classes               # Active QoS classes
GET  /api/v1/vpn/tunnels               # Active VPN tunnels
GET  /api/v1/monitor/traffic           # Interface traffic stats
GET  /api/v1/config/{module}           # Read current config
PUT  /api/v1/config/{module}           # Update config
POST /api/v1/config/apply              # Apply config changes
```

### Frontend: Single-Page App (Vue.js or LuCI-adapted)

Single web app, not scattered LuCI modules:

```
Dashboard
├── Overview: session count, throughput, CPU, mem, active services
├── Sessions: live table, search, batch disconnect
└── Traffic: real-time graphs (per-interface, per-user)

Configuration
├── Access: RADIUS, PPPoE/IPoE/L2TP/PPTP/SSTP, IP pools
├── Network: interfaces, VLANs, bridges, DHCP, firewall
└── Services: QoS, VPN, hotspot, HA

Tools
├── Diagnostics: ping, traceroute, tcpdump, radius-capture
├── Logs: filtered syslog viewer
└── Backup: export/import /etc/rnas/ tree
```

---

## 5. Deployment Models

### Model A: Package Install (primary)

```bash
# Add RNAS repository
curl -fsSL https://repo.rnas.dev/setup.sh | bash

# Install
apt install rnas-core          # accel-ppp + config engine + web
apt install rnas-network       # dnsmasq + nftables presets
apt install rnas-qos           # tc/SQM
apt install rnas-vpn           # strongSwan + WireGuard + OpenVPN
apt install rnas-full          # everything
```

### Model B: Bootstrap Script (VM template)

```bash
curl -fsSL https://get.rnas.dev | bash
# → installs dependencies, downloads binaries, configures defaults
```

### Model C: Docker

```bash
docker run -d --network host --name rnas \
  -v /etc/rnas:/etc/rnas \
  ghcr.io/lancer2049/rnas:latest
```

### Model D: OpenWrt Package (for actual OpenWrt deployments)

```bash
# Inside OpenWrt build system
make package/rnas-core/compile
# → opkg installs on OpenWrt with UCI + LuCI
```

This model still exists for users who DO want to deploy on OpenWrt hardware,
but it's now a secondary target, not the primary one.

---

## 6. Filesystem Layout

```
rnas/
├── cmd/
│   └── rnas-config/              # Unified config engine (Go/C)
│       ├── main.go               # CLI: generate, apply, validate
│       ├── reader/               # /etc/rnas/ parser
│       ├── generator/            # Native config generators
│       │   ├── accel_ppp.go
│       │   ├── dnsmasq.go
│       │   ├── strongswan.go
│       │   ├── tc_qos.go
│       │   └── ...
│       └── applier/              # systemd reload orchestrator
├── web/
│   ├── api/                      # rnas-api (FastAPI or Go)
│   │   ├── routes/
│   │   │   ├── status.py
│   │   │   ├── config.py
│   │   │   ├── sessions.py
│   │   │   └── ...
│   │   └── services/
│   │       ├── accel_cmd.py      # accel-cmd wrapper
│   │       ├── config_engine.py  # reads/writes /etc/rnas/
│   │       └── ...
│   └── frontend/                 # SPA (Vue.js)
│       ├── src/
│       │   ├── views/
│       │   │   ├── Dashboard.vue
│       │   │   ├── Sessions.vue
│       │   │   ├── Config.vue
│       │   │   └── ...
│       │   └── api/              # REST client
│       └── dist/                 # Built static assets
├── configs/
│   ├── rnas.conf                 # Default global config
│   ├── access.d/                 # Default access configs
│   │   ├── core.conf
│   │   ├── radius.conf
│   │   ├── pppoe.conf
│   │   └── ...
│   ├── network.d/
│   │   ├── interfaces.conf
│   │   ├── dhcp.conf
│   │   └── firewall.conf
│   └── ...
├── systemd/                      # systemd unit files
│   ├── rnas.target
│   ├── rnas-accel-ppp.service
│   ├── rnas-dnsmasq.service
│   ├── rnas-firewall.service
│   └── ...
├── tools/                        # CLI tools (current)
├── tests/                        # Test suites
├── docker/                       # Docker test environments
├── scripts/
│   ├── install.sh                # One-shot installer
│   └── build.sh                  # Build from source
└── docs/
    └── plans/
        └── 2026-04-26-rnas-full-platform-design.md  # ← this file
```

---

## 7. Phase Plan (Revised)

### Phase 1 — Core Platform (3 weeks)
| # | Task | Output |
|---|------|--------|
| 1.1 | Design `/etc/rnas/` schema | All `.conf` templates in `configs/` |
| 1.2 | Build `rnas-config` engine | `cmd/rnas-config/` — reader, generator, applier |
| 1.3 | systemd units for access + network | `systemd/rnas-*.service` |
| 1.4 | `rnas-api` backend scaffold | `web/api/` — status, sessions, config CRUD |
| 1.5 | Dashboard SPA (MVP) | `web/frontend/` — overview + sessions |
| 1.6 | `install.sh` bootstrap script | One-command install on Debian/Ubuntu/UOS |

### Phase 2 — Network + Monitoring (2 weeks)
| # | Task | Output |
|---|------|--------|
| 2.1 | dnsmasq integration (DHCP/DNS) | generator + systemd unit |
| 2.2 | nftables firewall integration | generator + systemd unit |
| 2.3 | SNMP + NetFlow + syslog | `rnas-mon` presets + API endpoints |
| 2.4 | Traffic dashboard (live graphs) | Frontend: real-time charts |

### Phase 3 — QoS + VPN (3 weeks)
| # | Task | Output |
|---|------|--------|
| 3.1 | tc/SQM integration | `rnas-config generate tc` + systemd |
| 3.2 | strongSwan IPsec integration | generator + systemd |
| 3.3 | WireGuard integration | generator + systemd |
| 3.4 | OpenVPN integration | generator + systemd |
| 3.5 | QoS + VPN web config pages | Frontend |

### Phase 4 — Hotspot + HA + Polish (2 weeks)
| # | Task | Output |
|---|------|--------|
| 4.1 | CoovaChilli integration | generator + systemd + web |
| 4.2 | keepalived VRRP integration | generator + systemd + web |
| 4.3 | Docker all-in-one test env | `docker-compose.yml` with all services |
| 4.4 | Debian packaging (`apt install rnas`) | `debian/` control files |
