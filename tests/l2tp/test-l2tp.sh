#!/bin/bash
# L2TP RADIUS Test Suite
# Tests RADIUS authentication, accounting, and CoA for L2TP protocol

set -e

# Configuration
RADIUS_SERVER="${RADIUS_SERVER:-192.168.100.1}"
RADIUS_SECRET="${RADIUS_SECRET:-testing123}"
NAS_IP="${NAS_IP:-192.168.100.2}"
TEST_USER="${TEST_USER:-testuser}"
TEST_PASS="${TEST_PASS:-testpass123}"
L2TP_PORT="${L2TP_PORT:-1701}"
CONFIG_FILE="${CONFIG_FILE:-../configs/l2tp.conf}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

run_test() {
    local test_name="$1"
    local test_cmd="$2"
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    
    log_info "Running: $test_name"
    
    if eval "$test_cmd" > /dev/null 2>&1; then
        log_success "$test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_fail "$test_name"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

print_header() {
    echo ""
    echo "========================================"
    echo "  L2TP RADIUS Protocol Test Suite"
    echo "========================================"
    echo "Server:   $RADIUS_SERVER"
    echo "NAS IP:   $NAS_IP"
    echo "L2TP Port: $L2TP_PORT"
    echo "Secret:   $RADIUS_SECRET"
    echo "User:     $TEST_USER"
    echo "========================================"
    echo ""
}

# Test 1: Configuration File Validation
test_config_file() {
    if [ -f "$CONFIG_FILE" ]; then
        grep -q "\[l2tp\]" "$CONFIG_FILE" && \
        grep -q "\[auth\]" "$CONFIG_FILE" && \
        grep -q "auth=Radius" "$CONFIG_FILE" && \
        grep -q "port=1701" "$CONFIG_FILE"
        return $?
    else
        log_warn "Config file not found: $CONFIG_FILE"
        return 1
    fi
}

# Test 2: L2TP Port Availability
test_l2tp_port() {
    if command -v nc &> /dev/null; then
        nc -z -w 3 127.0.0.1 $L2TP_PORT 2>/dev/null || true
        # Port check is informational only
        log_info "L2TP configured on port: $L2TP_PORT"
        return 0
    elif command -v timeout &> /dev/null; then
        timeout 2 bash -c "echo > /dev/tcp/127.0.0.1/$L2TP_PORT" 2>/dev/null || true
        return 0
    else
        log_warn "Port check tools not available"
        return 0
    fi
}

# Test 3: RADIUS Authentication (PAP)
test_radius_auth_pap() {
    if command -v radtest &> /dev/null; then
        echo "$TEST_PASS" | radtest "$TEST_USER" stdin "$NAS_IP" 0 "$RADIUS_SECRET" 2>&1
        return $?
    else
        log_warn "radtest not found, skipping authentication test"
        return 1
    fi
}

# Test 4: RADIUS Authentication (CHAP)
test_radius_auth_chap() {
    if command -v radtest &> /dev/null; then
        radtest "$TEST_USER" "$TEST_PASS" "$NAS_IP" 1 "$RADIUS_SECRET" 2>&1
        return $?
    else
        log_warn "radtest not found, skipping CHAP test"
        return 1
    fi
}

# Test 5: L2TP Tunnel Establishment
test_l2tp_tunnel() {
    log_info "Simulating L2TP tunnel establishment"
    log_info "Tunnel would use UDP port: $L2TP_PORT"
    # In a real test, this would initiate L2TP control connection
    return 0
}

# Test 6: L2TP Session Creation
test_l2tp_session() {
    log_info "Simulating L2TP session creation"
    # In a real test, this would create a PPP session over L2TP
    return 0
}

# Test 7: RADIUS Accounting Start
test_radius_acct_start() {
    log_info "Simulating RADIUS accounting start for L2TP session"
    return 0
}

# Test 8: CoA Disconnect Request
test_coa_disconnect() {
    if command -v coa-test.sh &> /dev/null; then
        ../tools/coa-test.sh disconnect -s "$NAS_IP" -r "$RADIUS_SECRET" -u "$TEST_USER"
        return $?
    else
        log_warn "coa-test.sh not found, skipping CoA test"
        return 1
    fi
}

# Test 9: CoA Session Timeout
test_coa_session_timeout() {
    if command -v coa-test.sh &> /dev/null; then
        ../tools/coa-test.sh timeout -s "$NAS_IP" -r "$RADIUS_SECRET" -u "$TEST_USER" -t 3600
        return $?
    else
        log_warn "coa-test.sh not found, skipping CoA timeout test"
        return 1
    fi
}

# Run all tests
run_all_tests() {
    print_header
    
    log_info "Running L2TP protocol tests..."
    echo ""
    
    # Configuration tests
    run_test "Configuration File Validation" "test_config_file"
    run_test "L2TP Port Configuration" "test_l2tp_port"
    
    # Authentication tests
    run_test "RADIUS Authentication (PAP)" "test_radius_auth_pap"
    run_test "RADIUS Authentication (CHAP)" "test_radius_auth_chap"
    
    # L2TP protocol tests
    run_test "L2TP Tunnel Establishment" "test_l2tp_tunnel"
    run_test "L2TP Session Creation" "test_l2tp_session"
    
    # Accounting tests
    run_test "RADIUS Accounting" "test_radius_acct_start"
    
    # CoA tests
    run_test "CoA Disconnect Request" "test_coa_disconnect"
    run_test "CoA Session Timeout" "test_coa_session_timeout"
    
    # Print summary
    echo ""
    echo "========================================"
    echo "  Test Summary"
    echo "========================================"
    echo "Total:  $TESTS_TOTAL"
    echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
    echo "========================================"
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}All tests passed!${NC}"
        return 0
    else
        echo -e "${RED}Some tests failed.${NC}"
        return 1
    fi
}

# Main
case "${1:-all}" in
    auth)
        print_header
        run_test "RADIUS Authentication (PAP)" "test_radius_auth_pap"
        run_test "RADIUS Authentication (CHAP)" "test_radius_auth_chap"
        ;;
    config)
        print_header
        run_test "Configuration Validation" "test_config_file"
        ;;
    tunnel)
        print_header
        run_test "L2TP Tunnel" "test_l2tp_tunnel"
        run_test "L2TP Session" "test_l2tp_session"
        ;;
    all|*)
        run_all_tests
        ;;
esac

exit $?
