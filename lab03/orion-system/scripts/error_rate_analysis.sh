#!/bin/bash

max_rate=0
highest=""

for file in logs/*.log
do
    total=$(wc -l < "$file")
    errors=$(grep -c ERROR "$file")
    rate=$(awk "BEGIN {printf \"%.4f\", $errors/$total}")
    echo "$(basename $file): $errors/$total = $rate"

    is_higher=$(awk "BEGIN {print ($rate > $max_rate) ? 1 : 0}")
    if [ "$is_higher" -eq 1 ]
    then
        max_rate=$rate
        highest=$(basename $file)
    fi
done

echo ""
echo "Highest error rate: $highest ($max_rate)"
