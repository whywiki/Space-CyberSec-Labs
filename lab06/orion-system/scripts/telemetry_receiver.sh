#!/bin/bash

PORT=5000

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/../reports/telemetry_insecure.log"

mkdir -p "$(dirname "$LOG_FILE")"
touch "$LOG_FILE"

echo "=== TELEMETRY RECEIVER STARTED ==="
echo "Listening on port $PORT"
echo "Logging to $LOG_FILE"
echo ""

while true; do
    nc -l 127.0.0.1 "$PORT" | while IFS= read -r line; do
        TS=$(date -Iseconds)
        echo "[RECEIVED $TS] $line"
        echo "[RECEIVED $TS] $line" >> "$LOG_FILE"
    done
done
