#!/bin/bash

RUN_DIR="/run/xbat"
PIPE_BASE_NAME="host-pipe"

mkdir -m 0700 -p "$RUN_DIR"

for ((i=0; i<$PIPE_POOLSIZE; i++))
do
    pipe_name="${PIPE_BASE_NAME}-xbatctld-${i}"
    pipe="${RUN_DIR}/${pipe_name}"
    echo "CREATING $pipe"
    if [ -p "$pipe" ]; then
        rm -f "$pipe"
    fi
    mkfifo -m 0600 "$pipe"
    /usr/local/share/xbat/pipe.sh "$RUN_DIR" "$pipe_name"  &
done
