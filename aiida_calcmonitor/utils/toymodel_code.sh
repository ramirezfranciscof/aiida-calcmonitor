#!/bin/bash

COUNTER=0
COUNTER_MAX=$1

while [ $COUNTER -le $COUNTER_MAX ]
do
    sleep 10s
    COUNTER=$((COUNTER+10))
    echo "elapsed time $COUNTER secs"
done