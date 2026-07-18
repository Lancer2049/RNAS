# RNAS Configuration Templates

This directory contains the unified `/etc/rnas/` INI-style configuration tree consumed by `rnas-config` (Python config engine).

## Directory Structure

```
configs/
├── rnas.conf                # Global RNAS settings
├── access.d/                # Access protocol configs
│   ├── core.conf
│   ├── common.conf
│   ├── ppp.conf
│   ├── pppoe.conf
│   ├── ipoe.conf
│   ├── l2tp.conf
│   ├── pptp.conf
│   ├── sstp.conf
│   ├── radius.conf
│   ├── mac-auth.conf
│   └── client-range.conf
├── network.d/               # Network stack configs
│   ├── interface-lan.conf
│   ├── dhcp.conf
│   ├── firewall.conf
│   ├── vlan.conf
│   ├── ipv6.conf
│   ├── relay.conf
│   └── rules/               # nftables rules
├── vpn.d/                   # VPN service configs
│   ├── ipsec.conf
│   ├── wireguard.conf
│   ├── openvpn.conf
│   ├── gre.conf
│   ├── ipip.conf
│   ├── eoip.conf
│   └── vxlan.conf
├── wireless.d/              # Wireless / 802.1X
│   └── dot1x.conf
├── dictionary/              # RADIUS vendor dictionaries (13 vendors, 474 attrs)
├── scenarios/               # Deployment scenario overrides
├── qos.conf                 # QoS / traffic shaping
├── monitor.conf             # SNMP / monitoring
├── hotspot.conf             # Hotspot portal
└── ha.conf                  # High Availability (VRRP)
```

## Usage

All configs are INI format with `${VAR:-default}` env var interpolation:

```ini
[section "instance"]
key = value
another_key = ${RNAS_RADIUS_SECRET:-testing123}
```

### Validate
```bash
python3 cmd/rnas-config/rnas_config.py validate --root configs/
```

### Generate service config
```bash
python3 cmd/rnas-config/rnas_config.py generate accel-ppp --root configs/
python3 cmd/rnas-config/rnas_config.py generate dnsmasq --root configs/
python3 cmd/rnas-config/rnas_config.py generate firewall --root configs/
```

### Show parsed tree
```bash
python3 cmd/rnas-config/rnas_config.py show --root configs/
```

## Environment Variables

| Variable | Default | Used By |
|----------|---------|---------|
| `RNAS_RADIUS_SECRET` | `testing123` | RADIUS auth, DAE, hotspot |
| `RNAS_RADIUS_SERVER` | `192.168.0.202` | RADIUS server |
| `RNAS_ACCEL_CMD` | `accel-cmd` | Dashboard WebSocket |
| `RNAS_VM3_HOST` | `192.168.0.203` | Deploy script |
| `RNAS_VM3_PASS` | `123456` | Deploy script (set to avoid warning) |
