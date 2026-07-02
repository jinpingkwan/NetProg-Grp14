#!/bin/bash

echo "=========================="
echo "Network Connectivity Test"
echo "=========================="

hosts=(
10.10.10.1
10.10.10.2
)

for host in "${hosts[@]}"
do
    echo ""
    echo "Testing $host"

    if ping -c 2 $host >/dev/null
    then
        echo "[PASS] $host reachable"
    else
        echo "[FAIL] $host unreachable"
    fi
done