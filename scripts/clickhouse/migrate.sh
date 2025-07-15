#!/bin/bash

set -euo pipefail

INSTALL_DIR="/usr/local/share/xbat/clickhouse"
GOOSE_BINARY="$INSTALL_DIR/bin/goose" # bin is automatically created by goose install script

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

# Migration script is running outside of docker infrastructure and has no access to xbat-clickhouse host.
# If the host is set to xbat-clickhouse, assume clickhouse is reachable via localhost. Host different from xbat-clickhouse
# is expected to be a real host on a different server.
if [[ "$CLICKHOUSE_HOST" == "xbat-clickhouse" ]]; then
    CLICKHOUSE_HOST="localhost"
fi

CLICKHOUSE_PORT=9000
GOOSE_DRIVER=clickhouse

GOOSE_DBSTRING="clickhouse://${CLICKHOUSE_USER}:${CLICKHOUSE_PASSWORD}@${CLICKHOUSE_HOST}:${CLICKHOUSE_PORT}/${CLICKHOUSE_DATABASE}"
GOOSE_MIGRATIONS_DIR="/usr/local/share/xbat/clickhouse/migrations/"

"$GOOSE_BINARY" clickhouse -dir "$GOOSE_MIGRATIONS_DIR" "$GOOSE_DBSTRING" "$@"