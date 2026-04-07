#!/bin/bash

# For each file, extract unique messages (fields 5+).
# Combine all unique-per-file messages and find those appearing in 2+ files.
for file in logs/*.log
do
    awk '{for(i=5;i<=NF;i++) printf $i (i<NF?" ":""); print ""}' "$file" | sort -u
done | sort | uniq -d
