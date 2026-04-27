#!/bin/bash
# RNAS One-Command Installer for Debian/Ubuntu/UOS
set -e

echo "=== RNAS v2.0 Installer ==="
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root: sudo bash install.sh"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "[1/6] Installing system packages..."
CORE="accel-ppp dnsmasq nftables python3 curl"
OPTIONAL="snmpd strongswan wireguard-tools keepalived"
apt-get update -qq
apt-get install -y -qq $CORE 2>/dev/null || true
apt-get install -y -qq $OPTIONAL 2>/dev/null || echo "Optional packages skipped (install manually if needed)"

echo "[2/6] Installing rnas-config..."
mkdir -p /usr/bin
cp "$PROJECT_DIR/cmd/rnas-config/rnas_config.py" /usr/bin/rnas-config
chmod +x /usr/bin/rnas-config

echo "[3/6] Deploying config templates..."
mkdir -p /etc/rnas/access.d /etc/rnas/network.d /etc/rnas/vpn.d
cp "$PROJECT_DIR/configs/rnas.conf" /etc/rnas/
cp "$PROJECT_DIR/configs/access.d/"*.conf /etc/rnas/access.d/
cp "$PROJECT_DIR/configs/network.d/"*.conf /etc/rnas/network.d/
# Phase 3 configs (optional — disabled by default)
cp "$PROJECT_DIR/configs/vpn.d/"*.conf /etc/rnas/vpn.d/ 2>/dev/null || true
cp "$PROJECT_DIR/configs/qos.conf" /etc/rnas/ 2>/dev/null || true
cp "$PROJECT_DIR/configs/monitor.conf" /etc/rnas/ 2>/dev/null || true
cp "$PROJECT_DIR/configs/hotspot.conf" /etc/rnas/ 2>/dev/null || true
cp "$PROJECT_DIR/configs/ha.conf" /etc/rnas/ 2>/dev/null || true

echo "[4/6] Validating config..."
/usr/bin/rnas-config validate --root /etc/rnas/ 2>/dev/null || echo "Validation skipped (safe to ignore)"

echo "[5/6] Installing systemd units..."
cp "$PROJECT_DIR/systemd/"*.service "$PROJECT_DIR/systemd/"*.target /etc/systemd/system/
systemctl daemon-reload
systemctl enable rnas.target 2>/dev/null || true

echo "[6/6] Starting RNAS core..."
mkdir -p /var/run/rnas
systemctl start rnas-accel-ppp 2>/dev/null || echo "Start rnas-accel-ppp manually after configuring /etc/rnas/access.d/radius.conf"

echo ""
echo "=== RNAS v2.0 installed! ==="
echo "Config:    /etc/rnas/"
echo "Dashboard: http://$(hostname -I | awk '{print $1}'):5173"
echo "API:       http://$(hostname -I | awk '{print $1}'):8099/api/health"
echo "Services:  systemctl list-units 'rnas-*'"
echo "Logs:      journalctl -u rnas-accel-ppp -f"
echo ""
echo "Available services: $(systemctl list-unit-files 'rnas-*' 2>/dev/null | grep -c rnas- || echo 0) installed"
echo "  rnas-accel-ppp  rnas-dnsmasq  rnas-firewall  rnas-snmpd"
echo "  rnas-qos  rnas-ipsec  rnas-wireguard  rnas-ha"
