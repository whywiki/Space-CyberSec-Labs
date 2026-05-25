#!/bin/sh
echo "================================="
echo "MISSION ORION INCIDENT SIMULATOR"
echo "================================="
echo "Scenario:"
echo "Unauthorized administrative commands"
echo ""

for i in $(seq 1 20)
do
  echo "Injecting malicious command #$i"
  echo "USER=intruder;ROLE=admin;CMD=SHUTDOWN" | nc 127.0.0.1 6004
  sleep 0.2
done

echo ""
echo "Attack simulation completed."
echo "================================="
