#!/bin/bash
# ============================================================================
# VM3 CPE Client Deployment Script
# ============================================================================
# Installs all CPE (Customer Premises Equipment) client tools on VM3.
# VM3 is a Ubuntu VM running under VMware Station on Windows 11.
# These tools simulate end-user clients for end-to-end protocol testing
# against the RNAS NAS device.
#
# Usage:
#   ./scripts/deploy/install-vm3-cpe.sh          # Install all clients
#   ./scripts/deploy/install-vm3-cpe.sh --verify  # Verify installation
#   ./scripts/deploy/install-vm3-cpe.sh --test    # Run connectivity tests
#
# Environment:
#   RNAS_HOST - NAS IP address (default: 192.168.0.84)
# ============================================================================

set -e

NAS_IP="${RNAS_HOST:-192.168.0.84}"
PPPOE_USER="${PPPOE_USER:-testuser}"
PPPOE_PASS="${PPPOE_PASS:-testpass}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ============================================================================
# Install all CPE client tools
# ============================================================================
install_clients() {
    log_info "Updating package lists..."
    sudo apt-get update -qq

    log_info "Installing CPE client tools..."

    # PPPoE client
    sudo apt-get install -y -qq \
        pppoe \
        pppoeconf \
        ppp \
        2>/dev/null || sudo apt-get install -y -qq pppoe ppp

    # PPTP client
    sudo apt-get install -y -qq pptp-linux 2>/dev/null || \
        log_warn "pptp-linux not available, skipping"

    # L2TP client
    sudo apt-get install -y -qq \
        strongswan \
        xl2tpd \
        2>/dev/null || log_warn "L2TP tools partially installed"

    # DHCP / IPoE
    sudo apt-get install -y -qq \
        isc-dhcp-client \
        2>/dev/null || sudo apt-get install -y -qq dhcpcd5

    # Network utilities
    sudo apt-get install -y -qq \
        tcpdump \
        net-tools \
        iproute2 \
        iperf3 \
        curl \
        nmap

    # Python for scripting
    sudo apt-get install -y -qq \
        python3 \
        python3-pip

    log_info "All CPE client tools installed successfully"
}

# ============================================================================
# Verify installation
# ============================================================================
verify_installation() {
    local all_ok=0

    echo ""
    echo "=== CPE Client Tools Verification ==="
    echo ""

    # Core PPP tools
    for cmd in pppd pppoe tcpdump ip iperf3 curl; do
        if command -v "$cmd" &>/dev/null; then
            echo -e "  ${GREEN}✓${NC} $cmd found"
        else
            echo -e "  ${RED}✗${NC} $cmd NOT found"
            all_ok=1
        fi
    done

    # Optional tools
    for cmd in pptp xl2tpd strongswan dhclient nmap; do
        if command -v "$cmd" &>/dev/null; then
            echo -e "  ${GREEN}✓${NC} $cmd found (optional)"
        fi
    done

    echo ""
    if [ "$all_ok" -eq 0 ]; then
        log_info "All core CPE tools verified"
    else
        log_error "Some core tools are missing"
        return 1
    fi
}

# ============================================================================
# Test connectivity against RNAS
# ============================================================================
test_connectivity() {
    echo ""
    echo "=== RNAS Connectivity Tests ==="
    echo ""

    # Test basic reachability
    log_info "Testing reachability to RNAS (${NAS_IP})..."
    if ping -c 2 -W 2 "$NAS_IP" &>/dev/null; then
        echo -e "  ${GREEN}✓${NC} RNAS reachable at ${NAS_IP}"
    else
        echo -e "  ${RED}✗${NC} RNAS NOT reachable at ${NAS_IP}"
        log_warn "Skipping further tests - NAS not reachable"
        return 1
    fi

    # Test RADIUS ports
    for port in 1812 1813 3799; do
        if timeout 2 bash -c "echo > /dev/tcp/${NAS_IP}/${port}" 2>/dev/null; then
            echo -e "  ${GREEN}✓${NC} Port ${port} open on ${NAS_IP}"
        else
            echo -e "  ${YELLOW}?${NC} Port ${port} not reachable (may be UDP)"
        fi
    done

    echo ""
    log_info "Connectivity tests complete"
}

# ============================================================================
# Create PPPoE test configuration
# ============================================================================
create_test_configs() {
    local config_dir="$HOME/rnas-cpe-configs"
    mkdir -p "$config_dir"

    # PPPoE test script
    cat > "$config_dir/test-pppoe.sh" << 'PPPOE_SCRIPT'
#!/bin/bash
# PPPoE test script for VM3
# Connects to RNAS via PPPoE and verifies connectivity

NAS_IP="${1:-192.168.0.84}"
USER="${2:-testuser}"
PASS="${3:-testpass}"
IFACE="${4:-eth0}"

echo "=== PPPoE Test ==="
echo "NAS: ${NAS_IP}  User: ${USER}"

# Start PPPoE
sudo pppoe -I "$IFACE" -U "$USER" -P "$PASS" -T 60 &
PPPD_PID=$!
sleep 5

# Check if PPP interface came up
if ip addr show ppp0 &>/dev/null; then
    PPP_IP=$(ip addr show ppp0 | grep "inet " | awk '{print $2}')
    echo "✓ PPPoE connected: IP=${PPP_IP}"
    ping -c 3 "$NAS_IP"
    sudo kill "$PPPD_PID" 2>/dev/null
    exit 0
else
    echo "✗ PPPoE connection failed"
    sudo kill "$PPPD_PID" 2>/dev/null
    exit 1
fi
PPPOE_SCRIPT
    chmod +x "$config_dir/test-pppoe.sh"

    # L2TP test script
    cat > "$config_dir/test-l2tp.sh" << 'L2TP_SCRIPT'
#!/bin/bash
# L2TP test script for VM3

NAS_IP="${1:-192.168.0.84}"
USER="${2:-testuser}"
PASS="${3:-testpass}"

echo "=== L2TP Test ==="
echo "NAS: ${NAS_IP}  User: ${USER}"

# Create xl2tpd config
cat > /tmp/l2tp-test.conf << EOF
[lac rnas]
lns = ${NAS_IP}
pppoptfile = /tmp/l2tp-ppp-options
EOF

cat > /tmp/l2tp-ppp-options << EOF
name ${USER}
password ${PASS}
ipcp-accept-local
ipcp-accept-remote
refuse-eap
require-chap
EOF

echo "Configuration created. Run:"
echo "  sudo xl2tpd -c /tmp/l2tp-test.conf"
L2TP_SCRIPT
    chmod +x "$config_dir/test-l2tp.sh"

    # IPoE/DHCP test script
    cat > "$config_dir/test-ipoe.sh" << 'IPOE_SCRIPT'
#!/bin/bash
# IPoE test script for VM3

IFACE="${1:-eth0}"

echo "=== IPoE/DHCP Test ==="
echo "Interface: ${IFACE}"

sudo dhclient -v "$IFACE" 2>&1 | head -10

IP_ADDR=$(ip addr show "$IFACE" | grep "inet " | awk '{print $2}')
echo "IP: ${IP_ADDR}"
IPOE_SCRIPT
    chmod +x "$config_dir/test-ipoe.sh"

    log_info "Test configurations created in ${config_dir}"
    log_info "  ${config_dir}/test-pppoe.sh"
    log_info "  ${config_dir}/test-l2tp.sh"
    log_info "  ${config_dir}/test-ipoe.sh"
}

# ============================================================================
# Main
# ============================================================================
case "${1:-install}" in
    install)
        install_clients
        create_test_configs
        log_info ""
        log_info "VM3 CPE client setup complete!"
        log_info "Run '$0 --verify' to check installation"
        log_info "Run '$0 --test' to test connectivity"
        ;;
    --verify)
        verify_installation
        ;;
    --test)
        test_connectivity
        ;;
    *)
        echo "Usage: $0 [install|--verify|--test]"
        echo ""
        echo "  install     Install CPE client tools (default)"
        echo "  --verify    Verify installed tools"
        echo "  --test      Test connectivity to RNAS"
        exit 1
        ;;
esac
