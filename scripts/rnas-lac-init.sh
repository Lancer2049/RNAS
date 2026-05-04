#!/bin/bash
# RNAS LAC Tunnel Auto-Creation
# Reads /etc/rnas/access.d/lac.conf and creates L2TP LAC tunnels via accel-cmd

CONF="/etc/rnas/access.d/lac.conf"
ACCEL_CMD="/home/lancer/projects/RNAS/build/accel-ppp/install/usr/bin/accel-cmd"

[ ! -f "$CONF" ] && exit 0

enabled=$(grep -A1 '^\[lac\]' "$CONF" | grep 'enabled' | cut -d= -f2 | xargs)
[ "$enabled" != "yes" ] && exit 0

# Wait for accel-ppp to be ready
for i in $(seq 1 10); do
    $ACCEL_CMD show stat >/dev/null 2>&1 && break
    sleep 1
done

# Parse tunnel sections
grep -A10 '^\[tunnel' "$CONF" | while IFS= read -r line; do
    case "$line" in
        peer_addr*) peer=$(echo "$line" | cut -d= -f2 | xargs) ;;
        peer_port*) pport=$(echo "$line" | cut -d= -f2 | xargs) ;;
        host_addr*) host=$(echo "$line" | cut -d= -f2 | xargs) ;;
        mode*) mode=$(echo "$line" | cut -d= -f2 | xargs) ;;
        '') 
            if [ -n "$peer" ] && [ -n "$mode" ]; then
                cmd="$ACCEL_CMD l2tp create tunnel peer-addr $peer"
                [ -n "$pport" ] && cmd="$cmd peer-port $pport"
                [ -n "$host" ] && cmd="$cmd host-addr $host"
                [ "$mode" = "lac" ] && cmd="$cmd mode lac"
                echo "[rnas-lac] Creating LAC tunnel: $cmd"
                $cmd 2>&1
            fi
            peer=""; pport=""; host=""; mode=""
            ;;
    esac
done
