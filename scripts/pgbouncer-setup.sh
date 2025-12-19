#!/bin/bash

# pgbouncer.ini and userlists.txt are generated from the xbat.conf file
# this avoids setting the same credentials in multiple places

INPUT_FILE="/etc/xbat/xbat.conf"
OUTPUT_IN_FILE="/etc/xbat/pgbouncer.ini.in"
OUTPUT_FILE="/etc/xbat/pgbouncer.ini"
USERLISTS_FILE="/etc/xbat/userlists.txt"

# Extract user and group from the OUTPUT_IN_FILE
USER=$(ls -al "$OUTPUT_IN_FILE" | awk '{print $3}')
GROUP=$(ls -al "$OUTPUT_IN_FILE" | awk '{print $4}')

cp "$OUTPUT_IN_FILE" "$OUTPUT_FILE" && chown "${USER}:${GROUP}" "$OUTPUT_FILE" && chmod 640 "$OUTPUT_FILE"

clickhouse_host=$(awk -F'=' '/\[clickhouse\]/ {flag=1; next} /^host/ && flag {print $2; flag=0}' "$INPUT_FILE" | xargs)
clickhouse_port=$(awk -F'=' '/\[clickhouse\]/ {flag=1; next} /^port/ && flag {print $2; flag=0}' "$INPUT_FILE" | xargs)
clickhouse_database=$(awk -F'=' '/\[clickhouse\]/ {flag=1; next} /^database/ && flag {print $2; flag=0}' "$INPUT_FILE" | xargs)
clickhouse_user=$(awk -F'=' '/\[clickhouse\]/ {flag=1; next} /^user/ && flag {print $2; flag=0}' "$INPUT_FILE" | xargs)
clickhouse_password=$(awk -F'=' '/\[clickhouse\]/ {flag=1; next} /^password/ && flag {print $2; flag=0}' "$INPUT_FILE" | xargs)

# Replace placeholders in the [databases] section of the OUTPUT_FILE
sed -i "s/#HOST#/$clickhouse_host/" "$OUTPUT_FILE"
sed -i "s/#PORT#/$clickhouse_port/" "$OUTPUT_FILE"
sed -i "s/#DATABASE#/$clickhouse_database/" "$OUTPUT_FILE"
sed -i "s/#USER#/$clickhouse_user/" "$OUTPUT_FILE"
sed -i "s/#PASSWORD#/$clickhouse_password/" "$OUTPUT_FILE"

pgb_user=$(awk -F'=' '/\[pgbouncer\]/ {flag=1; next} /^user/ && flag {print $2; flag=0}' "$INPUT_FILE" | xargs)
pgb_password=$(awk -F'=' '/\[pgbouncer\]/ {flag=1; next} /^password/ && flag {print $2; flag=0}' "$INPUT_FILE" | xargs)

# Create/overwrite the USERLISTS_FILE with user credentials
echo "\"$pgb_user\" \"$pgb_password\"" > "$USERLISTS_FILE" && chown "${USER}:${GROUP}" "$USERLISTS_FILE" && chmod 640 "$USERLISTS_FILE"