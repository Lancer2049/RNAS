#!/bin/bash
# RNAS Fault Injection Test Suite
# Simulates RADIUS failures and verifies system resilience

PASS=0; FAIL=0; START=$(date +%s)
pass() { echo "  ✅ $1"; PASS=$((PASS+1)); }
fail() { echo "  ❌ $1"; FAIL=$((FAIL+1)); }
S="sshpass -p 123456 ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5"
VM2="192.168.0.202"
VM3="192.168.0.203"
VM1="192.168.0.201"

echo "=== RNAS Fault Injection Test ==="
echo ""

# ── Test 1: RADIUS Timeout ──
echo "--- Test 1: RADIUS Timeout (block port 1812 on VM2) ---"
$S root@$VM2 "iptables -A INPUT -p udp --dport 1812 -j DROP" 2>/dev/null
sleep 1
OUT=$($S root@$VM1 "timeout 15 pppd call rnas-pppoe nodetach 2>&1")
echo "$OUT" | grep -q "authentication failed\|LCP.*terminated\|Connection terminated" && pass "PPPoE correctly failed on timeout" || fail "PPPoE behavior unexpected"
$S root@$VM2 "iptables -D INPUT -p udp --dport 1812 -j DROP" 2>/dev/null
sleep 2
OUT2=$($S root@$VM1 "timeout 8 pppd call rnas-pppoe nodetach 2>&1")
echo "$OUT2" | grep -q "PAP authentication succeeded" && pass "PPPoE recovered after unblock" || fail "PPPoE recovery failed"

# ── Test 2: RADIUS Reject ──
echo "--- Test 2: RADIUS Reject (wrong password) ---"
OUT=$($S root@$VM1 "timeout 8 pppd call rnas-pppoe nodetach name testuser password wrongpass 2>&1")
echo "$OUT" | grep -q "authentication failed" && pass "Correctly rejected wrong password" || fail "Wrong password handling"

# ── Test 3: Network Latency ──
echo "--- Test 3: Network Latency (200ms on RADIUS) ---"
$S root@$VM3 "tc qdisc add dev ens33 root netem delay 200ms 50ms" 2>/dev/null
sleep 1
TS1=$(date +%s%N)
$S root@$VM1 "timeout 15 pppd call rnas-pppoe nodetach 2>&1" >/dev/null 2>&1
TS2=$(date +%s%N)
ELAPSED=$(( (TS2 - TS1) / 1000000 ))
$S root@$VM3 "tc qdisc del dev ens33 root" 2>/dev/null
sleep 1
[ $ELAPSED -gt 500 ] && pass "High latency handled (${ELAPSED}ms)" || fail "Latency too low: ${ELAPSED}ms"

# ── Test 4: Session Flood ──
echo "--- Test 4: Session Flood (rapid disconnect/reconnect) ---"
for i in 1 2 3 4 5; do
  $S root@$VM1 "timeout 5 pppd call rnas-pppoe nodetach 2>&1" >/dev/null 2>&1 &
done
wait
sleep 2
COUNT=$($S root@$VM3 "/home/lancer/projects/RNAS/build/accel-ppp/install/usr/bin/accel-cmd show sessions 2>&1 | grep -c active" 2>/dev/null)
echo "Active sessions after flood: $COUNT"
[ "$COUNT" -le 5 ] && pass "Session flood contained ($COUNT active)" || fail "Too many stale sessions"

# ── Test 5: CoA Under Stress ──
echo "--- Test 5: CoA During Active Session ---"
$S root@$VM1 "timeout 20 pppd call rnas-pppoe nodetach &" 2>/dev/null
sleep 5
SID=$($S root@$VM3 "/home/lancer/projects/RNAS/build/accel-ppp/install/usr/bin/accel-cmd show sessions sid 2>&1 | grep '^ ' | head -1 | xargs")
$S root@$VM2 "printf 'User-Name=testuser' | radclient -r 1 -t 2 192.168.0.203:3799 disconnect testing123 2>&1" >/dev/null 2>&1
sleep 2
REMAIN=$($S root@$VM3 "/home/lancer/projects/RNAS/build/accel-ppp/install/usr/bin/accel-cmd show sessions 2>&1 | grep -c active" 2>/dev/null)
[ "$REMAIN" -eq 0 ] && pass "CoA disconnected during stress" || fail "CoA failed under stress"

$S root@$VM1 "pkill pppd" 2>/dev/null
$S root@$VM3 "/home/lancer/projects/RNAS/build/accel-ppp/install/usr/bin/accel-cmd terminate all 2>/dev/null" 2>/dev/null

# ── Summary ──
ELAPSED=$(( $(date +%s) - START ))
echo ""
echo "=== Fault Injection Results: $PASS/$((PASS+FAIL)) passed ($FAIL failed) in ${ELAPSED}s ==="
[ $FAIL -eq 0 ]
