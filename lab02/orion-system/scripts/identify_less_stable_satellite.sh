#!/bin/bash

max_count=0
max_sat=""

for logfile in logs/*.log; do
    count=$(grep "ERROR" "$logfile" | wc -l)
    echo "$logfile ERROR count: $count"

    if [ "$count" -gt "$max_count" ]; then
        max_count=$count
        max_sat=$logfile
    fi
done

echo "Less stable satellite: $max_sat ($max_count errors)"
