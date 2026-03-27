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
host=${CLICKHOUSE_EXTERNAL_HOST}
port=${CLICKHOUSE_DAEMON_PORT}
database=${CLICKHOUSE_DATABASE}
user=${CLICKHOUSE_DAEMON_USER}
password=${CLICKHOUSE_DAEMON_PASSWORD}
EOF
)

output_path="/etc/xbat/xbatd.conf"
output_dir="$(dirname "$output_path")"

if [[ $use_stdout -eq 1 ]]; then
  echo "$config_contents"
else
  mkdir -p -m 0700 "$output_dir"
  echo "$config_contents" > "$output_path"
  echo "Configuration written to $output_path"
  echo "Tip: Use --stdout to print to standard output instead."
fi
