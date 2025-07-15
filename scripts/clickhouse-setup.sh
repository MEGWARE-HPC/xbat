#!/bin/bash
# Script to generate ClickHouse user configuration from xbat.conf

source <(/usr/local/share/xbat/conf-to-env.sh --stdout)

USER_IN_FILE="/etc/xbat/clickhouse/users/users.xml.in"
USER_OUT_FILE="/etc/xbat/clickhouse/users/users.xml"
MIGRATE_SCRIPT="/usr/local/share/xbat/clickhouse/migrate.sh"

# Function to check for pending migrations
check_pending_migrations() {
    echo "Checking for pending database migrations..."
    
    if [[ ! -f "$MIGRATE_SCRIPT" ]]; then
        echo "Error: Migration script not found at $MIGRATE_SCRIPT" >&2
        exit 1
    fi
    
    # Run migration status and capture output
    local migration_output
    if migration_output=$("$MIGRATE_SCRIPT" status 2>&1); then
        # Check if there are any pending migrations
        if echo "$migration_output" | grep -q "Pending"; then
            echo >&2
            echo "ERROR: Pending database migrations detected!" >&2
            echo "Migration status:" >&2
            echo "$migration_output" >&2
            echo >&2
            echo "You must apply pending migrations before setting up ClickHouse users." >&2
            echo "Run the following command to upgrade the database:" >&2
            echo "  sudo /usr/local/share/xbat/setup.sh migrate up" >&2
            echo >&2
            echo "Or check migration status with:" >&2
            echo "  sudo /usr/local/share/xbat/setup.sh migrate status" >&2
            return 1
        else
            echo "✓ Database is up to date - no pending migrations"
        fi
    else
        echo "Error: Could not check migration status (database may not be running)" >&2
        echo -e "Migration output:\n$migration_output" >&2
        return 1
    fi
}


# Check for pending migrations first
check_pending_migrations

if [[ -f "$USER_IN_FILE" ]]; then
    sed -e "s/#PASSWORD#/${CLICKHOUSE_PASSWORD}/g" \
        -e "s/#DAEMON_PASSWORD#/${CLICKHOUSE_DAEMON_PASSWORD}/g" \
        "$USER_IN_FILE" > "$USER_OUT_FILE"
    
    echo "ClickHouse user configuration written to $USER_OUT_FILE"
else
    echo "Error: ClickHouse user template file $USER_IN_FILE does not exist." >&2
    exit 1
fi