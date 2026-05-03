#!/bin/bash
# RNAS Concurrent Stress Test — launches N simultaneous PPPoE connections
# Usage: ./stress-pppoe.sh [COUNT=10]

COUNT=${1:-10}
PASS=123456
SSH="sshpass -p $PASS ssh -o StrictHostKeyChecking=no"

echo "=== RNAS PPPoE Stress Test: $COUNT concurrent connections ==="
START=$(date +%s)
PIDS=()
RESULTS=()

for i in $(seq 1 $COUNT); do
    $SSH root@192.168.0.201 "
        timeout 15 pppd call rnas-pppoe nodetach 2>&1 > /tmp/pppoe-$i.log
    " &
    PIDS+=($!)
done

echo "Launched $COUNT connections, waiting..."
wait

PASSED=0
FAILED=0
TIMES=()

for i in $(seq 1 $COUNT); do
    LOG=$($SSH root@192.168.0.201 "cat /tmp/pppoe-$i.log 2>/dev/null" 2>/dev/null)
    if echo "$LOG" | grep -q "PAP authentication succeeded"; then
        IP=$(echo "$LOG" | grep "local  IP address" | awk '{print $4}')
        PASSED=$((PASSED+1))
        echo "  ✅ conn $i: $IP"
    else
        FAILED=$((FAILED+1))
        REASON=$(echo "$LOG" | grep -E "failed|Error|timeout" | head -1)
        echo "  ❌ conn $i: ${REASON:-no output}"
    fi
done

ELAPSED=$(( $(date +%s) - START ))
echo ""
echo "=== Results: $PASSED/$COUNT passed, $FAILED failed in ${ELAPSED}s ==="

# Cleanup
$SSH root@192.168.0.203 "/home/lancer/projects/RNAS/build/accel-ppp/install/usr/bin/accel-cmd terminate all 2>/dev/null" 2>/dev/null
echo "Sessions cleaned"
