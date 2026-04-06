# RNAS-OpenWrt Configuration Files

This directory contains configuration templates for accel-ppp and RADIUS integration.

## Directory Structure

```
configs/
├── accel-ppp/           # accel-ppp daemon configurations
│   ├── accel-ppp.conf  # Main configuration
│   ├── ip-pool.conf    # IP address pools
│   ├── chap-secrets    # Local authentication (fallback)
│   └── modules.conf    # Protocol modules
├── templates/           # Configuration templates for different scenarios
│   ├── pppoe-basic.conf
│   ├── pppoe-full.conf
│   ├── ipoe-basic.conf
│   ├── l2tp-basic.conf
│   └── coa-template.conf
└── radius/              # RADIUS client configurations
    ├── clients.conf     # RADIUS client definitions
    └── dictionary       # RADIUS attribute dictionary
```

## Usage

Copy templates to your OpenWrt device:

```bash
# Main config
scp configs/accel-ppp/accel-ppp.conf root@192.168.1.1:/etc/accel-ppp.conf

# RADIUS config
scp configs/radius/clients.conf root@192.168.1.1:/etc/accel-ppp/radius.conf
```

Or use the deployment script:

```bash
./scripts/deploy/deploy-configs.sh -h 192.168.1.1 -u root -s
```
