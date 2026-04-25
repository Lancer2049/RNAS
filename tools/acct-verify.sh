#!/bin/bash
# RADIUS Accounting Packet Compliance Verifier
# Validates that RADIUS accounting packets from RNAS-OpenWrt contain
# all required attributes per RFC 2866 and RFC 2867.
#
# Reads from a pcap file (tshark required) or from stdin (text format).
#
# Usage:
#   ./acct-verify.sh <pcap-file>          # Verify pcap
#   ./acct-verify.sh --live [interface]   # Capture and verify live
#   ./acct-verify.sh --list               # List required attributes
#

set -e

TSHARK="${TSHARK:-$(command -v tshark 2>/dev/null || echo '')}"
TCPDUMP="${TCPDUMP:-$(command -v tcpdump 2>/dev/null || echo '')}"

# Required attributes per Acct-Status-Type
declare -A REQUIRED_ATTRS
REQUIRED_ATTRS["Start"]="User-Name NAS-IP-Address NAS-Port Acct-Session-Id Acct-Status-Type Acct-Delay-Time"
REQUIRED_ATTRS["Interim-Update"]="User-Name NAS-IP-Address Acct-Session-Id Acct-Status-Type Acct-Delay-Time Acct-Session-Time Acct-Input-Octets Acct-Output-Octets Acct-Input-Packets Acct-Output-Packets"
REQUIRED_ATTRS["Stop"]="User-Name NAS-IP-Address Acct-Session-Id Acct-Status-Type Acct-Delay-Time Acct-Session-Time Acct-Input-Octets Acct-Output-Octets Acct-Input-Packets Acct-Output-Packets Acct-Terminate-Cause"

# Recommended (nice-to-have) attributes
declare -A RECOMMENDED_ATTRS
RECOMMENDED_ATTRS["Start"]="NAS-Identifier NAS-Port-Type Framed-Protocol Calling-Station-Id"
RECOMMENDED_ATTRS["Interim-Update"]="NAS-Identifier NAS-Port-Type Framed-IP-Address Acct-Input-Gigawords Acct-Output-Gigawords"
RECOMMENDED_ATTRS["Stop"]="NAS-Identifier NAS-Port-Type Framed-IP-Address Calling-Station-Id Acct-Input-Gigawords Acct-Output-Gigawords"

# Acct-Status-Type enum
declare -A ACCT_STATUS_MAP
ACCT_STATUS_MAP[1]="Start"
ACCT_STATUS_MAP[2]="Stop"
ACCT_STATUS_MAP[3]="Interim-Update"
ACCT_STATUS_MAP[7]="Accounting-On"
ACCT_STATUS_MAP[8]="Accounting-Off"

VERDICTS=()
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

pass() {
	VERDICTS+=("PASS: $1")
	PASSED_CHECKS=$((PASSED_CHECKS + 1))
	TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
}

fail() {
	VERDICTS+=("FAIL: $1")
	FAILED_CHECKS=$((FAILED_CHECKS + 1))
	TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
}

warn() {
	VERDICTS+=("WARN: $1")
}

list_requirements() {
	echo "RADIUS Accounting Required Attributes (RFC 2866/2867)"
	echo "======================================================"
	echo ""
	for status in Start "Interim-Update" Stop; do
		echo "--- $status ---"
		echo "  REQUIRED:  ${REQUIRED_ATTRS[$status]}"
		echo "  RECOMMENDED: ${RECOMMENDED_ATTRS[$status]}"
		echo ""
	done

	echo "Acct-Status-Type Values:"
	for code in "${!ACCT_STATUS_MAP[@]}"; do
		printf "  %d = %s\n" "$code" "${ACCT_STATUS_MAP[$code]}"
	done
	echo ""
}

# Extract RADIUS accounting packets from pcap using tshark
extract_packets() {
	local pcap="$1"
	if [ ! -f "$pcap" ]; then
		echo "[ERROR] File not found: $pcap" >&2
		return 1
	fi

	if [ -z "$TSHARK" ]; then
		echo "[ERROR] tshark required for pcap analysis" >&2
		return 1
	fi

	# Extract Accounting-Request packets (code 4) with attributes
	$TSHARK -r "$pcap" -Y "radius.code == 4" -T fields \
		-e frame.number -e frame.time_relative \
		-e radius.code \
		-e radius.Acct-Status-Type \
		-e radius.User-Name \
		-e radius.NAS-IP-Address \
		-e radius.NAS-Identifier \
		-e radius.Acct-Session-Id \
		-e radius.Acct-Session-Time \
		-e radius.Acct-Input-Octets \
		-e radius.Acct-Output-Octets \
		-e radius.Acct-Input-Packets \
		-e radius.Acct-Output-Packets \
		-e radius.Acct-Terminate-Cause \
		-e radius.Acct-Delay-Time \
		-E header=y -E separator='|' 2>/dev/null
}

# Verify attributes for a specific Accounting-Request packet
verify_packet_attrs() {
	local frame="$1"
	local status_type="$2"
	local all_attrs="$3"
	local status_name="${ACCT_STATUS_MAP[$status_type]:-Unknown($status_type)}"

	if [ -z "$status_type" ]; then
		warn "Frame $frame: no Acct-Status-Type found"
		return
	fi

	if [ "$status_name" = "Unknown($status_type)" ]; then
		warn "Frame $frame: unknown Acct-Status-Type value: $status_type"
		return
	fi

	echo "  Acct-Status-Type: $status_name (value $status_type)"

	# Check required attributes
	local missing_req=0
	for attr in ${REQUIRED_ATTRS[$status_name]}; do
		if echo "$all_attrs" | grep -qi "$attr"; then
			pass "Frame $frame: $attr present in $status_name"
		else
			fail "Frame $frame: $attr MISSING in $status_name"
			missing_req=$((missing_req + 1))
		fi
	done

	# Check recommended attributes
	for attr in ${RECOMMENDED_ATTRS[$status_name]}; do
		if echo "$all_attrs" | grep -qi "$attr"; then
			pass "Frame $frame: $attr present in $status_name"
		else
			warn "Frame $frame: $attr not present in $status_name (recommended)"
		fi
	done

	echo ""
}

# Verify a text accounting record (one packet per line, pipe-separated)
verify_text() {
	local line="$1"
	local frame status_type
	frame=$(echo "$line" | cut -d'|' -f1)
	status_type=$(echo "$line" | cut -d'|' -f4)

	verify_packet_attrs "$frame" "$status_type" "$line"
}

# Main verify function
cmd_verify() {
	local pcap="$1"

	if [ -z "$pcap" ]; then
		echo "[ERROR] No pcap file specified" >&2
		return 1
	fi

	echo ""
	echo "============================================"
	echo "  RADIUS Accounting Compliance Verification"
	echo "============================================"
	echo "  File: $pcap"
	echo "============================================"
	echo ""

	# Extract and verify each accounting packet
	local tmpfile
	tmpfile=$(mktemp)
	extract_packets "$pcap" > "$tmpfile" || {
		rm -f "$tmpfile"
		return 1
	}

	local pkt_count
	pkt_count=$(tail -n +2 "$tmpfile" 2>/dev/null | grep -c . || true)

	if [ "$pkt_count" -eq 0 ]; then
		echo "[INFO] No Accounting-Request packets found"
		rm -f "$tmpfile"
		return 0
	fi

	echo "Found $pkt_count Accounting-Request packet(s)"
	echo ""

	# Process each packet (skip header line)
	tail -n +2 "$tmpfile" | while IFS= read -r line; do
		[ -z "$line" ] && continue
		verify_text "$line"
	done

	rm -f "$tmpfile"
}

# Live capture and verify
cmd_live() {
	local iface="${1:-any}"
	local tmpfile
	tmpfile=$(mktemp)

	echo "[INFO] Starting live RADIUS capture on interface '$iface'"
	echo "[INFO] Press Ctrl+C to stop and verify"
	echo ""

	# Capture packets, then analyze
	if [ -n "$TSHARK" ]; then
		$TSHARK -i "$iface" -f "port 1813" -Y "radius.code == 4" \
			-w "$tmpfile" -a duration:30 2>/dev/null || true
		cmd_verify "$tmpfile"
	else
		echo "[ERROR] tshark required for live verification" >&2
		rm -f "$tmpfile"
		return 1
	fi
	rm -f "$tmpfile"
}

print_report() {
	echo ""
	echo "============================================"
	echo "  Verification Report"
	echo "============================================"
	echo "  Total checks: $TOTAL_CHECKS"
	echo "  Passed:       $PASSED_CHECKS"
	echo "  Failed:       $FAILED_CHECKS"
	echo "============================================"

	if [ $FAILED_CHECKS -gt 0 ]; then
		echo "[RESULT] FAILED - $FAILED_CHECKS attribute check(s) missing"
		return 1
	else
		echo "[RESULT] PASSED - all required attributes present"
		return 0
	fi
}

usage() {
	cat <<- EOF
	Usage: $0 <command> [args]

	Commands:
	  verify <pcap>     Verify accounting packets in pcap file

	  live [interface]  Capture and verify live accounting traffic
	  --list            List required attributes per RFC 2866/2867

	Examples:
	  $0 verify /tmp/radius-capture/session.pcap
	  $0 live eth0
	  $0 --list
	EOF
}

case "${1:-help}" in
	verify)
		shift
		cmd_verify "$@"
		print_report
		;;
	live)
		shift
		cmd_live "$@"
		print_report
		;;
	--list)
		list_requirements
		;;
	help|*)
		usage
		;;
esac
