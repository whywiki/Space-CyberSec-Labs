#!/bin/bash

if [ -z "$1" ]
then
    echo "No pattern provided"
    exit 1
fi

PATTERN=$1
OUTPUT="reports/pattern_timestamps.txt"

grep "$PATTERN" logs/*.log | awk '{print $1, $2}' > $OUTPUT

echo "Timestamps saved to $OUTPUT"
cat $OUTPUT
