#!/bin/bash
RUN_DIR="$1"
PIPE_NAME="$2"
PIPE="${RUN_DIR}/${PIPE_NAME}"

while [ -p "$PIPE" ]; do
    while IFS= read -r input; do
        ident=$(echo "$input" | cut -d ";" -f 1)
        command=$(echo "$input" | cut -d ";" -f 2)
        if [ -z "$ident" ] || [ -z "$command" ]; then
            continue
        fi
        file="${RUN_DIR}/${ident}"
        eval "$command" 1>"${file}_stdout" 2>"${file}_stderr"
        echo "$?" > "${file}_ret"
    done < "$PIPE"
done
