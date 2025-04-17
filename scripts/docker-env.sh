#!/bin/bash
# Extracts values from /etc/xbat/xbat.conf and saves them as environment variables

CONFIG_FILE="/etc/xbat/xbat.conf"
ENV_FILE="/etc/xbat/docker-compose.env"

# Ensure the environment file exists
touch "$ENV_FILE"
chmod 644 "$ENV_FILE"

# Extract values from the [demo] section
awk -F= '
    /^\[demo\]/ {found=1; next} 
    /^\[/ {found=0} 
    found && /^[a-zA-Z]/ {
        key=$1; value=$2;
        gsub(/[ \t\r\n]+$/, "", key);  # Trim trailing spaces
        gsub(/^[ \t\r\n]+/, "", key);  # Trim leading spaces
        gsub(/[ \t\r\n]+$/, "", value);  # Trim trailing spaces
        gsub(/^[ \t\r\n]+/, "", value);  # Trim leading spaces
        print "DEMO_"toupper(key) "=" value;
    }
' "$CONFIG_FILE" > "$ENV_FILE"

# Reload systemd to pick up changes
systemctl daemon-reexec
