#!/bin/bash

if [ -z "$1" ]
then
    echo "No pattern provided"
    exit 1
fi

PATTERN=$1
REPORT="reports/pattern_report.txt"

echo "PATTERN REPORT: $PATTERN" > $REPORT
for file in logs/*.log
do
    count=$(grep -c "$PATTERN" "$file")
    echo "$(basename $file): $count" >> $REPORT
done

cat $REPORT
