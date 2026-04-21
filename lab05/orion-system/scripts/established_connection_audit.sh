#!/bin/bash

# Task 5: Established Connection Audit
# Detects all currently established TCP connections on the host.
# Uses 'lsof' (macOS equivalent of Linux 'ss -tnp state established') for socket inspection.
# On macOS, 'ss' is unavailable; lsof provides process-level connection visibility.

COUNT=0

# --- Detect established TCP connections via lsof ---
# lsof flags:
#   -i TCP    : list TCP internet connections
#   -P        : numeric ports (no service name resolution)
#   -n        : numeric addresses (no DNS resolution)
# Filter: lines containing "(ESTABLISHED)" keyword.
#
# NAME field format: local_addr:local_port->remote_addr:remote_port (ESTABLISHED)
# Example: 10.129.15.225:51148->35.190.46.17:443 (ESTABLISHED)

while IFS= read -r line; do
    cmd=$(echo "$line" | awk '{print $1}')
    pid=$(echo "$line" | awk '{print $2}')
    # NAME field is second-to-last (before "(ESTABLISHED)")
    conn=$(echo "$line" | awk '{print $(NF-1)}')

    # Split into local and remote at "->"
    local_ep=$(echo "$conn" | cut -d'>' -f1 | sed 's/-$//')
    remote_ep=$(echo "$conn" | cut -d'>' -f2)

    echo "ESTABLISHED CONNECTION: $local_ep -> $remote_ep $cmd $pid"
    COUNT=$((COUNT + 1))
done < <(lsof -i TCP -P -n 2>/dev/null | grep "(ESTABLISHED)" | awk '!seen[$1,$2,$NF]++')

# --- Final summary ---
echo ""
if [ "$COUNT" -eq 0 ]; then
    echo "NO ESTABLISHED CONNECTIONS DETECTED"
else
    echo "TOTAL ESTABLISHED CONNECTIONS: $COUNT"
fi
