#!/bin/bash

for file in logs/*.log
do
    error_count=$(grep -c ERROR "$file")
    if [ "$error_count" -eq 0 ]
    then
        echo "$(basename $file): no errors"
    fi
done
