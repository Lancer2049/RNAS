#!/bin/bash
# RNAS Deploy Script — packages the API + config engine and deploys to VM3.
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
STAGE="/tmp/rnas-deploy-$$"

SSH="sshpass -p ${VM3_PASS} ssh -o StrictHostKeyChecking=no root@${VM3_HOST}"
SCP="sshpass -p ${VM3_PASS} scp -o StrictHostKeyChecking=no"

echo "=== RNAS Deploy to VM3 (${VM3_HOST}) ==="

# 1. Build a clean package tree (avoids the flat-copy mistakes of scp glob)
# NOTE: the systemd unit's WorkingDirectory is /opt/rnas-fastapi — the tar
# must extract to that exact name, not a generic 'api' dir, or the deployed
# files land somewhere the service never reads.
mkdir -p "${STAGE}/rnas-fastapi/routes" "${STAGE}/rnas-fastapi/services" "${STAGE}/rnas-fastapi/api" "${STAGE}/rnas-config"
cp "${REPO_DIR}"/web/api/*.py "${REPO_DIR}"/web/rnas_env.py "${STAGE}/rnas-fastapi/"
cp "${REPO_DIR}"/web/api/routes/*.py "${STAGE}/rnas-fastapi/routes/"
cp "${REPO_DIR}"/web/api/services/*.py "${STAGE}/rnas-fastapi/services/"
cp "${REPO_DIR}"/cmd/rnas-config/*.py "${STAGE}/rnas-config/"
# api.* import chain: keep a copy at <root>/api/
cp "${REPO_DIR}"/web/api/auth.py "${REPO_DIR}"/web/api/validators.py \
   "${REPO_DIR}"/web/api/http_client.py "${REPO_DIR}"/web/api/event_bus.py \
   "${REPO_DIR}"/web/api/state_collector.py "${REPO_DIR}"/web/api/models.py \
   "${STAGE}/rnas-fastapi/api/"
touch "${STAGE}/rnas-fastapi/api/__init__.py"

# 2. Package
tar czf "${STAGE}/rnas.tar.gz" -C "${STAGE}" rnas-fastapi rnas-config

# 3. Deploy to VM3: correct dirs, then restart fastapi
$SSH "mkdir -p /opt/rnas-fastapi /opt/rnas-config"
$SCP "${STAGE}/rnas.tar.gz" root@${VM3_HOST}:/tmp/rnas.tar.gz
$SSH "
tar xzf /tmp/rnas.tar.gz -C /opt
# fresh api/ package dir — the import chain resolves api.* from here
rm -rf /opt/rnas-fastapi/__pycache__ /opt/rnas-fastapi/*/__pycache__ 2>/dev/null || true
chmod +x /opt/rnas-config/rnas_config.py
ln -sf /opt/rnas-config/rnas_config.py /usr/bin/rnas-config 2>/dev/null || true
systemctl daemon-reload
systemctl restart rnas-fastapi
sleep 3
systemctl is-active rnas-fastapi
curl -s http://127.0.0.1:9099/api/health
"

echo ""
echo "=== Deploy complete! ==="
rm -rf "${STAGE}"
