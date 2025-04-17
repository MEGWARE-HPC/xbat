#!/bin/bash

RUN_DIR="/run/xbat"
PIPE_BASE_NAME="host-pipe-"
PIPE_SCRIPT_PIDS="${RUN_DIR}/pipes.pid"

# pipe processes killed by systemd

if [ -d "$RUN_DIR" ]; then
    cd "$RUN_DIR" || exit 0
    ls | grep "$PIPE_BASE_NAME" | while read -r pipe; do
        echo "Removing $pipe"
        rm -f "$pipe"
    done
fi






