#!/bin/bash

grep -h "WARN" logs/*.log | awk '{print $1, $2}' > reports/warn_timestamps.txt
