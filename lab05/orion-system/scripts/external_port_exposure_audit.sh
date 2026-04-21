#!/bin/bash

# Task 3: External Port Exposure Audit
# Scans the local machine from the external perspective using nmap,
# compares detected open TCP ports against a whitelist of expected ports,
# and reports any unexpected exposed ports.

# --- Whitelist of expected ports ---
# Only these ports should be externally visible on this host.
EXPECTED_PORTS=(1 5000 6000)

TARGET="127.0.0.1"

# --- Run nmap scan to detect open TCP ports ---
# -n  : disable DNS resolution (use numeric addresses only)
# -p- : scan all 65535 TCP ports
# -oG : greppable output format for easy parsing
SCAN_OUTPUT=$(nmap -n -p- "$TARGET" 2>/dev/null)

# --- Extract open port numbers from nmap output ---
# Parse lines like "5000/tcp   open  ..."
OPEN_PORTS=$(echo "$SCAN_OUTPUT" | awk '/\/tcp/ && /open/ {split($1,a,"/"); print a[1]}')

UNEXPECTED_COUNT=0

# --- Compare each open port against the whitelist ---
for port in $OPEN_PORTS; do
    FOUND=0
    for expected in "${EXPECTED_PORTS[@]}"; do
        if [ "$port" -eq "$expected" ]; then
            FOUND=1
            break
        fi
    done
    # If port is not in the whitelist, report it as unexpected
    if [ "$FOUND" -eq 0 ]; then
        echo "EXPOSED PORT: $port"
        UNEXPECTED_COUNT=$((UNEXPECTED_COUNT + 1))
    fi
done

# --- Final summary ---
if [ "$UNEXPECTED_COUNT" -eq 0 ]; then
    echo "NO UNEXPECTED EXPOSED PORTS"
else
    echo "TOTAL UNEXPECTED EXPOSED PORTS: $UNEXPECTED_COUNT"
fi
