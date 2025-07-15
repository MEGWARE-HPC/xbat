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
user=${CLICKHOUSE_DAEMON_USER}
password=${CLICKHOUSE_DAEMON_PASSWORD}
EOF
)

if [[ $use_stdout -eq 1 ]]; then
  echo "$config_contents"
else
  output_path="/etc/xbat/xbatd.conf"
  echo "$config_contents" > "$output_path"
  echo "Configuration written to $output_path"
fi
