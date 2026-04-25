# luci-app-rnas

LuCI application for managing RADIUS NAS (accel-ppp) on OpenWrt.

## Features

### Management Interface

| Feature | Description |
|---------|-------------|
| **Overview** | System status, uptime, active sessions count |
| **RADIUS Settings** | Server, secret, ports configuration |
| **Protocol Config** | PPPoE, IPoE, L2TP, PPTP, SSTP settings |
| **IP Pool** | IP address allocation ranges |
| **Sessions** | Real-time session monitoring and termination |
| **CoA Control** | Disconnect, timeout, bandwidth modification |
| **Status** | System statistics and log viewing |

### Protocol Support

- **PPPoE**: Point-to-Point Protocol over Ethernet
- **IPoE**: IP over Ethernet (DHCP+)
- **L2TP**: Layer 2 Tunneling Protocol
- **PPTP**: Point-to-Point Tunneling Protocol
- **SSTP**: Secure Socket Tunneling Protocol

## Installation

### Build with OpenWrt SDK

```bash
# Clone the RNAS repository
git clone https://github.com/Lancer2049/RNAS.git
cd RNAS/luci-app-rnas

# Copy to OpenWrt package directory
cp -r luci-app-rnas /path/to/openwrt/package/

# Build
cd /path/to/openwrt
make package/luci-app-rnas/compile
```

### Manual Installation

```bash
# Copy files to OpenWrt device
scp -r luasrc root@192.168.1.1:/usr/lib/lua/luci/
scp -r root/* root@192.168.1.1:/
scp Makefile root@192.168.1.1:/usr/lib/lua/luci/controller/rnas.lua

# Set permissions
ssh root@192.168.1.1 "chmod 755 /etc/init.d/accel-ppp-rnas"
ssh root@192.168.1.1 "/etc/init.d/accel-ppp-rnas enable"
```

## Web Interface

Access via LuCI at: `http://192.168.1.1/cgi-bin/luci/admin/network/rnas`

### Menu Structure

```
Admin
├── Network
│   └── RADIUS NAS
│       ├── Overview          - System status
│       ├── RADIUS Settings  - RADIUS server config
│       ├── Protocol Config  - Protocol-specific settings
│       ├── IP Pool          - IP address allocation
│       ├── Sessions         - Active session management
│       ├── CoA Control      - Dynamic authorization
│       └── Status           - Logs and statistics
```

## Configuration

Configuration is stored in `/etc/config/rnas`:

```bash
config rnas 'config'
    option enabled '1'
    option protocol 'pppoe'
    option interface 'br-lan'

config radius 'radius'
    option server '192.168.1.100'
    option secret 'testing123'
    option auth_port '1812'
    option acct_port '1813'
    option coa_port '3799'
```

## CoA Operations

The web interface supports real-time CoA operations:

- **Disconnect**: Force session termination
- **Set Timeout**: Modify session timeout value
- **Set Bandwidth**: Adjust rate limits

## Dependencies

- luci-base
- luci-lib-nixio
- uhttpd
- accel-ppp
- radclient (for CoA)

## Files

```
luci-app-rnas/
├── luasrc/
│   ├── controller/
│   │   └── rnas.lua          - Main controller
│   ├── model/cbi/rnas/
│   │   ├── overview.lua       - Overview page
│   │   ├── radius.lua          - RADIUS settings
│   │   ├── protocol.lua       - Protocol config
│   │   ├── ip_pool.lua        - IP pool
│   │   ├── sessions.lua       - Session management
│   │   ├── coa.lua            - CoA control
│   │   └── status.lua         - Status page
│   ├── view/rnas/
│   │   ├── status_general.htm
│   │   ├── sessions_table.htm
│   │   ├── coa_log.htm
│   │   ├── status_overview.htm
│   │   └── status_connections.htm
│   └── i18n/
│       └── rnas.zh-cn.lua     - Chinese translations
├── root/
│   ├── etc/
│   │   ├── config/rnas        - UCI config
│   │   ├── init.d/accel-ppp-rnas  - Init script
│   │   └── uci-defaults/luci-rnas - Default config
│   └── usr/share/luci/menu.d/
│       └── luci-app-rnas.json - Menu entries
├── Makefile
└── README.md
```

## License

GPL-2.0
