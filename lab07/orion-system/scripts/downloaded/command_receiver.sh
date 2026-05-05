#!/bin/bash

PORT=6000
REPORT_DIR="../reports"
LOG_FILE="$REPORT_DIR/command_channel.log"

mkdir -p "$REPORT_DIR"
touch "$LOG_FILE"

echo "=== INSECURE COMMAND RECEIVER STARTED ==="
echo "Listening on 127.0.0.1:$PORT"
echo "Logging to $LOG_FILE"
echo ""

while true; do
    nc -l 127.0.0.1 "$PORT" | while IFS= read -r line; do
        TS=$(date -Iseconds)

        USER_NAME=$(echo "$line" | grep -o 'USER=[^;]*' | cut -d= -f2)
        ROLE=$(echo "$line" | grep -o 'ROLE=[^;]*' | cut -d= -f2)
        CMD=$(echo "$line" | grep -o 'CMD=[^;]*' | cut -d= -f2)
        MSG_TS=$(echo "$line" | grep -o 'TIMESTAMP=[^;]*' | cut -d= -f2)

        echo "[RECEIVED $TS] USER=$USER_NAME ROLE=$ROLE CMD=$CMD"
        echo "[RECEIVED $TS] USER=$USER_NAME ROLE=$ROLE CMD=$CMD MSG_TS=$MSG_TS RAW=$line" >> "$LOG_FILE"

        case "$CMD" in
            SET_MODE_NOMINAL)
                echo "[ACTION] Switching satellite mode to NOMINAL"
                echo "[ACTION $TS] SET_MODE_NOMINAL" >> "$LOG_FILE"
                ;;
            SET_MODE_SAFE)
                echo "[ACTION] Switching satellite mode to SAFE"
                echo "[ACTION $TS] SET_MODE_SAFE" >> "$LOG_FILE"
                ;;
            RESET)
                echo "[ACTION] Simulated satellite reset"
                echo "[ACTION $TS] RESET" >> "$LOG_FILE"
                ;;
            SHUTDOWN)
                echo "[ACTION] Simulated satellite shutdown"
                echo "[ACTION $TS] SHUTDOWN" >> "$LOG_FILE"
                ;;
            *)
                echo "[UNKNOWN COMMAND] $CMD"
                echo "[UNKNOWN $TS] RAW=$line" >> "$LOG_FILE"
                ;;
        esac

        echo ""
    done
done
