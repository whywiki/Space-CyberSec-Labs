#!/bin/bash

total=$(cat logs/*.log | wc -l)
info=$(grep "INFO" logs/*.log | wc -l)
warn=$(grep "WARN" logs/*.log | wc -l)
error=$(grep "ERROR" logs/*.log | wc -l)

max_count=0
max_sat=""
for logfile in logs/*.log; do
    count=$(grep "ERROR" "$logfile" | wc -l)
    if [ "$count" -gt "$max_count" ]; then
        max_count=$count
        max_sat=$logfile
    fi
done

echo "ORION LOG SUMMARY" > reports/log_summary.txt
echo "Total log entries: $total" >> reports/log_summary.txt
echo "INFO events: $info" >> reports/log_summary.txt
echo "WARN events: $warn" >> reports/log_summary.txt
echo "ERROR events: $error" >> reports/log_summary.txt
echo "Less stable satellite: $max_sat" >> reports/log_summary.txt
