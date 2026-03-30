#!/bin/bash

err_sat1=$(grep ERROR logs/sat-001.log)
err_sat2=$(grep ERROR logs/sat-002.log)

echo "ERRORS from log1:"
echo "$err_sat1"

echo ""

echo "ERRORS from log2:"
echo "$err_sat2"
