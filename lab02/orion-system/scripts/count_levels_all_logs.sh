#!/bin/bash

echo "INFO: $(grep -h "INFO" logs/*.log | wc -l)" > reports/level_summary.txt
echo "WARN: $(grep -h "WARN" logs/*.log | wc -l)" >> reports/level_summary.txt
echo "ERROR: $(grep -h "ERROR" logs/*.log | wc -l)" >> reports/level_summary.txt
