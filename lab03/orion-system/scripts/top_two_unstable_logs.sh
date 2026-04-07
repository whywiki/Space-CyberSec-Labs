#!/bin/bash

for file in logs/*.log
do
    count=$(grep -c ERROR "$file")
    echo "$count $(basename $file)"
done | sort -rn | head -2 | awk '{print $2": "$1}'
