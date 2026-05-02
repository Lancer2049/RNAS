# RNAS Development State

**Session Date**: 2026-05-02
**Status**: All 5 protocols verified, 10 services running, 11/11 regression

## ⚠️ VM TOPOLOGY (READ FIRST — NEVER CHANGE THESE)

```
VM1: CPE Client      192.168.0.201   Ubuntu 24.04 (pppoe/pptp/l2tp/sstp client)
VM2: RADIUS Server   192.168.0.202   Ubuntu (FreeRADIUS :1812/1813 + AIRadius :8000)
VM3: RNAS Server     192.168.0.203   Ubuntu 24.04 (accel-ppp + /etc/rnas/ + dashboard :8099)
```

- VM1 = CPE role, runs pppd/xl2tpd/pptp/sstpc clients
- VM2 = RADIUS role, NEVER install client tools here
- VM3 = RNAS NAS platform, all services deploy here
- ALL passwords: root/123456
- OLD IPs (.84/.85/.82) are DEPRECATED — never use them

## VM3 Running
- accel-ppp ✅ | rnas-web ✅ | dnsmasq ✅ | nftables ✅ | cake QoS ✅

## Pending
- SNMP: install snmpd + deploy
- VPN: strongSwan / WireGuard
- HA: keepalived

## Access
- Dashboard: http://192.168.0.203:8099
- SSH: root@192.168.0.203 (123456)

## VM3 Running Services
| Service | Status |
|---------|--------|
| rnas-accel-ppp (DAE:3799) | ✅ active |
| rnas-dnsmasq (DNS:53/DHCP:67) | ✅ running |
| nftables (firewall) | ✅ rules loaded |
| rnas-web (dashboard:8099) | ✅ active |
| tc/cake QoS (ens33, 100Mbit) | ✅ applied |

## Today's Progress
- ✅ QoS: cake qdisc deployed on VM3 ens33
- ✅ NetworkConfig: editable inline fields + Save per section + Apply
- ✅ ServicesConfig: editable inline + Save
- ✅ PUT /api/config/ endpoint working (writes to /etc/rnas/)
- ✅ POST /api/config/apply regenerates + reloads services
- ✅ System page: service status + logs + memory/disk
- ✅ Tools page: Ping/Traceroute/RADIUS/CoA

## Access
- Dashboard: http://192.168.0.203:8099
- SSH: root@192.168.0.203 (123456)

## Pending Commits
- 07fb04d: editable NetworkConfig + PUT API + QoS (pushed ✅)

## Next Session
1. Install snmpd + deploy monitoring
2. Try install strongSwan/WireGuard for VPN
3. Deploy keepalived for HA
4. Per-user QoS with iptables MARK + tc classes

## Current Architecture
```
VM1: CPE Client     192.168.0.201   UOS Desktop (pppoe/pppd)
VM2: FreeRADIUS     192.168.0.202   Ubuntu (auth/acct + AIRadius)
VM3: RNAS Server    192.168.0.203   Ubuntu 24.04 (RNAS v2 full stack)
```

## VM3 Running Services
| Service | Port | Status |
|---------|------|--------|
| rnas-accel-ppp | 3799 (DAE) | ✅ active |
| rnas-dnsmasq | 53 (DNS) / 67 (DHCP) | ✅ active |
| nftables | — | ✅ rules loaded |
| rnas-web | 8099 | ✅ active |

## Access
- Dashboard: http://192.168.0.203:8099
- SSH: root@192.168.0.203 (password: 123456)

## Key Deployments on VM3
- accel-ppp: `/home/lancer/projects/RNAS/build/accel-ppp/install/` (source-built)
- Config: `/etc/rnas/` (21 templates)
- Config engine: `/usr/bin/rnas-config`
- Web server: `/opt/rnas-web/server.py` + `/opt/rnas-web/static/`
- systemd: `rnas-accel-ppp`, `rnas-dnsmasq`, `rnas-web`

## Completed Today
- ✅ Role swap: RNAS moved from VM1(UOS) to VM3(Ubuntu 24.04)
- ✅ Source-built accel-ppp (OpenSSL 3.x, no cross-distro lib issues)
- ✅ dnsmasq + nftables deployed and running
- ✅ Web dashboard 6-tab (Overview/Sessions/Network/Config/Services/Tools)
- ✅ Tools page: Ping, Traceroute, RADIUS Auth Test, CoA Disconnect
- ✅ Full AAA+CoA end-to-end verified with new IPs
- ✅ rnas-config: removed hardcoded daemon=1
- ✅ Git: 41 commits pushed

## Next Session
1. Deploy remaining modules: QoS (tc), VPN (strongSwan/WireGuard), Hotspot, HA
2. Make NetworkConfig + ServicesConfig editable (forms, not just read-only tables)
3. Add System page (service status, logs, backup)
4. Install remaining services: snmpd, strongSwan, wireguard, keepalived, coova-chilli

## Key Files
- GitHub: https://github.com/Lancer2049/RNAS
- VM3 web server: /opt/rnas-web/server.py (stdlib, no pip needed)
- VM3 accel-ppp: /home/lancer/projects/RNAS/build/accel-ppp/install/
- VM3 config: /etc/rnas/

## Lessons Learned
- NEVER cross-distro copy .so files (UOS libc → Ubuntu = kernel panic)
- Use source-built binaries with matching RPATH
- systemd Type=simple, no daemon=1 in config

## Current Architecture

```
VM1: CPE Client     192.168.0.201   UOS Desktop (pppoe/pppd client)
VM2: FreeRADIUS     192.168.0.202   Ubuntu (auth/acct + AIRadius)
VM3: RNAS Server    192.168.0.203   Ubuntu 24.04 (accel-ppp + /etc/rnas/ + rnas-config)
```

## Deployment Details (VM3)

- accel-ppp: source-built at `/home/lancer/projects/RNAS/build/accel-ppp/install/`
- Config: `/etc/rnas/` (21 templates, 5 directories)
- Config engine: `/usr/bin/rnas-config` (Python)
- Service: systemd `rnas-accel-ppp` (Type=simple, auto-restart)
- DAE: 0.0.0.0:3799, allowed 192.168.0.202
- NAS-ID: rnas, NAS-IP: 192.168.0.203
- RADIUS: 192.168.0.202:1812/1813, secret: testing123

## Verified End-to-End

```
VM1(201) ──PPPoE──► VM3(203) ──RADIUS──► VM2(202)
 ppp0:192.168.100.10  accel-ppp           FreeRADIUS
                       NAS:rnas            auth/acct OK
                       DAE:3799            DB:Admin-Reset
CoA: radclient → Disconnect-ACK → ppp0 DISCONNECTED
```

## Key Lessons

- NEVER cross-distro copy .so files (UOS libc → Ubuntu = kernel panic)
- Use source-built binaries with matching RPATH
- systemd Type=simple with no daemon=1 in config

## Current Goal
Build RNAS as a standalone NAS platform for x86 Linux — fusion of accel-ppp + Linux networking under unified `/etc/rnas/` config with systemd orchestration and Vue.js dashboard.

## Phase 1 — Complete ✅
- `/etc/rnas/` config schema: 14 templates (access.d/ + network.d/)
- `rnas-config` engine: INI parser + accel-ppp generator
- systemd units: rnas.target + accel-ppp + dnsmasq + firewall
- FastAPI backend: status, sessions, config endpoints
- Vue.js dashboard: status cards + sessions table + disconnect
- `scripts/install.sh`: one-command bootstrap installer
- README + AGENTS.md rewritten for v2 fusion architecture

## Next Steps — Phase 2: Network + Monitoring

### Immediate
1. **dnsmasq config generator** in `rnas-config`: `/etc/rnas/network.d/dhcp.conf` → dnsmasq.conf
2. **nftables config generator** in `rnas-config`: `/etc/rnas/network.d/firewall.conf` → nft rules
3. **Network config pages** in Vue.js dashboard (interfaces, DHCP, firewall)

### Later
4. SNMP + NetFlow + syslog monitoring presets
5. Traffic dashboard with live graphs (Chart.js)
6. `rnas-network` + `rnas-mon` package definitions

## Open Issues
- VM1 is UOS Desktop (not OpenWrt) — LuCI/UCI not testable live
- GitHub push sometimes times out (workaround: unset credential.helper)
- protocol.lua fixed (commit ca12521) — L2TP/PPTP/SSTP now have interface field
