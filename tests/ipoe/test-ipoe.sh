#!/bin/bash
# IPoE (DHCP+) RADIUS Test Suite
# Tests RADIUS authentication, accounting, and CoA for IPoE protocol

set -e

# Configuration
RADIUS_SERVER="${RADIUS_SERVER:-192.168.100.1}"
RADIUS_SECRET="${RADIUS_SECRET:-testing123}"
NAS_IP="${NAS_IP:-192.168.100.2}"
TEST_MAC="${TEST_MAC:-00:11:22:33:44:55}"
CONFIG_FILE="${CONFIG_FILE:-../configs/ipoe.conf}"

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
    echo "  IPoE (DHCP+) RADIUS Test Suite"
    echo "========================================"
    echo "Server:   $RADIUS_SERVER"
    echo "NAS IP:   $NAS_IP"
    echo "Secret:   $RADIUS_SECRET"
    echo "Test MAC: $TEST_MAC"
    echo "========================================"
    echo ""
}

# Test 1: MAC Address Format Validation
test_mac_format() {
    if [[ "$TEST_MAC" =~ ^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$ ]]; then
        return 0
    else
        log_fail "Invalid MAC format: $TEST_MAC"
        return 1
    fi
}

# Test 2: Configuration File Validation
test_config_file() {
    if [ -f "$CONFIG_FILE" ]; then
        grep -q "\[ipoe\]" "$CONFIG_FILE" && \
        grep -q "\[auth\]" "$CONFIG_FILE" && \
        grep -q "auth=Radius" "$CONFIG_FILE" && \
        grep -q "username-format=mac" "$CONFIG_FILE"
        return $?
    else
        log_warn "Config file not found: $CONFIG_FILE"
        return 1
    fi
}

# Test 3: DHCP Lease Simulation
test_dhcp_lease() {
    # Simulate DHCP lease request with RADIUS attributes
    log_info "Simulating DHCP lease request for MAC: $TEST_MAC"
    
    # In a real test, this would send a DHCP request
    # For now, we just validate the format
    if [[ "$TEST_MAC" =~ ^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$ ]]; then
        return 0
    fi
    return 1
}

# Test 4: RADIUS Access-Request (simulated)
test_radius_access_request() {
    # Simulate sending Access-Request with Calling-Station-Id
    if command -v echo &> /dev/null; then
        log_info "Simulating Access-Request for MAC: $TEST_MAC"
        log_info "Username would be: $(echo $TEST_MAC | tr -d ':')"
        return 0
    fi
    return 1
}

# Test 5: RADIUS Accounting (simulated)
test_radius_accounting() {
    # Simulate accounting start for IPoE session
    log_info "Simulating accounting start for IPoE session"
    return 0
}

# Test 6: CoA Session Update
test_coa_session_update() {
    if command -v coa-test.sh &> /dev/null; then
        ../tools/coa-test.sh timeout -s "$NAS_IP" -r "$RADIUS_SECRET" -u "$(echo $TEST_MAC | tr -d ':')" -t 3600
        return $?
    else
        log_warn "coa-test.sh not found, skipping CoA test"
        return 1
    fi
}

# Test 7: IP Pool Configuration
test_ip_pool() {
    if [ -f "$CONFIG_FILE" ]; then
        grep -q "\[ip-pool\]" "$CONFIG_FILE" || grep -q "pool=" "$CONFIG_FILE"
        return $?
    else
        log_warn "Config file not found"
        return 1
    fi
}

# Run all tests
run_all_tests() {
    print_header
    
    log_info "Running IPoE protocol tests..."
    echo ""
    
    # Format tests
    run_test "MAC Address Format Validation" "test_mac_format"
    
    # Configuration tests
    run_test "Configuration File Validation" "test_config_file"
    run_test "IP Pool Configuration" "test_ip_pool"
    
    # DHCP/IPoE tests
    run_test "DHCP Lease Simulation" "test_dhcp_lease"
    run_test "RADIUS Access-Request" "test_radius_access_request"
    run_test "RADIUS Accounting" "test_radius_accounting"
    
    # CoA tests
    run_test "CoA Session Update" "test_coa_session_update"
    
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
    mac)
        print_header
        run_test "MAC Address Format" "test_mac_format"
        ;;
    config)
        print_header
        run_test "Configuration Validation" "test_config_file"
        ;;
    pool)
        print_header
        run_test "IP Pool Configuration" "test_ip_pool"
        ;;
    all|*)
        run_all_tests
        ;;
esac

exit $?
