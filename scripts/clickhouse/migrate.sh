#!/bin/bash

set -euo pipefail

INSTALL_DIR="/usr/local/share/xbat/bin"
GOOSE_BINARY="$INSTALL_DIR/goose"

# fail if install directory doesn't exist
if [[ ! -d "$INSTALL_DIR" ]]; then
    echo "Install directory $INSTALL_DIR does not exist. Aborting migration." >&2
    exit 1
fi

# install goose if not already present
if [[ ! -x "$GOOSE_BINARY" ]]; then
    curl -fsSL https://raw.githubusercontent.com/pressly/goose/master/install.sh | \
        GOOSE_INSTALL="$INSTALL_DIR" sh

    if [[ ! -x "$GOOSE_BINARY" ]]; then
        echo "Failed to install goose to $GOOSE_BINARY" >&2
        exit 1
    fi
fi

source <(/usr/local/share/xbat/conf-to-env.sh --stdout)

required_vars=(
  CLICKHOUSE_USER
  CLICKHOUSE_PASSWORD
  CLICKHOUSE_HOST
  CLICKHOUSE_DATABASE
)

missing=0
for var in "${required_vars[@]}"; do
  if [[ -z "${!var:-}" ]]; then
    suffix="${var#CLICKHOUSE_}"
    echo "Clickhouse '${suffix,,}' is not set or empty in /etc/xbat/xbat.conf" >&2
    missing=1
  fi
done

if [[ $missing -eq 1 ]]; then
  exit 1
fi

CLICKHOUSE_PORT=9000
GOOSE_DRIVER=clickhouse

GOOSE_DBSTRING="clickhouse://$CLICKHOUSE_USER:$CLICKHOUSE_PASSWORD@$CLICKHOUSE_HOST:$CLICKHOUSE_PORT/$CLICKHOUSE_DATABASE"
GOOSE_MIGRATIONS_DIR="/usr/local/share/xbat/migrations/"

goose clickhouse -dir "${GOOSE_MIGRATIONS_DIR}" "${GOOSE_DBSTRING}" "$@"