#!/bin/bash
# RNAS 802.1X Setup — configure hostapd wired authenticator with FreeRADIUS backend.
# Run on VM3: bash scripts/setup-dot1x.sh
set -e

VM3_HOST="${RNAS_VM3_HOST:-192.168.0.203}"
VM2_HOST="${RNAS_RADIUS_HOST:-192.168.0.202}"

echo "=== RNAS 802.1X Setup ==="
echo "VM3 (NAS): ${VM3_HOST}"
echo "VM2 (RADIUS): ${VM2_HOST}"
echo ""

# Step 1: Install hostapd
echo "[1/5] Installing hostapd..."
apt-get update -qq && apt-get install -y -qq hostapd || {
    echo "hostapd install failed — install manually: apt install hostapd"
    exit 1
}

# Step 2: Enable 802.1X in RNAS config
echo "[2/5] Enabling 802.1X in /etc/rnas/wireless.d/dot1x.conf..."
sed -i 's/^enabled = no/enabled = yes/' /etc/rnas/wireless.d/dot1x.conf

# Step 3: Generate hostapd config from RNAS config
echo "[3/5] Generating hostapd-wired.conf..."
rnas-config --root /etc/rnas generate dot1x -o /etc/hostapd/hostapd-wired.conf

echo "=== Generated hostapd-wired.conf ==="
cat /etc/hostapd/hostapd-wired.conf

# Step 4: Configure FreeRADIUS EAP on VM2
echo "[4/5] Configuring FreeRADIUS EAP on VM2..."
sshpass -p 123456 ssh -o StrictHostKeyChecking=no root@${VM2_HOST} "
    ln -sf /etc/freeradius/3.0/mods-available/eap /etc/freeradius/3.0/mods-enabled/eap 2>/dev/null || true
    systemctl restart freeradius
    echo 'FreeRADIUS EAP module enabled'
"

# Step 5: Start hostapd
echo "[5/5] Starting hostapd (wired 802.1X authenticator)..."
systemctl stop hostapd 2>/dev/null || true
hostapd -B /etc/hostapd/hostapd-wired.conf 2>&1 || {
    echo "hostapd failed to start — check certs at /etc/rnas/ssl/dot1x/"
    echo "May need: openssl req -x509 -newkey rsa:2048 -keyout /etc/rnas/ssl/dot1x/server.key -out /etc/rnas/ssl/dot1x/server.crt -days 365 -nodes -subj '/CN=rnas-dot1x'"
    echo "         cp /etc/rnas/ssl/dot1x/server.crt /etc/rnas/ssl/dot1x/ca.crt"
}

echo ""
echo "=== 802.1X Setup Complete ==="
echo "Verify: radtest testuser testpass ${VM2_HOST} 0 testing123"
echo "Test from client: eapol_test -c /etc/hostapd/hostapd-wired.conf -s testing123"
