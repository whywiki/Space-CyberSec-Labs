#!/bin/bash

grep "INFO" logs/*.log | cat > reports/info_only.txt
