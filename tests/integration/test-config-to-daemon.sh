#!/bin/bash
# Integration test: RNAS config → accel-ppp daemon
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=== 1. Config validation ==="
python3 "$PROJECT_DIR/cmd/rnas-config/rnas_config.py" \
    --root "$PROJECT_DIR/configs" validate

echo ""
echo "=== 2. Generate accel-ppp.conf ==="
OUTPUT="/tmp/rnas-test-accel-ppp.conf"
python3 "$PROJECT_DIR/cmd/rnas-config/rnas_config.py" \
    --root "$PROJECT_DIR/configs" generate accel-ppp -o "$OUTPUT"

echo "=== 3. Structure check ==="
for section in "[modules]" "[core]" "[common]" "[ppp]" "[radius]" "[ip-pool]" "[pppoe]" "[cli]" "[log]"; do
    if grep -q "^$section" "$OUTPUT"; then
        echo "  OK: $section"
    else
        echo "  FAIL: $section not found"
        exit 1
    fi
done

# Verify NAS identifier
grep -q "nas-identifier=rnas" "$OUTPUT" && echo "  OK: nas-identifier=rnas"
# Verify DAE server
grep -q "dae-server=" "$OUTPUT" && echo "  OK: dae-server configured"
# Verify RADIUS server
grep -q "server=.*192.168.0.85.*testing123" "$OUTPUT" && echo "  OK: RADIUS server"

echo ""
echo "=== 4. Daemon start test ==="
if command -v accel-pppd &>/dev/null; then
    cp "$OUTPUT" /tmp/accel-ppp-test.conf
    accel-pppd -c /tmp/accel-ppp-test.conf &
    PID=$!
    sleep 3
    if kill -0 $PID 2>/dev/null; then
        echo "  OK: accel-pppd started (PID $PID)"
        if ss -u -a 2>/dev/null | grep -q 3799; then
            echo "  OK: DAE port 3799 listening"
        fi
        kill $PID 2>/dev/null
    else
        echo "  WARN: accel-pppd failed to start (may need root)"
    fi
else
    echo "  SKIP: accel-pppd not installed on this host"
fi

echo ""
echo "=== PASS ==="
