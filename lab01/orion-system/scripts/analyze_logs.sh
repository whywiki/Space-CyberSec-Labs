#!/bin/bash

echo "Count all ERROR and WARN"
grep -E "WARN|ERROR" logs/*.log | wc -l > reports/log_summary.txt
