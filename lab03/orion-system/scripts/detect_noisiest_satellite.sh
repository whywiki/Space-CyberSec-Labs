#!/bin/bash

max=0
noisiest=""

for file in logs/*.log
do
    warn=$(grep -c WARN "$file")
    error=$(grep -c ERROR "$file")
    total=$((warn + error))

    if [ $total -gt $max ]
    then
        max=$total
        noisiest=$(basename $file)
    fi
done

echo "Noisiest satellite: $noisiest ($max WARN+ERROR events)"
