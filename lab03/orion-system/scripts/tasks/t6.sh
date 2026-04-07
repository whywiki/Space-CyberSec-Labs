#!/bin/bash

count_info() {
    grep -c INFO "$1"
}

count_warn() {
    grep -c WARN "$1"
}

count_error() {
    grep -c ERROR "$1"
}

for file in logs/*.log
do
    echo "=== $(basename $file) ==="
    echo "INFO:  $(count_info $file)"
    echo "WARN:  $(count_warn $file)"
    echo "ERROR: $(count_error $file)"
done
