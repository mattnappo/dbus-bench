#!/bin/bash

set -u -x

n_cont="$1"
systemd="$2"
rt="runsc"

if [ "$systemd" != "on" ] && [ "$systemd" != "off" ]; then
    echo "Error: systemd-cgroup must be either 'on' or 'off'."
    exit 1
fi

# start mon3.py
timestamp=$(date '+%Y%m%d%H%M%S')
logfile="systemd_${systemd}_${n_cont}.json"
sudo /home/ec2-user/mon3.py $logfile >/dev/null &
echo "started monitoring on $logfile"

sleep 10

echo "starting containers"
BUNDLE="/home/ec2-user/load/bundle/"
for i in $(seq 1 "$n_cont"); do
    if [ "$systemd" == "on" ]; then
        sudo $rt -systemd-cgroup \
            run -bundle $BUNDLE -detach "container_$i" &
    else
        sudo $rt \
            run -bundle $BUNDLE -detach "container_$i" &
    fi
    echo "started container_$i/$n_cont"
done

# Loop until the number of running containers equals $n_cont
while true; do
    running_count=$(sudo $rt list | grep -c running)
    if [ "$running_count" -eq "$n_cont" ]; then
        break
    fi
    sleep 1
    echo "Waiting for all containers to start..."
done

echo "spun up all $n_cont containers"

sleep 20 # let them run for 20s

echo "spinning down containers"

# Kill all running containers
running_ids=$(sudo $rt list | awk 'NR>1 && $3=="running" {print $1}')
if [ -n "$running_ids" ]; then
    echo "$running_ids" | xargs -n1 -I{} sudo $rt kill {} KILL
    echo "killed all running containers"
else
    echo "no running containers to kill"
fi

sleep 1

# Delete all stopped containers
stopped_ids=$(sudo $rt list | awk 'NR>1 && $3=="stopped" {print $1}')
if [ -n "$stopped_ids" ]; then
    echo "$stopped_ids" | xargs -n1 sudo $rt delete
    echo "deleted all stopped containers"
else
    echo "no stopped containers to delete"
fi


# kill the of the mon3.py to stop writing
echo "wrote results to $logfile"

# Kill the process started by mon3.py
mon3_pid=$(pgrep -f "/home/ec2-user/mon3.py")
if [ -n "$mon3_pid" ]; then
    echo "$mon3_pid" | xargs sudo kill -SIGINT
    echo "Stopped mon3.py processes"
else
    echo "No mon3.py process found to stop"
fi

