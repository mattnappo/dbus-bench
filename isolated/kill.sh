#!/bin/bash

rt=runsc

# Kill all running containers
running_ids=$(sudo $rt list | awk 'NR>1 && $3=="running" {print $1}')
if [ -n "$running_ids" ]; then
    echo "$running_ids" | xargs -n1 -I{} sudo $rt kill {} KILL
    echo "Killed all running containers"
else
    echo "No running containers to kill"
fi

sleep 1

# Delete all stopped containers
stopped_ids=$(sudo $rt list | awk 'NR>1 && $3=="stopped" {print $1}')
if [ -n "$stopped_ids" ]; then
    echo "$stopped_ids" | xargs -n1 sudo $rt delete
    echo "Deleted all stopped containers"
else
    echo "No stopped containers to delete"
fi

