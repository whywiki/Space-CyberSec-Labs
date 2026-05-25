#!/bin/bash
USER_NAME=$1
ROLE=$2
COMMAND=$3
TRACE_ID=$(openssl rand -hex 16)
SPAN_ID=$(openssl rand -hex 8)
NOW=$(date +%s%N)
END=$((NOW + 5000000))

echo "================================="
echo "MISSION ORION COMMAND EXECUTION"
echo "================================="
echo "Operator: $USER_NAME"
echo "Role: $ROLE"
echo "Command: $COMMAND"
echo ""
echo "Sending telemetry..."

curl -X POST http://localhost:4318/v1/traces \
-H "Content-Type: application/json" \
-d "{
  \"resourceSpans\": [
    {
      \"resource\": {
        \"attributes\": [
          {
            \"key\": \"service.name\",
            \"value\": {\"stringValue\": \"mission-orion\"}
          }
        ]
      },
      \"scopeSpans\": [
        {
          \"spans\": [
            {
              \"traceId\": \"$TRACE_ID\",
              \"spanId\": \"$SPAN_ID\",
              \"name\": \"$COMMAND\",
              \"kind\": 1,
              \"startTimeUnixNano\": \"$NOW\",
              \"endTimeUnixNano\": \"$END\"
            }
          ]
        }
      ]
    }
  ]
}"

echo ""
echo "Trace sent."
echo "================================="
