#!/bin/bash
# RNAS One-Command Installer for Debian/Ubuntu/UOS
set -e

echo "=== RNAS v2.0 Installer ==="
echo ""

# Check root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root: sudo bash install.sh"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "[1/5] Installing system packages..."
DEPS="accel-ppp dnsmasq nftables python3 python3-pip curl"
apt-get update -qq
apt-get install -y -qq $DEPS 2>/dev/null || echo "Some packages may need manual install"

echo "[2/5] Installing rnas-config..."
mkdir -p /usr/bin
cp "$PROJECT_DIR/cmd/rnas-config/rnas_config.py" /usr/bin/rnas-config
chmod +x /usr/bin/rnas-config

echo "[3/5] Deploying config templates..."
mkdir -p /etc/rnas/access.d /etc/rnas/network.d
cp "$PROJECT_DIR/configs/rnas.conf" /etc/rnas/
cp "$PROJECT_DIR/configs/access.d/"*.conf /etc/rnas/access.d/
cp "$PROJECT_DIR/configs/network.d/"*.conf /etc/rnas/network.d/

echo "[4/5] Installing systemd units..."
cp "$PROJECT_DIR/systemd/"*.service "$PROJECT_DIR/systemd/"*.target /etc/systemd/system/
systemctl daemon-reload
systemctl enable rnas.target 2>/dev/null || true

echo "[5/5] Starting RNAS..."
mkdir -p /var/run/rnas
systemctl start rnas-accel-ppp 2>/dev/null || echo "Start rnas-accel-ppp manually after configuring /etc/rnas/"

echo ""
echo "=== RNAS installed! ==="
echo "Config: /etc/rnas/"
echo "API:    http://$(hostname -I | awk '{print $1}'):8099/api/health"
echo "Logs:   journalctl -u rnas-accel-ppp -f"
echo ""
echo "Next: edit /etc/rnas/access.d/radius.conf and restart:"
echo "  systemctl restart rnas-accel-ppp"
