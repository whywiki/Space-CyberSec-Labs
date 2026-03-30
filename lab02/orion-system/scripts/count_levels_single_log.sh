#!/bin/bash

grep -oE "INFO|WARN|ERROR" logs/sat-001.log | sort | uniq -c
