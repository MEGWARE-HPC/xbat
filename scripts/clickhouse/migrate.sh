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

GOOSE_DRIVER=clickhouse

CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=changeme
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=9000
CLICKHOUSE_DATABASE=xbat

GOOSE_DBSTRING="clickhouse://$CLICKHOUSE_USER:$CLICKHOUSE_PASSWORD@$CLICKHOUSE_HOST:$CLICKHOUSE_PORT/$CLICKHOUSE_DATABASE"