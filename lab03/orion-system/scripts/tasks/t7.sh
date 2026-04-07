#!/bin/bash

REPORT="reports/dynamic_report.txt"

echo "DYNAMIC REPORT" > $REPORT
echo "Generated: $(date)" >> $REPORT

for file in logs/*.log
do
    total=$(wc -l < "$file")
    info=$(grep -c INFO "$file")
    warn=$(grep -c WARN "$file")
    error=$(grep -c ERROR "$file")

    echo "" >> $REPORT
    echo "File: $(basename $file)" >> $REPORT
    echo "Total entries: $total" >> $REPORT
    echo "INFO:  $info" >> $REPORT
    echo "WARN:  $warn" >> $REPORT
    echo "ERROR: $error" >> $REPORT
done

cat $REPORT
