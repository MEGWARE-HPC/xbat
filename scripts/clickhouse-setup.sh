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
        echo "Warning: Migration script not found at $MIGRATE_SCRIPT"
        exit 1
    fi
    
    # Run migration status and capture output
    local migration_output
    if migration_output=$("$MIGRATE_SCRIPT" status 2>&1); then
        # Check if there are any pending migrations
        if echo "$migration_output" | grep -q "Pending"; then
            echo
            echo "ERROR: Pending database migrations detected!"
            echo "Migration status:"
            echo "$migration_output"
            echo
            echo "You must apply pending migrations before setting up ClickHouse users."
            echo "Run the following command to upgrade the database:"
            echo "  sudo /usr/local/share/xbat/setup.sh migrate up"
            echo
            echo "Or check migration status with:"
            echo "  sudo /usr/local/share/xbat/setup.sh migrate status"
            echo
            exit 1
        else
            echo "✓ Database is up to date - no pending migrations"
        fi
    else
        echo "Warning: Could not check migration status (database may not be running)"
        echo "Migration output: $migration_output"
        exit 1
    fi
}


if [[ -f "$USER_IN_FILE" ]]; then
    sed -e "s/#PASSWORD#/${CLICKHOUSE_PASSWORD}/g" \
        -e "s/#DAEMON_PASSWORD#/${CLICKHOUSE_DAEMON_PASSWORD}/g" \
        "$USER_IN_FILE" > "$USER_OUT_FILE"
    
    echo "ClickHouse user configuration written to $USER_OUT_FILE"
else
    echo "Error: ClickHouse user template file $USER_IN_FILE does not exist." >&2
    exit 1
fi

# Check for pending migrations first
check_pending_migrations