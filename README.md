# RNAS-OpenWrt

**OpenWrt-based RADIUS NAS (Network Access Server) with full RADIUS protocol support**

A production-ready OpenWrt distribution with accel-ppp, featuring complete RADIUS authentication, accounting, and dynamic authorization (CoA) capabilities.

## 🎯 Overview

RNAS-OpenWrt is a specialized OpenWrt build optimized for use as a RADIUS NAS (Network Access Server). It provides enterprise-grade authentication and session management for ISP and enterprise networks.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    RNAS-OpenWrt (NAS Device)                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   PPPoE     │  │   IPoE     │  │   L2TP      │        │
│  │   Server    │  │   (DHCP)   │  │   Server    │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                  │
│  ┌──────▼────────────────▼────────────────▼──────┐          │
│  │              accel-pppd (Unified Core)        │          │
│  │         High-performance VPN Gateway          │          │
│  └──────────────────────┬───────────────────────┘          │
│                         │                                    │
│  ┌──────────────────────▼───────────────────────┐          │
│  │            RADIUS Client Module              │          │
│  │  • Authentication (PAP/CHAP/EAP)          │          │
│  │  • Accounting (Start/Interim/Stop)         │          │
│  │  • CoA (Disconnect/Bandwidth/Timed-Out)   │          │
│  └──────────────────────┬───────────────────────┘          │
│                         │                                    │
│  ◄────────────── RADIUS Protocol ──────────────►            │
│                         │                                    │
│              ┌──────────▼──────────┐                         │
│              │  FreeRADIUS Server │                         │
│              │   (External)       │                         │
│              └───────────────────┘                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Features

### Supported Access Protocols

| Protocol | Description | Status | Tested |
|---------|-------------|--------|--------|
| **PPPoE** | Point-to-Point Protocol over Ethernet | ✅ Complete | ✅ Yes |
| **IPoE** | IP over Ethernet (DHCP) | ✅ Complete | ⏳ Pending |
| **L2TP** | Layer 2 Tunneling Protocol | ✅ Complete | ⏳ Pending |
| **PPTP** | Point-to-Point Tunneling Protocol | ✅ Complete | ⏳ Pending |
| **SSTP** | Secure Socket Tunneling Protocol | ✅ Complete | ⏳ Pending |

### RADIUS Features

| Feature | Description | Status |
|---------|-------------|--------|
| **Authentication** | PAP, CHAP, MS-CHAPv2, EAP-MD5, EAP-TLS | ✅ |
| **Accounting** | Start, Interim-Update, Stop | ✅ |
| **CoA-Request** | Session-Timeout, Bandwidth, Data-Limit | ✅ |
| **Disconnect-Request** | Force session termination | ✅ |
| **Interim-Accounting** | Periodic session updates | ✅ |

### Management

| Feature | Description |
|---------|-------------|
| **LuCI Web Interface** | Built-in OpenWrt management |
| **CLI Tools** | accel-cmd, radtest,coa-test |
| **REST API** | Programmatic control |
| **Port Forwarding** | External access to LuCI/SSH |

## 🚀 Quick Start

### Option 1: Download Pre-built Image

```bash
# Download latest release
wget https://github.com/YOUR_USER/RNAS-OpenWrt/releases/latest/download/openwrt.img.gz
gunzip openwrt.img.gz

# Flash to device or run in VM/QEMU
```

### Option 2: Build from Source

```bash
# Clone repository
git clone https://github.com/YOUR_USER/RNAS-OpenWrt.git
cd RNAS-OpenWrt

# Run build script
./scripts/build/build-accel-ppp.sh

# Or use Docker
docker build -t rnas-openwrt-builder -f Dockerfile.builder .
docker run --rm -v $(pwd):/build rnas-openwrt-builder
```

### Option 3: Deploy to Existing OpenWrt

```bash
# On your OpenWrt device
opkg update
opkg install accel-ppp

# Deploy configurations
./scripts/deploy/deploy-configs.sh -h 192.168.1.100 -s testing123
```

## ⚙️ Configuration

### RADIUS Connection

```bash
# /etc/config/radius

config radius 'auth'
    option server '192.168.1.1'
    option secret 'your_shared_secret'
    option auth_port '1812'
    option acct_port '1813'

config radius 'coa'
    option server '192.168.1.1'
    option secret 'your_shared_secret'
    option port '3799'
```

### PPPoE Server

```bash
# /etc/accel-ppp.conf

[core]
thread-count=4

[ppp]
min-mtu=1280
mtu=1492
mru=1492

[auth]
# RADIUS authentication
auth=Radius
radius-auth-port=1812
radius-acct-port=1813
radius-secret=testing123
radius-config=/etc/accel-ppp/radius.conf

[coa]
# Dynamic Authorization
radius-coa-port=3799

[log]
verbosity=3
log-file=/var/log/accel-ppp/accel-ppp.log
```

### IP Pool

```bash
# /etc/accel-ppp/ip-pool.conf

[ip-pool]
gw-pool-address=10.0.0.1
pool=10.0.0.2-10.0.0.254
```

## 🧪 Testing

### PPPoE Test

```bash
# Test RADIUS authentication
radtest username password 192.168.100.2 0 testing123

# Test CoA disconnect
./tools/coa-test.sh disconnect -s 192.168.100.2 -r testing123 -u username

# Test CoA bandwidth modification
./tools/coa-test.sh bandwidth -s 192.168.100.2 -r testing123 -u username -d 10240 -u 5120
```

### Automated Tests

```bash
# Run all protocol tests
./tests/run-all-tests.sh

# Run specific protocol tests
./tests/pppoe/test-pppoe.sh
./tests/ipoe/test-ipoe.sh
./tests/l2tp/test-l2tp.sh
```

## 📡 Port Forwarding (Default)

When deployed, these ports provide external access:

| Service | External Port | Internal Port | Purpose |
|---------|---------------|---------------|---------|
| LuCI | 8080 | 80 | Web Management |
| SSH | 2222 | 22 | CLI Access |
| CoA | 3799 | 3799 | RADIUS CoA |

## 📁 Project Structure

```
RNAS-OpenWrt/
├── README.md
├── LICENSE
├── configs/
│   ├── accel-ppp/           # accel-ppp configurations
│   ├── templates/            # Configuration templates
│   └── radius/               # RADIUS client settings
├── scripts/
│   ├── build/                # Build scripts
│   │   ├── build-accel-ppp.sh
│   │   └── cross-compile.sh
│   ├── deploy/               # Deployment scripts
│   │   └── deploy-configs.sh
│   └── tools/                # Utility scripts
├── tests/
│   ├── pppoe/               # PPPoE tests
│   ├── ipoe/                # IPoE tests
│   └── l2tp/                # L2TP tests
├── tools/
│   ├── coa-test.sh          # CoA testing tool
│   ├── radtest.sh           # RADIUS test tool
│   └── session-monitor.sh   # Session monitor
├── docs/
│   ├── PROTOCOLS.md         # Protocol documentation
│   ├── RADIUS.md            # RADIUS integration
│   └── DEPLOYMENT.md        # Deployment guide
└── .github/
    └── workflows/           # CI/CD pipelines
```

## 🔧 Protocol Details

### PPPoE (Point-to-Point over Ethernet)
- **Port**: Standard Ethernet
- **MTU**: 1492 bytes
- **Use Case**: DSL, Fiber-to-Home, ISP networks

### IPoE (IP over Ethernet / DHCP+)
- **Port**: Standard Ethernet
- **Use Case**: IPTV, Shared media networks

### L2TP (Layer 2 Tunneling Protocol)
- **Port**: UDP 1701
- **Encryption**: Often combined with IPSec
- **Use Case**: Remote access, Site-to-site VPN

### PPTP (Point-to-Point Tunneling Protocol)
- **Port**: TCP 1723, GRE (Protocol 47)
- **Encryption**: MPPE (128-bit)
- **Use Case**: Legacy VPN support

### SSTP (Secure Socket Tunneling Protocol)
- **Port**: TCP 443
- **Encryption**: HTTPS (SSL/TLS)
- **Use Case**: Firewall-friendly VPN

## 📊 Requirements

### Hardware
- **CPU**: x86_64 (recommended) or MIPS/arm64
- **RAM**: 256MB minimum, 512MB recommended
- **Storage**: 100MB minimum

### External Dependencies
- **RADIUS Server**: FreeRADIUS, Cisco ISE, Aruba ClearPass, etc.
- **Network**: Ethernet switch or bridge capable of VLANs

## 🐛 Troubleshooting

### Check Service Status
```bash
/etc/init.d/accel-ppp status
ps | grep accel-pppd
```

### View Logs
```bash
tail -f /var/log/accel-ppp/accel-ppp.log
logread | grep accel-ppp
```

### Common Issues

| Issue | Solution |
|-------|----------|
| Authentication fails | Check RADIUS secret and server connectivity |
| No IP assigned | Verify IP pool configuration |
| CoA not working | Ensure port 3799 is not blocked |
| Performance slow | Increase thread-count in config |

## 📄 License

This project is licensed under the GNU General Public License v2.0 (GPL-2.0).

## 🤝 Contributing

Contributions welcome! Please read CONTRIBUTING.md for details.

## 📚 References

- [accel-ppp Official](https://accel-ppp.org/)
- [accel-ppp GitHub](https://github.com/accel-ppp/accel-ppp)
- [OpenWrt Documentation](https://openwrt.org/)
- [RADIUS Protocol RFC 2866](https://tools.ietf.org/html/rfc2866)

## 👥 Authors

- **Your Name** - Initial work

## 🙏 Acknowledgments

- accel-ppp project for the high-performance VPN gateway
- OpenWrt community for the base distribution
- All contributors

---

**Built with ❤️ for the RADIUS community**
