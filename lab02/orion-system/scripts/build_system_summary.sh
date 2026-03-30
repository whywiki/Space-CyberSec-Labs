#!/bin/bash

echo "Total log entries: $(cat logs/*.log | wc -l)" > reports/system_summary.txt
echo "Total ERROR events: $(grep "ERROR" logs/*.log | wc -l)" >> reports/system_summary.txt
echo "Total WARN events: $(grep "WARN" logs/*.log | wc -l)" >> reports/system_summary.txt
echo "Total INFO events: $(grep "INFO" logs/*.log | wc -l)" >> reports/system_summary.txt
