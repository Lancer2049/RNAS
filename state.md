# RNAS Development State

**Session Date**: 2026-04-26
**Status**: ✅ AAA + CoA verified, LuCI live-data wired, RNAS config on VM1

## Current Goal
Build RNAS as a standalone OpenWrt-based software NAS — deep accel-ppp integration with UCI/procd/LuCI.

### LuCI Live Data Wiring (commit 2fa31c7)
- `controller/rnas.lua` — rewritten session + service data parsing
  - `parse_sessions()` — structured parser for `accel-cmd show sessions` with explicit columns
  - `parse_service_stat()` — parses `accel-cmd show stat` for uptime/cpu/mem/RADIUS state
  - `get_status_data()` — returns JSON with sessions[] + service{} + system{}
  - `action_terminate_session()` — uses `accel-cmd terminate sid <id> hard`
- `status_overview.htm` — UCI fields match RNAS schema (global.enabled, radius.auth_server, coa.enabled)
  - Added: NAS Identifier, Active Protocols, Service Uptime, CoA status
- `sessions_table.htm` — added `format_bytes()` helper, nil-safe field access
- `status_connections.htm` — uses explicit accel-cmd columns (sid,ifname,username,ip,type,state,uptime-raw,rx-bytes-raw,tx-bytes-raw)

## What We Did Today

### Deployment
- ✅ Deployed RNAS config to VM1 (UOS Desktop + standalone accel-ppp)
  - `nas-identifier=rnas` (was `accel-ppp-vm1`)
  - `nas-ip-address=192.168.0.84` ✅ (was commented out)
  - `dae-server=192.168.0.84:3799,testing123` — CoA port active
  - `dae-allowed=192.168.0.85` — FreeRADIUS authorized
  - Backup: `/etc/accel-ppp.conf.rnas-backup`

### Three-Node AAA Verified ✅
```
VM3 (pppoe client)  ──PPPoE──►  VM1 (accel-ppp)  ──RADIUS──►  VM2 (FreeRADIUS)
192.168.0.82                        192.168.0.84                  192.168.0.85
                                     ──CoA/DM◄──                  (3799)
```
- PPPoE discovery: VM3 finds AC "accel-ppp" on ens33 ✅
- RADIUS auth: Access-Request → Access-Accept for testuser ✅
- RADIUS acct: Accounting-Start → radacct record ✅
- IP pool: 192.168.100.10 assigned from 192.168.100.10-100 ✅

### CoA Disconnect Verified ✅
- Direct radclient test: Disconnect-Request → Disconnect-ACK ✅
- accel-ppp sends Accounting-Stop with `Acct-Terminate-Cause=Admin-Reset` ✅
- PPPoE session on VM3 actually torn down ✅

### Config Fixes
- `.gitignore`: added `.git/` and `*.local` rules (commit 5b9e913)

## Known Issue — DAE / nas-ip-address
When deploying with `nas-ip-address=192.168.0.84` + `nas-identifier=rnas`, the first
accel-ppp restart had DAE (port 3799) fail to bind. Root cause: multiple accel-ppp
instances from failed restarts. Clean kill+single start resolves it.

Current running: `accel-pppd -c /etc/accel-ppp.conf` with RNAS config ✅

## Active Architecture
```
VM1: RNAS (UOS Desktop + accel-ppp) → 192.168.0.84, ACCEL-PPP RUNNING ✅ (PID 1566)
VM2: FreeRADIUS + AIRadius → 192.168.0.85, services running ✅
VM3: CPE Client → 192.168.0.82 (Ubuntu, PPPoE client installed, ppp0 DHCP)
```

## Current Config Snapshot (VM1)
```
nas-identifier=rnas
nas-ip-address=192.168.0.84
server=192.168.0.85,testing123,auth-port=1812,acct-port=1813,...
dae-server=192.168.0.84:3799,testing123
dae-allowed=192.168.0.85
pppoe interface=ens33
ip-pool: 192.168.100.10-100
```

## Next Steps (priority order)
1. Reboot VM1 to clear kernel state (multiple accel-ppp segfaults from testing)
   → PPPoE will stabilize after reboot
2. Build bootable OpenWrt image with accel-ppp baked in (needs SDK)
3. Deploy UCI + LuCI on actual OpenWrt — only then can web UI be tested live

## Open Issues
- VM1 runs UOS Desktop (NOT OpenWrt) — no UCI available
- Multiple accel-ppp segfaults during testing may have corrupted kernel state
  → Recommend `reboot` on VM1 before next test session
- protocol.lua: `rnas.pppoe.enabled` mismatch with `rnas.pppoe.interface`
- GitHub push sometimes times out in WSL (workaround: unset credential.helper)
