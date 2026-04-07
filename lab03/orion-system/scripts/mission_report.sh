#!/bin/bash

if [ -z "$1" ]
then
    echo "No file pattern provided"
    exit 1
fi

REPORT="reports/mission_report.txt"

file_count=0
total_entries=0
total_info=0
total_warn=0
total_error=0
max_errors=0
most_unstable=""

for file in $1
do
    file_count=$((file_count + 1))
    entries=$(wc -l < "$file")
    info=$(grep -c INFO "$file")
    warn=$(grep -c WARN "$file")
    error=$(grep -c ERROR "$file")

    total_entries=$((total_entries + entries))
    total_info=$((total_info + info))
    total_warn=$((total_warn + warn))
    total_error=$((total_error + error))

    if [ $error -gt $max_errors ]
    then
        max_errors=$error
        most_unstable=$(basename $file)
    fi
done

{
echo "MISSION REPORT"
echo "Processed files: $file_count"
echo "Total entries: $total_entries"
echo "INFO: $total_info"
echo "WARN: $total_warn"
echo "ERROR: $total_error"
echo "Most unstable log: $most_unstable"
} > $REPORT

cat $REPORT
