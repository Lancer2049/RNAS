#!/bin/bash
# CoA Testing Tool for RNAS-OpenWrt

set -e

RADIUS_HOST="${RADIUS_HOST:-192.168.1.1}"
RADIUS_SECRET="${RADIUS_SECRET:-testing123}"
NAS_IP="${NAS_IP:-192.168.100.2}"
NAS_PORT="${NAS_PORT:-3799}"

log_info() { echo "[INFO] $1"; }
log_error() { echo "[ERROR] $1" >&2; }

send_coa() {
    local action="$1"
    local user="$2"
    local attrs="$3"
    
    log_info "Sending CoA $action for user: $user"
    
    local attrs_str=""
    case "$action" in
        disconnect)
            attrs_str="User-Name=$user"
            ;;
        timeout)
            attrs_str="User-Name=$user,Session-Timeout=$attrs"
            ;;
        bandwidth)
            local down_speed="$3"
            local up_speed="$4"
            attrs_str="User-Name=$user,Download-Speed-Limit=$down_speed,Upload-Speed-Limit=$up_speed"
            ;;
        data-limit)
            local down_limit="$3"
            local up_limit="$4"
            attrs_str="User-Name=$user,Download-Limit=$down_limit,Upload-Limit=$up_limit"
            ;;
    esac
    
    echo "$attrs_str" | radclient "$NAS_IP:$NAS_PORT" "$action" "$RADIUS_SECRET"
}

usage() {
    cat << EOF
Usage: $0 <action> [options]

Actions:
    disconnect <username>           Disconnect a session
    timeout <username> <seconds>  Set session timeout
    bandwidth <username> <down> <up>  Set bandwidth limits (Kbps)
    data-limit <username> <down> <up>  Set data limits (KB)

Examples:
    $0 disconnect testuser
    $0 timeout testuser 3600
    $0 bandwidth testuser 10240 5120
    $0 data-limit testuser 1048576 524288
EOF
}

case "$1" in
    disconnect)
        send_coa "coa" "$2" ""
        ;;
    timeout)
        send_coa "coa" "$2" "$3"
        ;;
    bandwidth)
        send_coa "coa" "$2" "$3" "$4"
        ;;
    data-limit)
        send_coa "coa" "$2" "$3" "$4"
        ;;
    *)
        usage
        ;;
esac
