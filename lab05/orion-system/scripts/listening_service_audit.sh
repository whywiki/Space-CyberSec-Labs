#!/bin/bash

# Task 4: Listening Service Audit
# Detects all currently listening TCP and UDP services on the host.
# Uses 'lsof' (macOS equivalent approach to Linux 'ss -lntp -lnup') to inspect sockets.
# On macOS, 'ss' is unavailable; lsof provides equivalent process-level socket visibility.

COUNT=0

# --- Detect listening TCP sockets via lsof ---
# lsof flags:
#   -i TCP    : list TCP internet connections
#   -P        : numeric ports (no service name resolution)
#   -n        : numeric addresses (no DNS resolution)
# Filter for "(LISTEN)" state lines only.
# Deduplicate by CMD+PID+port using awk to avoid double-counting IPv4/IPv6 entries.
#
# NAME field format for listeners: *:5000 (LISTEN) or 127.0.0.1:5000 (LISTEN)

while IFS= read -r line; do
    cmd=$(echo "$line" | awk '{print $1}')
    pid=$(echo "$line" | awk '{print $2}')
    # Address is second-to-last field (before "(LISTEN)")
    addr=$(echo "$line" | awk '{print $(NF-1)}')
    # Normalize wildcard: *:PORT -> 0.0.0.0:PORT
    addr_display=$(echo "$addr" | sed 's/^\*:/0.0.0.0:/')
    echo "LISTENING SERVICE: tcp $addr_display $cmd $pid"
    COUNT=$((COUNT + 1))
done < <(lsof -i TCP -P -n 2>/dev/null \
    | grep "(LISTEN)" \
    | awk '!seen[$1,$2,$(NF-1)]++')

# --- Detect listening UDP sockets via lsof ---
# UDP sockets do not have a LISTEN state; we identify them by the absence of "->"
# in the NAME field (no remote endpoint means it is a local listening socket).
# Deduplicate by CMD+PID+address to avoid double-counting protocol variants.

while IFS= read -r line; do
    cmd=$(echo "$line" | awk '{print $1}')
    pid=$(echo "$line" | awk '{print $2}')
    addr=$(echo "$line" | awk '{print $NF}')
    # Normalize wildcard
    addr_display=$(echo "$addr" | sed 's/^\*:/0.0.0.0:/')
    echo "LISTENING SERVICE: udp $addr_display $cmd $pid"
    COUNT=$((COUNT + 1))
done < <(lsof -i UDP -P -n 2>/dev/null \
    | grep -v "^COMMAND" \
    | grep -v "\->" \
    | awk '!seen[$1,$2,$NF]++')

# --- Final summary ---
echo ""
if [ "$COUNT" -eq 0 ]; then
    echo "NO LISTENING SERVICES DETECTED"
else
    echo "TOTAL LISTENING SERVICES: $COUNT"
fi
