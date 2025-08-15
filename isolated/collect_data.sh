#!/bin/bash


./script.sh 100  on
./script.sh 300  on
./script.sh 500  on
./script.sh 700  on
./script.sh 1000 on

./script.sh 100  off
./script.sh 300  off
./script.sh 500  off
./script.sh 700  off
./script.sh 1000 off

timestamp=$(date '+%Y%m%d%H%M%S')
zip "data_${timestamp}.zip" *.json
