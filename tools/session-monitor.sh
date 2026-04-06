#!/bin/bash
# Session Monitor for RNAS-OpenWrt

set -e

NAS_IP="${NAS_IP:-192.168.100.2}"
ACCEL_CMD="${ACCEL_CMD:-accel-cmd}"

log_info() { echo "[INFO] $1"; }

show_sessions() {
    log_info "Active sessions:"
    if command -v "$ACCEL_CMD" &> /dev/null; then
        "$ACCEL_CMD" show sessions
    else
        log_info "accel-cmd not found, using /proc"
        cat /var/run/accel-ppp/sessions 2>/dev/null || \
            log_info "No session info available"
    fi
}

monitor() {
    local interval="${1:-5}"
    
    while true; do
        clear
        echo "=== RNAS-OpenWrt Session Monitor ==="
        echo "Time: $(date)"
        echo ""
        show_sessions
        echo ""
        echo "Press Ctrl+C to exit"
        sleep "$interval"
    done
}

case "$1" in
    show)
        show_sessions
        ;;
    monitor|watch)
        monitor "${2:-5}"
        ;;
    *)
        echo "Usage: $0 {show|monitor} [interval]"
        ;;
esac
