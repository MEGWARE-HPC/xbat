#!/bin/bash

source <(/usr/local/share/xbat/conf-to-env.sh --stdout)

# Check for optional --stdout flag
use_stdout=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --stdout)
      use_stdout=1
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

required_vars=(
  RESTAPI_HOST
  RESTAPI_PORT
  RESTAPI_CLIENT_ID
  RESTAPI_CLIENT_SECRET
  CLICKHOUSE_HOST
  CLICKHOUSE_PORT
  CLICKHOUSE_DATABASE
  CLICKHOUSE_USER
  CLICKHOUSE_PASSWORD
)

missing=0
for var in "${required_vars[@]}"; do
  if [[ -z "${!var:-}" ]]; then
    prefix="${var%%_*}"
    suffix="${var#${prefix}_}"
    case "$prefix" in
      CLICKHOUSE)
        echo "Clickhouse '${suffix,,}' is not set or empty in /etc/xbat/xbat.conf" >&2
        ;;
      RESTAPI)
        echo "REST API '${suffix,,}' is not set or empty in /etc/xbat/xbat.conf" >&2
        ;;
      *)
        echo "Unknown config '${var}' is not set or empty in /etc/xbat/xbat.conf" >&2
        ;;
    esac
    missing=1
  fi
done

if [[ $missing -eq 1 ]]; then
  exit 1
fi

config_contents=$(cat <<EOF
# Auto-generated configuration file for xbatd from /etc/xbat/xbat.conf
[general]
# [debug|info|warning|error]
log_level = info
log_level_file = debug

[restapi]
host=${RESTAPI_HOST}
port=${RESTAPI_PORT}
client_id=${RESTAPI_CLIENT_ID}
client_secret=${RESTAPI_CLIENT_SECRET}

[clickhouse]
host=${CLICKHOUSE_HOST}
port=${CLICKHOUSE_PORT}
database=${CLICKHOUSE_DATABASE}
user=${CLICKHOUSE_USER}
password=${CLICKHOUSE_PASSWORD}
EOF
)

if [[ $use_stdout -eq 1 ]]; then
  echo "$config_contents"
else
  output_path="/etc/xbat/xbatd.conf"
  echo "$config_contents" > "$output_path"
  echo "Configuration written to $output_path"
fi
