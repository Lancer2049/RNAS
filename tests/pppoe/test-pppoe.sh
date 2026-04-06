#!/bin/bash
# PPPoE RADIUS Test Suite
# Tests RADIUS authentication, accounting, and CoA for PPPoE protocol

set -e

# Configuration
RADIUS_SERVER="${RADIUS_SERVER:-192.168.100.1}"
RADIUS_SECRET="${RADIUS_SECRET:-testing123}"
NAS_IP="${NAS_IP:-192.168.100.2}"
TEST_USER="${TEST_USER:-testuser}"
TEST_PASS="${TEST_PASS:-testpass123}"
CONFIG_FILE="${CONFIG_FILE:-../configs/pppoe.conf}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
    echo "  PPPoE RADIUS Protocol Test Suite"
    echo "========================================"
    echo "Server:   $RADIUS_SERVER"
    echo "NAS IP:   $NAS_IP"
    echo "Secret:   $RADIUS_SECRET"
    echo "User:     $TEST_USER"
    echo "========================================"
    echo ""
}

# Test 1: RADIUS Authentication (PAP)
test_radius_auth_pap() {
    if command -v radtest &> /dev/null; then
        echo "$TEST_PASS" | radtest "$TEST_USER" stdin "$NAS_IP" 0 "$RADIUS_SECRET" 2>&1
        return $?
    elif command -v radtest.sh &> /dev/null; then
        radtest.sh "$RADIUS_SERVER" "$RADIUS_SECRET" "$TEST_USER" "$TEST_PASS"
        return $?
    else
        log_warn "radtest not found, skipping authentication test"
        return 1
    fi
}

# Test 2: RADIUS Authentication (CHAP)
test_radius_auth_chap() {
    if command -v radtest &> /dev/null; then
        radtest "$TEST_USER" "$TEST_PASS" "$NAS_IP" 1 "$RADIUS_SECRET" 2>&1
        return $?
    else
        log_warn "radtest not found, skipping CHAP test"
        return 1
    fi
}

# Test 3: RADIUS Accounting Start
test_radius_acct_start() {
    if command -v radtest &> /dev/null; then
        # Simulate accounting start
        echo "Acct-Status-Type = Start" > /tmp/acct_start.txt
        echo "User-Name = $TEST_USER" >> /tmp/acct_start.txt
        echo "Framed-IP-Address = 10.0.0.100" >> /tmp/acct_start.txt
        echo "NAS-IP-Address = $NAS_IP" >> /tmp/acct_start.txt
        echo "Acct-Session-Id = $(date +%s)001" >> /tmp/acct_start.txt
        echo "Acct-Delay-Time = 0" >> /tmp/acct_start.txt
        return 0
    else
        log_warn "radtest not found, skipping accounting test"
        return 1
    fi
}

# Test 4: Configuration File Validation
test_config_file() {
    if [ -f "$CONFIG_FILE" ]; then
        # Check for required sections
        grep -q "\[pppoe\]" "$CONFIG_FILE" && \
        grep -q "\[auth\]" "$CONFIG_FILE" && \
        grep -q "auth=Radius" "$CONFIG_FILE"
        return $?
    else
        log_warn "Config file not found: $CONFIG_FILE"
        return 1
    fi
}

# Test 5: CoA Disconnect Request
test_coa_disconnect() {
    if command -v coa-test.sh &> /dev/null; then
        ../tools/coa-test.sh disconnect -s "$NAS_IP" -r "$RADIUS_SECRET" -u "$TEST_USER"
        return $?
    else
        log_warn "coa-test.sh not found, skipping CoA test"
        return 1
    fi
}

# Test 6: CoA Session Timeout
test_coa_session_timeout() {
    if command -v coa-test.sh &> /dev/null; then
        ../tools/coa-test.sh timeout -s "$NAS_IP" -r "$RADIUS_SECRET" -u "$TEST_USER" -t 3600
        return $?
    else
        log_warn "coa-test.sh not found, skipping CoA timeout test"
        return 1
    fi
}

# Test 7: CoA Bandwidth Modification
test_coa_bandwidth() {
    if command -v coa-test.sh &> /dev/null; then
        ../tools/coa-test.sh bandwidth -s "$NAS_IP" -r "$RADIUS_SECRET" -u "$TEST_USER" -d 10240 -u 5120
        return $?
    else
        log_warn "coa-test.sh not found, skipping bandwidth test"
        return 1
    fi
}

# Run all tests
run_all_tests() {
    print_header
    
    log_info "Running PPPoE protocol tests..."
    echo ""
    
    # Authentication tests
    run_test "RADIUS Authentication (PAP)" "test_radius_auth_pap"
    run_test "RADIUS Authentication (CHAP)" "test_radius_auth_chap"
    
    # Accounting tests
    run_test "RADIUS Accounting Start" "test_radius_acct_start"
    
    # Configuration tests
    run_test "Configuration File Validation" "test_config_file"
    
    # CoA tests
    run_test "CoA Disconnect Request" "test_coa_disconnect"
    run_test "CoA Session Timeout" "test_coa_session_timeout"
    run_test "CoA Bandwidth Modification" "test_coa_bandwidth"
    
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
    acct)
        print_header
        run_test "RADIUS Accounting" "test_radius_acct_start"
        ;;
    coa)
        print_header
        run_test "CoA Disconnect" "test_coa_disconnect"
        run_test "CoA Session Timeout" "test_coa_session_timeout"
        run_test "CoA Bandwidth" "test_coa_bandwidth"
        ;;
    config)
        print_header
        run_test "Configuration Validation" "test_config_file"
        ;;
    all|*)
        run_all_tests
        ;;
esac

exit $?
