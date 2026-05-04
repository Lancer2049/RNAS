# RNAS Development State

**Last Updated**: 2026-05-03
**Status**: v3 complete — 5 protocols + 10 services + 13 vendor dicts + 11/11 regression

## ⚠️ VM TOPOLOGY (READ FIRST — NEVER CHANGE THESE)

```
VM1: CPE Client      192.168.0.201   Ubuntu 24.04 (pppoe/pptp/l2tp/sstp client)
VM2: RADIUS Server   192.168.0.202   Ubuntu (FreeRADIUS :1812/1813 + AIRadius :8000 + DHCP :67)
VM3: RNAS Server     192.168.0.203   Ubuntu 24.04 (accel-ppp + /etc/rnas/ + dashboard :8099)
```

- VM1 = CPE role, runs pppd/xl2tpd/pptp/sstpc clients
- VM2 = RADIUS role + DHCP server, NEVER install client tools here
- VM3 = RNAS NAS platform, all services deploy here
- ALL passwords: root/123456
- OLD IPs (.84/.85/.82) are DEPRECATED — never use them

## VM3 Running Services (10/10)

| Service | Port | Enabled | Active |
|---------|------|---------|--------|
| rnas-accel-ppp | 3799(DAE)1723(PPTP)1701(L2TP)443(SSTP) | enabled | active |
| rnas-web | 8099 | enabled | active |
| rnas-qosd | — | enabled | active |
| dnsmasq | 53(DNS) | enabled | active |
| strongswan-starter | 500/4500(IPsec) | enabled | active |
| wg-quick@wg0 | 51820(WireGuard) | enabled | active |
| openvpn-server@server | 1194 | enabled | active |
| keepalived | VRRP | enabled | active |
| snmpd | 161 | enabled | active |
| rnas-dhcp-relay | 67 | disabled | inactive (opt-in) |

## Verified Protocols (5/5)

| Protocol | Auth | RADIUS | CoA | Notes |
|----------|------|--------|-----|-------|
| PPPoE | PAP ✅ | Start/Stop ✅ | Disconnect-ACK ✅ | multi-user |
| PPTP | PAP ✅ | Start/Stop ✅ | Disconnect-ACK ✅ | |
| L2TP | PAP ✅ | Start/Stop ✅ | Disconnect-ACK ✅ | auto-redial |
| SSTP | PAP+TLS ✅ | Start/Stop ✅ | via DAE | cert-persist |
| IPoE | RADIUS ✅ | Start/Stop ✅ | Disconnect-ACK ✅ | DORA + DHCP relay |

## RADIUS Dictionary

13 vendors, 474 attributes: Huawei, H3C, Cisco, ZTE, Juniper, Aruba, Ericsson, Arista, NVIDIA, Ruijie, MikroTik, Microsoft, WISPr

## Key Deployments on VM3

- accel-ppp: `/home/lancer/projects/RNAS/build/accel-ppp/install/` (source-built, v06f64b1)
- Config: `/etc/rnas/` (21+ templates, 12 generators)
- Web server: `/opt/rnas-web/server.py`
- QoS daemon: `/opt/rnas-qosd.py` (systemd: rnas-qosd)
- DHCP relay: `/opt/rnas-dhcp-relay.py` (systemd: rnas-dhcp-relay)

## Test Suite

```
tests/regression/rnas-full-test.sh  — 11/11 (PPPoE/PPTP/L2TP/SSTP/IPoE + Web + DB)
tests/stress/stress-pppoe.sh        — Concurrent PPPoE (4/5 pass on 5-user)
tests/stress/fault-injection.sh     — 5 fault scenarios
tests/compat/rnas-compat-test.py    — 13-vendor VSA compatibility
scripts/post-boot-verify.sh         — 17/18 boot checks
```

## Current Git

~21 commits since May 1, 127+ source files, main branch at `885e109`
