#!/bin/bash
# CoA Testing Tool for RNAS
# RADIUS Dynamic Authorization (RFC 5176) testing:
#   - Disconnect-Request (session termination)
#   - CoA-Request (Session-Timeout update, bandwidth modification)
#   - Packet capture for verification

set -e

RADIUS_HOST="${RADIUS_HOST:-192.168.1.1}"
RADIUS_SECRET="${RADIUS_SECRET:-testing123}"
NAS_IP="${NAS_IP:-192.168.100.2}"
NAS_PORT="${NAS_PORT:-3799}"
DEFAULT_IFACE="${DEFAULT_IFACE:-any}"

# Check prerequisites
check_prereqs() {
	if ! command -v radclient &> /dev/null; then
		log_error "radclient not found (install freeradius-utils)"
		exit 1
	fi
}

# Send a CoA/Disconnect packet via radclient
send_coa() {
	local action="$1"
	local user="$2"
	local extra_attrs="$3"

	log_info "Sending $action for user: $user"
	log_info "Attributes: User-Name=$user${extra_attrs:+, $extra_attrs}"

	if [ "$action" = "disconnect" ]; then
		echo "User-Name=$user${extra_attrs:+, $extra_attrs}" | \
			radclient "$NAS_IP:$NAS_PORT" disconnect "$RADIUS_SECRET"
	else
		echo "User-Name=$user${extra_attrs:+, $extra_attrs}" | \
			radclient "$NAS_IP:$NAS_PORT" coa "$RADIUS_SECRET"
	fi
}

# Disconnect a session
cmd_disconnect() {
	check_prereqs
	local user="$1"
	if [ -z "$user" ]; then
		log_error "Usage: $0 disconnect <username>"
		return 1
	fi
	send_coa "disconnect" "$user" ""
	echo "[INFO] Disconnect-Request sent to $NAS_IP:$NAS_PORT"
}

# Set session timeout
cmd_timeout() {
	check_prereqs
	local user="$1"
	local seconds="$2"
	if [ -z "$user" ] || [ -z "$seconds" ]; then
		log_error "Usage: $0 timeout <username> <seconds>"
		return 1
	fi
	send_coa "coa" "$user" "Session-Timeout=$seconds"
	echo "[INFO] CoA Session-Timeout=$seconds sent for $user"
}

# Set bandwidth limits
cmd_bandwidth() {
	check_prereqs
	local user="$1"
	local down="$2"
	local up="$3"
	if [ -z "$user" ] || [ -z "$down" ]; then
		log_error "Usage: $0 bandwidth <username> <down_kbps> [up_kbps]"
		return 1
	fi
	up="${up:-$down}"
	send_coa "coa" "$user" "WISPr-Bandwidth-Max-Down=$down,WISPr-Bandwidth-Max-Up=$up"
	log_info "CoA bandwidth: down=${down}Kbps up=${up}Kbps for $user"
}

# Data limit
cmd_data_limit() {
	check_prereqs
	local user="$1"
	local down="$2"
	local up="$3"
	if [ -z "$user" ] || [ -z "$down" ]; then
		log_error "Usage: $0 data-limit <username> <down_kb> [up_kb]"
		return 1
	fi
	up="${up:-$down}"
	send_coa "coa" "$user" "ChilliSpot-Max-Input-Octets=$((down * 1024)),ChilliSpot-Max-Output-Octets=$((up * 1024))"
	log_info "CoA data-limit: down=${down}KB up=${up}KB for $user"
}

# Test: send CoA with live packet capture
cmd_test_with_capture() {
	check_prereqs
	local action="$1"
	local user="$2"
	local extra="$3"
	local iface="${4:-$DEFAULT_IFACE}"
	local pcap_file
	pcap_file="/tmp/coa-test-$(date +%s).pcap"

	if [ -z "$user" ]; then
		log_error "Usage: $0 test <action> <username> [extra] [interface]"
		return 1
	fi

	# Start capture in background
	log_info "Starting packet capture on $iface (port $NAS_PORT)"
	tcpdump -i "$iface" -nn -s 0 -w "$pcap_file" "port $NAS_PORT" 2>/dev/null &
	local tcpdump_pid=$!
	sleep 1

	# Send the CoA packet
	case "$action" in
		disconnect)
			send_coa "disconnect" "$user" ""
			;;
		timeout)
			send_coa "coa" "$user" "Session-Timeout=${extra:-3600}"
			;;
		bandwidth)
			local down="${extra:-10240}"
			local up="${3:-$down}"
			send_coa "coa" "$user" "WISPr-Bandwidth-Max-Down=$down,WISPr-Bandwidth-Max-Up=$up"
			;;
		*)
			kill "$tcpdump_pid" 2>/dev/null || true
			log_error "Unknown action: $action"
			return 1
			;;
	esac

	sleep 1
	kill "$tcpdump_pid" 2>/dev/null || true
	wait "$tcpdump_pid" 2>/dev/null || true

	# Show captured packets
	if [ -f "$pcap_file" ] && [ -s "$pcap_file" ]; then
		log_info "Captured packets saved to $pcap_file"
		echo ""
		if command -v tshark &> /dev/null; then
			tshark -r "$pcap_file" -Y "radius" \
				-T fields -e frame.number -e frame.time_relative \
				-e radius.code -e radius.id \
				-e radius.User-Name \
				-E header=y -E separator=' | '
		else
			tcpdump -nn -r "$pcap_file" 2>/dev/null
		fi
		echo ""
		log_ok "Capture complete: $(stat -c %s "$pcap_file" 2>/dev/null || stat -f %z "$pcap_file" 2>/dev/null || echo "?") bytes"
	else
		log_error "No packets captured (is the NAS reachable on $NAS_IP:$NAS_PORT?)"
		return 1
	fi
}

usage() {
	cat <<- EOF
	Usage: $0 <action> [options]

	Actions:
	  disconnect <username>              Disconnect a session
	  timeout <username> <seconds>       Set session timeout via CoA
	  bandwidth <username> <down> [up]   Set bandwidth limits (Kbps)
	  data-limit <username> <down> [up]  Set data limits (KB)
	  test <action> <username> [args]    Run action with live packet capture
	  help                               Show this help

	Environment:
	  RADIUS_HOST    RADIUS server IP (default: 192.168.1.1)
	  RADIUS_SECRET  Shared secret (default: testing123)
	  NAS_IP         NAS IP address (default: 192.168.100.2)
	  NAS_PORT       CoA port (default: 3799)

	Examples:
	  $0 disconnect testuser
	  $0 timeout testuser 3600
	  $0 bandwidth testuser 10240 5120
	  $0 data-limit testuser 1048576 524288
	  $0 test disconnect testuser
	EOF
}

case "${1:-help}" in
	disconnect)
		shift
		cmd_disconnect "$@"
		;;
	timeout)
		shift
		cmd_timeout "$@"
		;;
	bandwidth)
		shift
		cmd_bandwidth "$@"
		;;
	data-limit)
		shift
		cmd_data_limit "$@"
		;;
	test)
		shift
		cmd_test_with_capture "$@"
		;;
	help|*)
		usage
		;;
esac
