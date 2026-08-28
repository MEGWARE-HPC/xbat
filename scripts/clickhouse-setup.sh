#!/bin/bash
# Script to generate ClickHouse user configuration from xbat.conf

source <(/usr/local/share/xbat/conf-to-env.sh --stdout)

if [[ ! -d "/etc/xbat/clickhouse" ]]; then
    echo "Warning: /etc/xbat/clickhouse not found, assuming no-db option. Skipping ClickHouse configuration." >&2
    exit 0
fi

USER_IN_FILE="/etc/xbat/clickhouse/users/users.xml.in"
USER_OUT_FILE="/etc/xbat/clickhouse/users/users.xml"

if [[ -f "$USER_IN_FILE" ]]; then
    sed -e "s/#PASSWORD#/${CLICKHOUSE_PASSWORD}/g" \
        -e "s/#DAEMON_PASSWORD#/${CLICKHOUSE_DAEMON_PASSWORD}/g" \
        "$USER_IN_FILE" > "$USER_OUT_FILE"
    
    echo "ClickHouse user configuration written to $USER_OUT_FILE"
else
    echo "Error: ClickHouse user template file $USER_IN_FILE does not exist." >&2
    exit 1
fi