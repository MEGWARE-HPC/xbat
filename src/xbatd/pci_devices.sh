#!/bin/bash

classes=("0108" "0207" "0300" "0302" "0380")

temp_file=$(mktemp)

for class in "${classes[@]}"; do
  lspci -d ::"${class}" -vvnn | grep -E "\[${class}\]:" | while read -r line; do
    if [[ "$line" == *"NVIDIA Corporation"* ]]; then
      vendor="NVIDIA"
      model=$(echo "$line" | grep -oP '(?<=NVIDIA Corporation ).*?\[.*?\]')
      echo "$vendor, $model" >> "$temp_file"
    elif [[ "$line" == *"Advanced Micro Devices"* ]]; then
      vendor="AMD"
      model=$(echo "$line" | grep -oP '(?<=\] ).*?(?= \[.*?\])')
      echo "$vendor $model" >> "$temp_file"
    fi
  done
done

# count identical devices
sort "$temp_file" | uniq -c | while read -r count device; do
  echo "${count}x $device"
done

rm "$temp_file"
