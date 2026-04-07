#!/bin/bash

for file in logs/*.log
do
    count=$(grep -c ERROR "$file")
    echo "$count $file"
done | sort -rn | awk '{print $2": "$1}'
