# RNAS Configuration Files

This directory contains configuration templates for accel-ppp and RADIUS integration.

## Directory Structure

```
configs/
├── pppoe.conf           # PPPoE server configuration
├── ipoe.conf            # IPoE (DHCP+) server configuration
├── l2tp.conf            # L2TP server configuration
├── pptp.conf            # PPTP server configuration
└── sstp.conf            # SSTP server configuration
```

## Protocol Support

| Protocol | Port | Encryption | RADIUS Support |
|----------|------|-----------|---------------|
| PPPoE | Ethernet | PAP/CHAP/MPPE | Full |
| IPoE | Ethernet | DHCP+ | Full |
| L2TP | UDP 1701 | IPSec | Full |
| PPTP | TCP 1723 | MPPE | Full |
| SSTP | TCP 443 | HTTPS/TLS | Full |

## Usage

Copy the appropriate configuration to your OpenWrt device:

```bash
# PPPoE configuration
scp configs/pppoe.conf root@192.168.1.1:/etc/accel-ppp.conf

# IPoE configuration
scp configs/ipoe.conf root@192.168.1.1:/etc/accel-ppp.conf

# L2TP configuration
scp configs/l2tp.conf root@192.168.1.1:/etc/accel-ppp.conf

# PPTP configuration
scp configs/pptp.conf root@192.168.1.1:/etc/accel-ppp.conf

# SSTP configuration
scp configs/sstp.conf root@192.168.1.1:/etc/accel-ppp.conf
```

Then restart accel-ppp:

```bash
ssh root@192.168.1.1 "/etc/init.d/accel-ppp restart"
```

## Configuration Variables

The following variables can be customized in each configuration file:

- `RADIUS_SERVER` - RADIUS server IP address
- `RADIUS_SECRET` - Shared secret for RADIUS communication
- `NAS_IP` - IP address of this NAS device
- `RADIUS_AUTH_PORT` - Authentication port (default: 1812)
- `RADIUS_ACCT_PORT` - Accounting port (default: 1813)
- `RADIUS_COA_PORT` - CoA port (default: 3799)
