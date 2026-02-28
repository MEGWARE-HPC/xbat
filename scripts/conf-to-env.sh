#!/bin/bash
# Extracts values from /etc/xbat/xbat.conf and saves them as environment variables or prints to stdout

CONFIG_FILE="/etc/xbat/xbat.conf"
ENV_FILE="/etc/xbat/docker-compose.env"
OUTPUT_MODE="file"

if [[ "${1:-}" == "--stdout" ]]; then
    OUTPUT_MODE="stdout"
else
    # Ensure the environment file exists
    touch "$ENV_FILE"
    chmod 644 "$ENV_FILE"
    : > "$ENV_FILE"  # clear previous content
fi

# Extract values of all sections
current_section=""
while IFS= read -r line || [[ -n "$line" ]]; do
    # Strip leading/trailing whitespace
    line="$(echo "$line" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"

    # Skip empty lines and comments
    [[ -z "$line" || "$line" =~ ^# ]] && continue

    # Match section headers
    if [[ "$line" =~ ^\[(.*)\]$ ]]; then
        current_section="${BASH_REMATCH[1]}"
        current_section_upper=$(echo "$current_section" | tr '[:lower:]' '[:upper:]')
        continue
    fi

    # Match key=value pairs
    if [[ "$line" =~ ^([a-zA-Z0-9_]+)[[:space:]]*=[[:space:]]*(.*)$ ]]; then
        key="${BASH_REMATCH[1]}"
        value="${BASH_REMATCH[2]}"
        key_upper=$(echo "$key" | tr '[:lower:]' '[:upper:]')
        varname="${current_section_upper}_${key_upper}"

        if [[ "$OUTPUT_MODE" == "stdout" ]]; then
            echo "${varname}=${value}"
        else
            echo "${varname}=${value}" >> "$ENV_FILE"
        fi
    fi
done < "$CONFIG_FILE"