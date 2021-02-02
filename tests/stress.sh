#!/usr/bin/env bash

set -e

THREADS=400
LOOPS=8

START=$(date +%s.%N)

i=0;
for ((i = 0; i < THREADS; i++)); do
    for ((j = 0; j < LOOPS; j++)); do
        curl http://127.0.0.1:5000/servers/0b0t.org &>/dev/null &
    done
    pids[${i}]=$!
done

echo "started $THREADS threads with $LOOPS loops"

for pid in ${pids[*]}; do
    wait $pid
done

END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)

echo "done in $DIFF sec"
