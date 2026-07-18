#!/bin/bash
# RNAS Deploy Script — copies updated files from repo to VM3 and restarts services.
# Run: bash scripts/deploy-to-vm3.sh
set -e

VM3_HOST="${RNAS_VM3_HOST:-192.168.0.203}"
if [ -n "$RNAS_VM3_PASS" ]; then
    VM3_PASS="$RNAS_VM3_PASS"
else
    echo "WARNING: Using default VM3 password. Set RNAS_VM3_PASS env var for security." >&2
    VM3_PASS="${RNAS_VM3_PASS:-123456}"
fi
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

SSH="sshpass -p ${VM3_PASS} ssh -o StrictHostKeyChecking=no root@${VM3_HOST}"
SCP="sshpass -p ${VM3_PASS} scp -o StrictHostKeyChecking=no"

echo "=== RNAS Deploy to VM3 (${VM3_HOST}) ==="
echo ""

# 1. Copy updated config engine
echo "[1/5] Deploying rnas-config..."
$SCP "${REPO_DIR}/cmd/rnas-config/rnas_config.py" root@${VM3_HOST}:/usr/bin/rnas-config
$SSH "chmod +x /usr/bin/rnas-config"

# 2. Copy updated config templates and new ones
echo "[2/5] Deploying config templates..."
$SCP "${REPO_DIR}/configs/access.d/core.conf" root@${VM3_HOST}:/etc/rnas/access.d/core.conf
$SCP "${REPO_DIR}/configs/access.d/mac-auth.conf" root@${VM3_HOST}:/etc/rnas/access.d/mac-auth.conf 2>/dev/null || echo "(mac-auth.conf new)"
$SCP "${REPO_DIR}/configs/network.d/ipv6.conf" root@${VM3_HOST}:/etc/rnas/network.d/ipv6.conf 2>/dev/null || echo "(ipv6.conf new)"

# 3. Copy updated web server and new config module
echo "[3/5] Deploying web server..."
$SSH "mkdir -p /opt/rnas-web"
$SCP "${REPO_DIR}/web/server.py" root@${VM3_HOST}:/opt/rnas-web/server.py
$SCP "${REPO_DIR}/web/rnas_env.py" root@${VM3_HOST}:/opt/rnas-web/rnas_env.py

# 4. Regenerate configs and restart core service
echo "[4/5] Regenerating accel-ppp config..."
$SSH "mkdir -p /var/run/rnas && /usr/bin/rnas-config --root /etc/rnas generate accel-ppp -o /var/run/rnas/accel-ppp.conf"

echo "[5/5] Restarting RNAS services..."
# Fix service unit if not already fixed
$SSH "
sed -i '/^ExecStartPre=\/usr\/bin\/rnas-config/i ExecStartPre=mkdir -p /var/run/rnas' /etc/systemd/system/rnas-accel-ppp.service 2>/dev/null
systemctl daemon-reload
systemctl restart rnas-accel-ppp
sleep 2
systemctl status rnas-accel-ppp --no-pager | head -5
"

echo ""
echo "=== Deploy complete! ==="
echo "accel-ppp status: $($SSH 'systemctl is-active rnas-accel-ppp')"
echo "Dashboard:      http://${VM3_HOST}:8099/api/health"
echo "accel-cmd:      $SSH 'accel-cmd show stat 2>&1 | head -3'"
echo ""
echo "Next: run L2TP/SSTP/IPoE protocol tests"
