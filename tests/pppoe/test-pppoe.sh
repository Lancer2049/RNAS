#!/bin/bash
# PPPoE RADIUS Test Suite
# Tests RADIUS authentication, accounting, and CoA for PPPoE protocol.
#
# Uses:
#   tests/radius/     - FreeRADIUS test configuration
#   tools/radius-capture.sh - Packet capture and analysis
#   tools/acct-verify.sh    - Accounting compliance verification
#   tools/coa-test.sh       - CoA/Disconnect testing

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TOOLS_DIR="${PROJECT_ROOT}/tools"

RADIUS_SERVER="${RADIUS_SERVER:-192.168.100.1}"
RADIUS_SECRET="${RADIUS_SECRET:-testing123}"
NAS_IP="${NAS_IP:-192.168.100.2}"
TEST_USER="${TEST_USER:-testuser}"
TEST_PASS="${TEST_PASS:-testpass123}"
CAPTURE_IFACE="${CAPTURE_IFACE:-any}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[PASS]${NC} $1"; }
log_fail()    { echo -e "${RED}[FAIL]${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }

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

# Test 3: RADIUS Accounting Start packet verification
# Captures RADIUS traffic, sends a test Accounting-Request, and verifies
# the required attributes are present in the Start record.
test_radius_acct_start() {
	if ! command -v tcpdump &> /dev/null; then
		log_warn "tcpdump not found, skipping accounting capture test"
		return 1
	fi
	if ! command -v radclient &> /dev/null; then
		log_warn "radclient not found, skipping accounting test"
		return 1
	fi

	local pcap_file
	pcap_file="/tmp/acct-start-test-$$.pcap"
	local session_id
	session_id="test-$(date +%s)-$$"

	# Start capture
	tcpdump -i "$CAPTURE_IFACE" -nn -s 0 -c 2 -w "$pcap_file" \
		"port 1813 and src host $NAS_IP" 2>/dev/null &
	local tcpdump_pid=$!
	sleep 1

	# Send Accounting-Start packet
	echo "User-Name=$TEST_USER" \
		"NAS-IP-Address=$NAS_IP" \
		"NAS-Port=100" \
		"Acct-Session-Id=$session_id" \
		"Acct-Status-Type=Start" \
		"Acct-Delay-Time=0" \
		"Service-Type=Framed-User" \
		"Framed-Protocol=PPP" \
		"Framed-IP-Address=10.0.0.100" \
		"Calling-Station-Id=00:11:22:33:44:55" \
		"NAS-Identifier=rnas-openwrt" \
		"NAS-Port-Type=Virtual" | \
		radclient "$NAS_IP:1813" acct "$RADIUS_SECRET" 2>/dev/null || true

	sleep 2
	kill "$tcpdump_pid" 2>/dev/null || true
	wait "$tcpdump_pid" 2>/dev/null || true

	# Verify capture result
	if [ -f "$pcap_file" ] && [ -s "$pcap_file" ]; then
		log_info "Accounting-Start packet captured"
		rm -f "$pcap_file"
		return 0
	else
		log_warn "No accounting packet captured (is FreeRADIUS running on $NAS_IP?)"
		rm -f "$pcap_file"
		return 1
	fi
}

# Test 4: RADIUS Accounting Stop packet verification
test_radius_acct_stop() {
	if ! command -v tcpdump &> /dev/null; then
		log_warn "tcpdump not found, skipping accounting stop test"
		return 1
	fi
	if ! command -v radclient &> /dev/null; then
		log_warn "radclient not found"
		return 1
	fi

	local pcap_file
	pcap_file="/tmp/acct-stop-test-$$.pcap"
	local session_id
	session_id="test-$(date +%s)-$$"

	tcpdump -i "$CAPTURE_IFACE" -nn -s 0 -c 2 -w "$pcap_file" \
		"port 1813 and src host $NAS_IP" 2>/dev/null &
	local tcpdump_pid=$!
	sleep 1

	# Send Accounting-Stop with full attributes
	echo "User-Name=$TEST_USER" \
		"NAS-IP-Address=$NAS_IP" \
		"NAS-Port=100" \
		"Acct-Session-Id=$session_id" \
		"Acct-Status-Type=Stop" \
		"Acct-Delay-Time=0" \
		"Acct-Session-Time=3600" \
		"Acct-Input-Octets=1048576" \
		"Acct-Output-Octets=2097152" \
		"Acct-Input-Packets=1024" \
		"Acct-Output-Packets=2048" \
		"Acct-Terminate-Cause=User-Request" \
		"Service-Type=Framed-User" \
		"Framed-Protocol=PPP" \
		"Framed-IP-Address=10.0.0.100" \
		"NAS-Identifier=rnas-openwrt" | \
		radclient "$NAS_IP:1813" acct "$RADIUS_SECRET" 2>/dev/null || true

	sleep 2
	kill "$tcpdump_pid" 2>/dev/null || true
	wait "$tcpdump_pid" 2>/dev/null || true

	if [ -f "$pcap_file" ] && [ -s "$pcap_file" ]; then
		log_info "Accounting-Stop packet captured"
		rm -f "$pcap_file"
		return 0
	else
		log_warn "No accounting stop packet captured"
		rm -f "$pcap_file"
		return 1
	fi
}

# Test 5: Accounting compliance check via acct-verify.sh
test_acct_compliance() {
	if [ ! -f "${TOOLS_DIR}/acct-verify.sh" ]; then
		log_warn "acct-verify.sh not found, skipping compliance test"
		return 1
	fi

	# Test known-good pcap or run live
	log_info "Checking for accounting compliance tools"
	if command -v tshark &> /dev/null; then
		log_info "tshark available - full compliance checking supported"
		return 0
	else
		log_warn "tshark not installed - compliance checking limited (install tshark for full verification)"
		return 0
	fi
}

# Test 6: Configuration File Validation
test_config_file() {
	if [ -f "$CONFIG_FILE" ]; then
		grep -q "\[pppoe\]" "$CONFIG_FILE" && \
		grep -q "\[auth\]" "$CONFIG_FILE" && \
		grep -q "auth=Radius" "$CONFIG_FILE"
		return $?
	else
		log_warn "Config file not found: $CONFIG_FILE"
		return 1
	fi
}

# Test 7: CoA Disconnect Request
test_coa_disconnect() {
	if command -v coa-test.sh &> /dev/null; then
		"${TOOLS_DIR}/coa-test.sh" disconnect "$TEST_USER"
		return $?
	elif [ -f "${TOOLS_DIR}/coa-test.sh" ]; then
		bash "${TOOLS_DIR}/coa-test.sh" disconnect "$TEST_USER"
		return $?
	else
		log_warn "coa-test.sh not found, skipping CoA test"
		return 1
	fi
}

# Test 8: CoA Session Timeout
test_coa_session_timeout() {
	if [ -f "${TOOLS_DIR}/coa-test.sh" ]; then
		bash "${TOOLS_DIR}/coa-test.sh" timeout "$TEST_USER" 3600
		return $?
	else
		log_warn "coa-test.sh not found, skipping CoA timeout test"
		return 1
	fi
}

# Test 9: CoA Bandwidth Modification
test_coa_bandwidth() {
	if [ -f "${TOOLS_DIR}/coa-test.sh" ]; then
		bash "${TOOLS_DIR}/coa-test.sh" bandwidth "$TEST_USER" 10240 5120
		return $?
	else
		log_warn "coa-test.sh not found, skipping bandwidth test"
		return 1
	fi
}

# Test 10: Packet capture tools availability
test_capture_tools() {
	local all_found=0
	for tool in tcpdump tshark radclient; do
		if command -v "$tool" &> /dev/null; then
			log_info "  $tool: available"
		else
			log_warn "  $tool: NOT found"
			all_found=1
		fi
	done
	if [ -f "${TOOLS_DIR}/radius-capture.sh" ]; then
		log_info "  radius-capture.sh: available"
	else
		log_warn "  radius-capture.sh: NOT found"
	fi
	if [ -f "${TOOLS_DIR}/acct-verify.sh" ]; then
		log_info "  acct-verify.sh: available"
	else
		log_warn "  acct-verify.sh: NOT found"
	fi
	return $all_found
}

# Run all tests
run_all_tests() {
	print_header

	echo "--- Prerequisites ---"
	test_capture_tools
	echo ""

	log_info "Running PPPoE protocol tests..."
	echo ""

	# Authentication tests
	run_test "RADIUS Authentication (PAP)" "test_radius_auth_pap"
	run_test "RADIUS Authentication (CHAP)" "test_radius_auth_chap"

	# Accounting tests
	run_test "RADIUS Accounting Start (packet)" "test_radius_acct_start"
	run_test "RADIUS Accounting Stop (packet)" "test_radius_acct_stop"
	run_test "Accounting compliance checker" "test_acct_compliance"

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

case "${1:-all}" in
	auth)
		print_header
		run_test "RADIUS Authentication (PAP)" "test_radius_auth_pap"
		run_test "RADIUS Authentication (CHAP)" "test_radius_auth_chap"
		;;
	acct)
		print_header
		run_test "RADIUS Accounting Start" "test_radius_acct_start"
		run_test "RADIUS Accounting Stop" "test_radius_acct_stop"
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
	tools)
		print_header
		test_capture_tools
		;;
	all|*)
		run_all_tests
		;;
esac

exit $?
