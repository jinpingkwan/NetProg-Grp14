#!/bin/bash

echo "Hostname"
hostname

echo ""
echo "Date"
date

echo ""
echo "CPU"
lscpu

echo ""
echo "Memory"
free -h

echo ""
echo "Disk"
df -h

echo ""
echo "Users"
who

echo ""
echo "Top Processes"
ps -eo pid,comm,%cpu --sort=-%cpu | head -6
