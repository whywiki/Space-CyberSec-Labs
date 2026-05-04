#!/bin/bash

HOST="127.0.0.1"
PORT=5001
SAT_ID="sat-001"
SECRET_KEY="orion-shared-secret"

echo "=== SECURE TELEMETRY SENDER STARTED ==="
echo "Sending to $HOST:$PORT"
echo ""

while true; do
    TS=$(date -Iseconds)
    VALUE=$((RANDOM % 100))
    MESSAGE="SAT_ID=$SAT_ID;TIMESTAMP=$TS;VALUE=$VALUE"

    SIGNATURE=$(printf "%s" "$MESSAGE" | openssl dgst -sha256 -hmac "$SECRET_KEY" | cut -d' ' -f2)
    SIGNED_MESSAGE="$MESSAGE;SIGNATURE=$SIGNATURE"

    echo "[SENT] $SIGNED_MESSAGE"

    echo "$SIGNED_MESSAGE" | nc -w 1 "$HOST" "$PORT"

    sleep 2
done
