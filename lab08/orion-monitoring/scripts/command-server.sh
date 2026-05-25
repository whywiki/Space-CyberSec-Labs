#!/bin/sh
echo "Mission ORION command listener starting..."
while true
do
  nc -l 6004 >> /tmp/mission-commands.log
  tail -n 1 /tmp/mission-commands.log
done
