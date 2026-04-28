# RNAS Development State

**Session Date**: 2026-04-28
**Status**: ✅ Role swap complete — RNAS on Ubuntu, CPE on UOS, full AAA+CoA verified

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
