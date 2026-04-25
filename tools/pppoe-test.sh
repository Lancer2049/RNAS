#!/bin/bash
# PPPoE Test Script for RNAS

set -e

RADIUS_HOST="${RADIUS_HOST:-192.168.1.1}"
RADIUS_SECRET="${RADIUS_SECRET:-testing123}"
NAS_IP="${NAS_IP:-192.168.100.2}"

log_info() { echo "[INFO] $1"; }
log_error() { echo "[ERROR] $1" >&2; }

test_auth() {
    local user="$1"
    local pass="$2"
    
    log_info "Testing RADIUS auth for user: $user"
    radtest "$user" "$pass" "$NAS_IP" 0 "$RADIUS_SECRET"
}

test_coa_disconnect() {
    local user="$1"
    
    log_info "Testing CoA disconnect for user: $user"
    echo "User-Name=$user" | radclient "$NAS_IP:3799" disconnect "$RADIUS_SECRET"
}

test_coa_bandwidth() {
    local user="$1"
    local down="$2"
    local up="$3"
    
    log_info "Testing CoA bandwidth modification: down=$down up=$up"
    echo "User-Name=$user, Download-Speed-Limit=$down, Upload-Speed-Limit=$up" | \
        radclient "$NAS_IP:3799" coa "$RADIUS_SECRET"
}

case "$1" in
    auth)
        test_auth "${2:-testuser}" "${3:-test123}"
        ;;
    disconnect)
        test_coa_disconnect "${2:-testuser}"
        ;;
    bandwidth)
        test_coa_bandwidth "${2:-testuser}" "${3:-10240}" "${4:-5120}"
        ;;
    *)
        echo "Usage: $0 {auth|disconnect|bandwidth} [username] [password/args]"
        ;;
esac
