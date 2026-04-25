#!/bin/bash
# RADIUS Packet Capture Tool for RNAS
# Captures and optionally decodes RADIUS traffic on ports 1812/1813/3799
#
# Usage:
#   ./radius-capture.sh start [name]     # Start capture in background
#   ./radius-capture.sh stop             # Stop running capture
#   ./radius-capture.sh analyze [pcap]   # Decode and analyze a pcap file
#   ./radius-capture.sh live             # Live decode (foreground, Ctrl+C to stop)
#

set -e

CAPTURE_DIR="/tmp/radius-capture"
INTERFACE="${INTERFACE:-any}"
PID_FILE="${CAPTURE_DIR}/capture.pid"
DUMPCAP="${DUMPCAP:-$(command -v dumpcap 2>/dev/null || echo '')}"
TCPDUMP="${TCPDUMP:-$(command -v tcpdump 2>/dev/null || echo '')}"
TSHARK="${TSHARK:-$(command -v tshark 2>/dev/null || echo '')}"

ensure_dir() {
	mkdir -p "$CAPTURE_DIR"
}

# Find the best available packet capture tool
find_captool() {
	if [ -n "$DUMPCAP" ]; then
		echo "dumpcap"
	elif [ -n "$TCPDUMP" ]; then
		echo "tcpdump"
	else
		echo ""
	fi
}

# RADIUS ports filter expression
radius_filter() {
	echo "port 1812 or port 1813 or port 3799"
}

# Start background capture
cmd_start() {
	local name="${1:-radius-$(date +%Y%m%d-%H%M%S)}"
	local pcap_file="${CAPTURE_DIR}/${name}.pcap"
	local captool
	captool=$(find_captool)

	ensure_dir

	if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
		echo "[ERROR] Capture already running (PID $(cat "$PID_FILE"))" >&2
		echo "  Stop it first: $0 stop" >&2
		return 1
	fi

	case "$captool" in
		dumpcap)
			$DUMPCAP -i "$INTERFACE" -f "$(radius_filter)" -w "$pcap_file" \
				-P > /dev/null 2>&1 &
			echo $! > "$PID_FILE"
			echo "[INFO] dumpcap capture started: $pcap_file (PID $(cat "$PID_FILE"))"
			;;
		tcpdump)
			$TCPDUMP -i "$INTERFACE" -nn -s 0 "$(radius_filter)" -w "$pcap_file" \
				> /dev/null 2>&1 &
			echo $! > "$PID_FILE"
			echo "[INFO] tcpdump capture started: $pcap_file (PID $(cat "$PID_FILE"))"
			;;
		*)
			echo "[ERROR] No packet capture tool found (install tcpdump or wireshark)" >&2
			return 1
			;;
	esac
}

# Stop background capture
cmd_stop() {
	if [ ! -f "$PID_FILE" ]; then
		echo "[WARN] No capture PID file found at $PID_FILE" >&2
		# Try to find and kill any orphaned captures
		pkill -f "tcpdump.*\(port 1812 or port 1813 or port 3799\)" 2>/dev/null || true
		pkill -f "dumpcap.*\(port 1812 or port 1813 or port 3799\)" 2>/dev/null || true
		return 0
	fi

	local pid
	pid=$(cat "$PID_FILE")
	if kill "$pid" 2>/dev/null; then
		echo "[INFO] Capture stopped (PID $pid)"
	else
		echo "[WARN] Capture process $pid not running" >&2
	fi
	rm -f "$PID_FILE"

	# Find the last pcap file
	local latest
	latest=$(find "$CAPTURE_DIR" -name '*.pcap' -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)
	if [ -n "$latest" ]; then
		local size
		size=$(stat -c %s "$latest" 2>/dev/null || stat -f %z "$latest" 2>/dev/null || echo "unknown")
		echo "[INFO] Captured data: $latest (${size} bytes)"
		echo "  Analyze with: $0 analyze \"$latest\""
	fi
}

# Analyze a pcap file
cmd_analyze() {
	local pcap_file="$1"

	if [ ! -f "$pcap_file" ]; then
		echo "[ERROR] File not found: $pcap_file" >&2
		return 1
	fi

	if [ -n "$TSHARK" ]; then
		echo "============================================"
		echo "  RADIUS Packet Analysis: $(basename "$pcap_file")"
		echo "============================================"
		echo ""

		# Summary by RADIUS packet type
		echo "--- Packet Summary (by Code) ---"
		$TSHARK -r "$pcap_file" -Y "radius" -T fields \
			-e frame.number -e frame.time_relative \
			-e radius.code -e radius.id \
			-e radius.packet_type \
			-E header=y -E separator='    ' 2>/dev/null || \
		echo "(no RADIUS packets found)"

		echo ""

		# Accounting packets detail
		echo "--- Accounting Packets ---"
		$TSHARK -r "$pcap_file" -Y "radius.code == 4 || radius.code == 5" -T fields \
			-e frame.number -e frame.time_relative \
			-e radius.code -e radius.id \
			-e radius.Acct-Status-Type \
			-e radius.User-Name \
			-e radius.Acct-Session-Id \
			-e radius.Acct-Input-Octets \
			-e radius.Acct-Output-Octets \
			-E header=y -E separator='    ' 2>/dev/null

		echo ""

		# CoA/Disconnect packets
		echo "--- CoA/Disconnect Packets ---"
		$TSHARK -r "$pcap_file" -Y "radius.code == 43 || radius.code == 44 || radius.code == 40 || radius.code == 41" -T fields \
			-e frame.number -e frame.time_relative \
			-e radius.code -e radius.id \
			-e radius.User-Name \
			-e radius.Session-Timeout \
			-e radius.NAS-IP-Address \
			-E header=y -E separator='    ' 2>/dev/null

		echo ""

		# Authentication packets
		echo "--- Authentication Summary ---"
		$TSHARK -r "$pcap_file" -Y "radius.code == 1 || radius.code == 2 || radius.code == 3 || radius.code == 11" -T fields \
			-e frame.number -e frame.time_relative \
			-e radius.code -e radius.id \
			-e radius.User-Name \
			-e radius.Service-Type \
			-e radius.Framed-Protocol \
			-E header=y -E separator='    ' 2>/dev/null

		echo ""
		echo "--- RADIUS Code Legend ---"
		echo "   1 = Access-Request      2 = Access-Accept"
		echo "   3 = Access-Reject       4 = Accounting-Request"
		echo "   5 = Accounting-Response  11 = Access-Challenge"
		echo "   40 = Disconnect-Request  41 = Disconnect-ACK"
		echo "   42 = Disconnect-NAK      43 = CoA-Request"
		echo "   44 = CoA-ACK             45 = CoA-NAK"
	else
		# Fallback: basic summary with tcpdump
		echo "[INFO] tshark not available, showing pcap summary with tcpdump"
		$TCPDUMP -nn -r "$pcap_file" 2>/dev/null | head -100
	fi

	echo ""
	echo "============================================"
	echo "  File: $pcap_file"
	echo "  Packets: $($TCPDUMP -nn -r "$pcap_file" 2>/dev/null | wc -l)"
	if [ -n "$TSHARK" ]; then
		echo "  RADIUS packets: $($TSHARK -r "$pcap_file" -Y radius 2>/dev/null | wc -l)"
	fi
	echo "============================================"
}

# Live capture with real-time decode
cmd_live() {
	local captool
	captool=$(find_captool)

	if [ -z "$captool" ]; then
		echo "[ERROR] No packet capture tool found" >&2
		return 1
	fi

	if [ -n "$TSHARK" ]; then
		echo "[INFO] Live RADIUS capture (Ctrl+C to stop)"
		echo "[INFO] Decoding RADIUS on ports 1812, 1813, 3799"
		echo ""
		$TSHARK -i "$INTERFACE" -f "$(radius_filter)" -Y radius \
			-T fields -e frame.time_relative \
			-e ip.src -e ip.dst -e radius.code \
			-e radius.User-Name -e radius.Acct-Status-Type \
			-E header=y -E separator='  ->  '
	else
		echo "[INFO] Live RADIUS capture (Ctrl+C to stop)"
		echo "[INFO] tshark not installed - showing hex dump"
		$TCPDUMP -i "$INTERFACE" -nn -s 0 -X "$(radius_filter)"
	fi
}

# List captured files
cmd_list() {
	if [ -d "$CAPTURE_DIR" ]; then
		echo "Captured RADIUS pcap files:"
		ls -lh "$CAPTURE_DIR"/*.pcap 2>/dev/null || echo "  (no captures yet)"
	else
		echo "(no capture directory)"
	fi
}

usage() {
	cat <<- EOF
	Usage: $0 <command> [args]

	Commands:
	  start [name]    Start background capture (saves to /tmp/radius-capture/)
	  stop            Stop background capture
	  analyze <file>  Decode and display RADIUS packets from pcap
	  live            Live capture with real-time decoding (Ctrl+C to stop)
	  list            List captured pcap files

	Environment:
	  INTERFACE       Network interface (default: any)
	  DUMPCAP         Path to dumpcap binary
	  TCPDUMP         Path to tcpdump binary
	  TSHARK          Path to tshark binary

	Examples:
	  $0 start test-session-1
	  # ... run tests ...
	  $0 stop
	  $0 analyze /tmp/radius-capture/test-session-1.pcap
	  $0 live
	EOF
}

case "${1:-help}" in
	start)
		cmd_start "$2"
		;;
	stop)
		cmd_stop
		;;
	analyze)
		shift
		cmd_analyze "$@"
		;;
	live)
		cmd_live
		;;
	list)
		cmd_list
		;;
	help|*)
		usage
		;;
esac
