#!/bin/bash
# RNAS Post-Boot Verification — run after system startup or crash recovery
# Ensures all services are running and configuration is valid

VM3="192.168.0.203"
PASS=0; FAIL=0
pass() { echo "  ✅ $1"; PASS=$((PASS+1)); }
fail() { echo "  ❌ $1"; FAIL=$((FAIL+1)); }

echo "=== RNAS Post-Boot Verification ==="
echo ""

# 1. Create /var/run/rnas if missing (tmpfs cleared on reboot)
if [ ! -d /var/run/rnas ]; then
    mkdir -p /var/run/rnas
    pass "Created /var/run/rnas"
else
    pass "/var/run/rnas exists"
fi

# 2. Verify core services
for svc in rnas-accel-ppp rnas-web dnsmasq; do
    if systemctl is-active --quiet $svc 2>/dev/null; then
        pass "$svc active"
    else
        systemctl start $svc 2>/dev/null
        sleep 1
        systemctl is-active --quiet $svc 2>/dev/null && pass "$svc started" || fail "$svc failed"
    fi
done

# 3. Verify optional services
for svc in strongswan-starter wg-quick@wg0 openvpn-server@server keepalived snmpd rnas-qosd; do
    systemctl is-active --quiet $svc 2>/dev/null && pass "$svc active" || \
        { systemctl start $svc 2>/dev/null; sleep 1; systemctl is-active --quiet $svc 2>/dev/null && pass "$svc started" || pass "$svc skipped"; }
done

# 4. Verify accel-ppp config is valid and ports are listening
if [ -f /var/run/rnas/accel-ppp.conf ]; then
    pass "accel-ppp config exists"
else
    /usr/bin/rnas-config --root /etc/rnas generate accel-ppp -o /var/run/rnas/accel-ppp.conf
    systemctl restart rnas-accel-ppp
    [ -f /var/run/rnas/accel-ppp.conf ] && pass "accel-ppp config regenerated" || fail "config generation failed"
fi

# 5. Verify key ports
for port in 1723 1701 443 8099 3799; do
    proto="tcp"
    [ $port -eq 1701 ] && proto="udp"
    [ $port -eq 3799 ] && proto="udp"
    if ss -${proto:0:1}lnp 2>/dev/null | grep -q ":$port "; then
        pass "port $port listening"
    else
        fail "port $port NOT listening"
    fi
done

# 6. Verify IPoE kernel module
if lsmod | grep -q ipoe; then
    pass "ipoe kernel module loaded"
else
    modprobe ipoe 2>/dev/null && pass "ipoe module loaded" || fail "ipoe module missing"
fi

# 7. Run quick PPPoE test
pppoe-discovery -I ens33 2>/dev/null | grep -q "RNAS" && pass "PPPoE AC visible" || fail "PPPoE AC not found"

echo ""
echo "=== Verification complete: $PASS passed, $FAIL failed ==="
[ $FAIL -eq 0 ]
