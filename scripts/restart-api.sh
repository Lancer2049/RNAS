#!/bin/bash
# RNAS API restart — kill the uvicorn bound to RNAS_API_PORT precisely
# (via /proc cmdline, never pgrep self-match), start it, then gate on the
# health endpoint so a failed boot surfaces immediately instead of
# silently serving stale code.
#
# Usage: bash scripts/restart-api.sh            # env from RNAS_ENV_FILE
#        RNAS_ENV_FILE=/tmp/rnas9099.env bash scripts/restart-api.sh
set -euo pipefail

API_DIR="${RNAS_API_DIR:-/opt/rnas-fastapi}"
API_PORT="${RNAS_API_PORT:-9099}"
ENV_FILE="${RNAS_ENV_FILE:-/tmp/rnas9099.env}"
LOG_FILE="${RNAS_LOG_FILE:-/var/log/rnas-api-9099.log}"
START_OUT="${RNAS_START_OUT:-/tmp/rnas-api-start.out}"
HEALTH_URL="http://127.0.0.1:${API_PORT}/api/health"
HEALTH_RETRIES=12
HEALTH_INTERVAL=2

echo "=== Restarting RNAS API on :${API_PORT} ==="

# 1. Kill the exact process bound to API_PORT (safe against pgrep self-match)
for pid in $(pgrep -f "uvicorn main:app"); do
    if tr "\0" " " < "/proc/${pid}/cmdline" 2>/dev/null | grep -q "port ${API_PORT}"; then
        echo "Killing stale pid ${pid}"
        kill "${pid}" 2>/dev/null || true
    fi
done
sleep 1

# 2. Start fresh (env file exports DB/RADIUS secrets for the process)
cd "${API_DIR}"
set -a
# shellcheck disable=SC1090
. "${ENV_FILE}"
set +a
nohup /usr/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port "${API_PORT}" >> "${LOG_FILE}" 2>&1 &
echo "PID=$!" > "${START_OUT}"
echo "Started PID $(cat "${START_OUT}")"

# 3. Health gate — fail loudly if the app does not come up
for i in $(seq 1 "${HEALTH_RETRIES}"); do
    code=$(curl -s -o /dev/null -w "%{http_code}" "${HEALTH_URL}" || true)
    if [ "${code}" = "200" ]; then
        echo "Health OK after ${i} tries (${HEALTH_URL} -> ${code})"
        exit 0
    fi
    echo "Health check ${i}/${HEALTH_RETRIES}: ${code}, retrying..."
    sleep "${HEALTH_INTERVAL}"
done

echo "ERROR: API failed health check after ${HEALTH_RETRIES} attempts."
echo "Tail of ${LOG_FILE}:"
tail -20 "${LOG_FILE}" 2>/dev/null || true
exit 1
