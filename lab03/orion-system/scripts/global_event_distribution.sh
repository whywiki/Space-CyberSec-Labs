#!/bin/bash

echo "Global Event Distribution:"
for level in INFO WARN ERROR
do
    count=$(grep -h "$level" logs/*.log | wc -l)
    echo "$level: $count"
done
