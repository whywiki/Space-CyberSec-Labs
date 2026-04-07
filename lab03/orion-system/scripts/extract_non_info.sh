#!/bin/bash

total=$(grep -hv INFO logs/*.log | wc -l)
echo "Non-INFO entries: $total"
