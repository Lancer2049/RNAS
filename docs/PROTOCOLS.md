# Protocol Support Status

## Overview

| Protocol | Code | Status | Notes |
|----------|------|--------|-------|
| PPPoE | `pppoe` | ✅ Complete | Tested |
| IPoE | `ipoe` | ✅ Complete | Config ready |
| L2TP | `l2tp` | ✅ Complete | Config ready |
| PPTP | `pptp` | ✅ Complete | Config ready |
| SSTP | `sstp` | ✅ Complete | Config ready |

## PPPoE - Point-to-Point Protocol over Ethernet

### Description
PPPoE is the most common protocol for DSL and fiber-to-home ISP networks. It provides PPP encapsulation over Ethernet.

### Configuration
```bash
[ppp]
min-mtu=1280
mtu=1492
mru=1492

[pppoe]
verbose=1
accept-any=1
if=br-lan
```

### Port
- Standard Ethernet (Layer 2)
- No specific port required

### Test Command
```bash
pppoe-test.sh auth testuser test123
```

---

## IPoE - IP over Ethernet (DHCP+)

### Description
IPoE uses DHCP for session establishment, commonly used for IPTV and shared media networks.

### Configuration
```bash
[ipoe]
verbose=1
mode=l2
interface=br-lan
username=format=mac
```

### Port
- Standard Ethernet (Layer 2)
- DHCP ports 67/68

### Test Command
```bash
# Requires DHCP client configuration
```

---

## L2TP - Layer 2 Tunneling Protocol

### Description
L2TP creates L2 tunnels over IP. Often combined with IPSec for encryption.

### Configuration
```bash
[l2tp]
verbose=1
bind=0.0.0.0
port=1701
```

### Ports
- UDP 1701 (L2TP control)
- ESP (Protocol 50) when combined with IPSec

### Test Command
```bash
# Requires L2TP client (e.g., xl2tpd)
```

---

## PPTP - Point-to-Point Tunneling Protocol

### Description
Legacy VPN protocol with MPPE encryption. Less secure but widely supported.

### Configuration
```bash
[pptp]
verbose=1
bind=0.0.0.0
port=1723
```

### Ports
- TCP 1723 (control)
- GRE (Protocol 47) - data

### Test Command
```bash
# Requires PPTP client
```

---

## SSTP - Secure Socket Tunneling Protocol

### Description
Modern VPN protocol using HTTPS (TCP 443). Firewall-friendly and highly secure.

### Configuration
```bash
[sstp]
verbose=1
bind=0.0.0.0
port=443
# cert-file=/etc/ssl/certs/server.pem
# key-file=/etc/ssl/private/server-key.pem
```

### Ports
- TCP 443 (HTTPS)

### Test Command
```bash
# Requires SSTP client (Windows built-in, or sstpc)
```

---

## RADIUS Integration

All protocols support full RADIUS integration:

### Authentication
- PAP, CHAP, MS-CHAPv2
- EAP-MD5, EAP-TLS

### Accounting
- Start, Interim-Update, Stop packets

### CoA Support
| Operation | Support |
|-----------|---------|
| Session Disconnect | ✅ |
| Bandwidth Modify | ✅ |
| Session Timeout | ✅ |
| Data Limit | ✅ |

---

## Testing Matrix

| Protocol | Auth | Acct | CoA | Load Test |
|----------|------|------|-----|-----------|
| PPPoE | ✅ | ✅ | ✅ | ⏳ |
| IPoE | ⏳ | ⏳ | ⏳ | ⏳ |
| L2TP | ⏳ | ⏳ | ⏳ | ⏳ |
| PPTP | ⏳ | ⏳ | ⏳ | ⏳ |
| SSTP | ⏳ | ⏳ | ⏳ | ⏳ |

Legend: ✅ Tested | ⏳ Pending

---

## TODO

- [ ] IPoE testing with DHCP client
- [ ] L2TP site-to-site test
- [ ] L2TP with IPSec test
- [ ] PPTP compatibility test
- [ ] SSTP certificate setup
- [ ] Load testing (100+ concurrent sessions)
- [ ] Performance benchmarking
