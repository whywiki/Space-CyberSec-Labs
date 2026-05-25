#!/bin/sh
echo "Mission ORION telemetry service starting..."
COUNTER=0
while true
do
  echo "$(date) INFO telemetry packet received id=$COUNTER"
  COUNTER=$((COUNTER+1))
  sleep 2
done
