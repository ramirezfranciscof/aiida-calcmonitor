#!/bin/bash
COUNTER=0
for (( ; ; ))
do
    COUNTER=$((COUNTER+1))
    echo "iteration number $COUNTER"
    sleep 1m
done