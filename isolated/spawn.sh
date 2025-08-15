#!/bin/bash

BUNDLE="/home/ec2-user/load/bundle/"

N=300

for i in $(seq 1 $N); do
    container_dir="container_$i"

    runc \
        run -bundle $BUNDLE -d "container_$i" &

    echo "Started container_$i"
done

