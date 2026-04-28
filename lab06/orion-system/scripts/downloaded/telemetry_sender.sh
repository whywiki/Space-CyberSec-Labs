#!/bin/bash

HOST="127.0.0.1"
PORT=5000
SAT_ID="sat-001"

echo "=== TELEMETRY SENDER STARTED ==="
echo "Sending to $HOST:$PORT"
echo ""

while true; do
    TS=$(date -Iseconds)
    VALUE=$((RANDOM % 100))
    MESSAGE="SAT_ID=$SAT_ID;TIMESTAMP=$TS;VALUE=$VALUE"

    echo "[SENT] $MESSAGE"

    echo "$MESSAGE" | nc -N "$HOST" "$PORT"

    sleep 2
done
