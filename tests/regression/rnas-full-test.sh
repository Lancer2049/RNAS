#!/bin/bash
# RNAS Full Protocol Regression Test Suite

PASS=0; FAIL=0; START=$(date +%s)
pass() { echo "  ✅ $1"; PASS=$((PASS+1)); }
fail() { echo "  ❌ $1"; FAIL=$((FAIL+1)); }
S="sshpass -p 123456 ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5"

echo "=== RNAS Full Protocol Regression ==="
echo ""

# Pre-checks
$S root@192.168.0.203 "systemctl is-active rnas-accel-ppp" >/dev/null 2>&1 && pass "accel-ppp" || fail "accel-ppp"
$S root@192.168.0.202 "systemctl is-active freeradius" >/dev/null 2>&1 && pass "FreeRADIUS" || fail "FreeRADIUS"

# PPPoE
OUT=$($S root@192.168.0.201 "timeout 8 pppd call rnas-pppoe nodetach 2>&1")
echo "$OUT" | grep -q "PAP authentication succeeded" && pass "PPPoE auth" || fail "PPPoE"
echo "$OUT" | grep -q "local  IP address" && pass "PPPoE IP" || fail "PPPoE IP"

# PPTP
OUT=$($S root@192.168.0.201 "timeout 8 pppd call rnas-pptp 2>&1")
echo "$OUT" | grep -q "PAP authentication succeeded" && pass "PPTP auth" || fail "PPTP"

# L2TP
$S root@192.168.0.201 "systemctl stop xl2tpd 2>/dev/null; sleep 1; systemctl start xl2tpd; sleep 4; echo 'c rnas' > /var/run/xl2tpd/l2tp-control; sleep 12" 2>/dev/null
IP=$($S root@192.168.0.201 "ip addr show dev ppp0 2>&1 | grep 'inet '" 2>/dev/null | awk '{print $2}')
[ -n "$IP" ] && pass "L2TP: $IP" || fail "L2TP"

# SSTP  
OUT=$($S root@192.168.0.201 "timeout 15 pppd call rnas-sstp 2>&1")
echo "$OUT" | grep -q "PAP authentication succeeded" && pass "SSTP auth" || fail "SSTP"

# IPoE
OUT=$($S root@192.168.0.201 "python3 /tmp/dhcp_test.py 2>&1")
echo "$OUT" | grep -q "192.168.100" && pass "IPoE DHCP" || fail "IPoE"

# Dashboard
HTTP=$(curl -s -o /dev/null -w '%{http_code}' http://192.168.0.203:8099/)
[ "$HTTP" = "200" ] && pass "Web HTTP 200" || fail "Web HTTP $HTTP"
API=$(curl -s http://192.168.0.203:8099/api/health | grep -c '"ok"')
[ "$API" -gt 0 ] && pass "API health" || fail "API"

# RADIUS DB
COUNT=$($S root@192.168.0.202 "PGPASSWORD=radpass psql -h localhost -U radius -d radius -t -c \"SELECT count(*) FROM radpostauth WHERE authdate > now() - interval '5 minutes'\"" 2>/dev/null | tr -d ' ')
[ "${COUNT:-0}" -gt 0 ] && pass "RADIUS DB: $COUNT auths" || fail "RADIUS DB"

# Summary
ELAPSED=$(( $(date +%s) - START ))
echo ""
echo "=== $PASS passed, $FAIL failed in ${ELAPSED}s ==="
[ $FAIL -eq 0 ]
