#!/bin/bash

# Validates all required variables and warns about default/insecure values

set -euo pipefail

source <(/usr/local/share/xbat/conf-to-env.sh --stdout)

# Color codes for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

CONF_PATH="/etc/xbat/xbat.conf"

# Counters
errors=0
warnings=0

print_section() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

print_error() {
    echo -e "${RED}ERROR: $1${NC}" >&2
    ((errors++))
}

print_warning() {
    echo -e "${YELLOW}WARNING: $1${NC}" >&2
    ((warnings++))
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Check if a configuration key exists in the config file
check_config_key_exists() {
    local section="$1"
    local key="$2"
    local config_file="${CONF_PATH}"
    
    # Use awk to check if the key exists in the specified section
    local exists=$(awk -v section="[$section]" -v key="$key" '
        BEGIN { in_section = 0; found = 0 }
        /^\[.*\]$/ { 
            in_section = ($0 == section) ? 1 : 0 
        }
        in_section && /^[[:space:]]*[^#\[]/ {
            if (match($0, "^[[:space:]]*" key "[[:space:]]*=")) {
                found = 1
                exit
            }
        }
        END { print found }
    ' "$config_file")
    
    return $((1 - exists))  # Return 0 if found, 1 if not found
}

# Check if a configuration section exists in the config file
check_section_exists() {
    local section="$1"
    local config_file="${CONF_PATH}"
    
    if grep -q "^\[${section}\]" "$config_file"; then
        return 0
    else
        print_error "Section [$section] is missing from configuration file ${CONF_PATH}"
        return 1
    fi
}

check_required_var() {
    local var_name="$1"
    local section="${2:-}"
    local display_name="${3:-}"
    
    # Auto-deduce section and display_name if not provided
    if [[ -z "$section" ]]; then
        section="${var_name%%_*}"
        section="${section,,}" # convert to lowercase
    fi
    
    if [[ -z "$display_name" ]]; then
        display_name="${var_name#*_}"
        display_name="${display_name,,}" # convert to lowercase
    fi
    
    # First check if the config key exists in the file
    if ! check_config_key_exists "$section" "$display_name"; then
        print_error "[$section] '$display_name' is missing from configuration file - add it to ${CONF_PATH}"
        return 1
    fi
    
    # Then check if it's set to a value
    if [[ -z "${!var_name:-}" ]]; then
        print_error "[$section] '$display_name' is not set or empty"
        return 1
    fi
    return 0
}

check_optional_var() {
    local var_name="$1"
    local section="${2:-}"
    local display_name="${3:-}"
    
    # Auto-deduce section and display_name if not provided
    if [[ -z "$section" ]]; then
        section="${var_name%%_*}"
        section="${section,,}" # convert to lowercase
    fi
    
    if [[ -z "$display_name" ]]; then
        display_name="${var_name#*_}"
        display_name="${display_name,,}" # convert to lowercase
    fi
    
    # First check if the config key exists in the file
    if ! check_config_key_exists "$section" "$display_name"; then
        print_warning "[$section] '$display_name' is missing from configuration file (optional) - consider adding it to ${CONF_PATH}"
        return 1
    fi
    
    # Then check if it's set to a value
    if [[ -z "${!var_name:-}" ]]; then
        print_warning "[$section] '$display_name' is not set (optional)"
        return 1
    fi
    return 0
}

check_default_value() {
    local var_name="$1"
    local default_value="$2"
    local message="${3:-contains default value and should be changed}"
    local section="${4:-}"
    local display_name="${5:-}"
    
    # Auto-deduce section and display_name if not provided
    if [[ -z "$section" ]]; then
        section="${var_name%%_*}"
        section="${section,,}" # convert to lowercase
    fi
    
    if [[ -z "$display_name" ]]; then
        display_name="${var_name#*_}"
        display_name="${display_name,,}" # convert to lowercase
    fi
    
    if [[ "${!var_name:-}" == "$default_value" ]]; then
        print_warning "[$section] '$display_name' $message"
        return 1
    fi
    return 0
}

check_infrastructure_value() {
    local var_name="$1"
    local infra_value="$2"
    local message="${3:-has been changed from infrastructure default - ensure this is intentional}"
    local section="${4:-}"
    local display_name="${5:-}"
    
    # Auto-deduce section and display_name if not provided
    if [[ -z "$section" ]]; then
        section="${var_name%%_*}"
        section="${section,,}" # convert to lowercase
    fi
    
    if [[ -z "$display_name" ]]; then
        display_name="${var_name#*_}"
        display_name="${display_name,,}" # convert to lowercase
    fi
    
    if [[ "${!var_name:-}" != "$infra_value" ]]; then
        print_warning "[$section] '$display_name' $message"
        return 1
    fi
    return 0
}

check_optional_with_default() {
    local var_name="$1"
    local default_value="$2"
    local section="${3:-}"
    local display_name="${4:-}"
    
    # Auto-deduce section and display_name if not provided
    if [[ -z "$section" ]]; then
        section="${var_name%%_*}"
        section="${section,,}" # convert to lowercase
    fi
    
    if [[ -z "$display_name" ]]; then
        display_name="${var_name#*_}"
        display_name="${display_name,,}" # convert to lowercase
    fi
    
    # First check if the config key exists in the file
    if ! check_config_key_exists "$section" "$display_name"; then
        print_warning "[$section] '$display_name' is missing from configuration file, will default to '$default_value' - consider adding it to ${CONF_PATH}"
        return 1
    fi
    
    # Then check if it's set to a value
    if [[ -z "${!var_name:-}" ]]; then
        print_warning "[$section] '$display_name' is not set, will default to '$default_value'"
        return 1
    fi
    return 0
}

validate_general_section() {
    print_section "General Configuration"
    
    # First check if the section exists
    check_section_exists "general" || return 1
    
    check_required_var "GENERAL_LOG_LEVEL" && print_success "log_level is set"
    check_optional_with_default "GENERAL_CLI_INTERVAL" "5" && print_success "cli_interval is set"
    
    # Validate log level values
    if [[ -n "${GENERAL_LOG_LEVEL:-}" ]]; then
        case "${GENERAL_LOG_LEVEL}" in
            debug|info|warning|error)
                print_success "log_level has valid value: ${GENERAL_LOG_LEVEL}"
                ;;
            *)
                print_warning "[general] log_level '${GENERAL_LOG_LEVEL}' is not a standard value (debug|info|warning|error)"
                ;;
        esac
    fi
    
    # Validate CLI interval
    if [[ -n "${GENERAL_CLI_INTERVAL:-}" ]]; then
        if [[ "${GENERAL_CLI_INTERVAL}" -lt 5 ]]; then
            print_warning "[general] cli_interval '${GENERAL_CLI_INTERVAL}' is below minimum recommended value of 5 seconds"
        fi
    fi
}

validate_mongodb_section() {
    print_section "MongoDB Configuration"
    
    check_section_exists "mongodb" || return 1
    
    check_required_var "MONGODB_ADDRESS" && print_success "address is set"
    check_required_var "MONGODB_DATABASE" && print_success "database is set"
    check_required_var "MONGODB_USER" && print_success "user is set"
    check_required_var "MONGODB_PASSWORD" && print_success "password is set"
    
    check_default_value "MONGODB_PASSWORD" "changeme" "uses default password 'changeme' - security risk!"
    
    check_infrastructure_value "MONGODB_ADDRESS" "mongodb://xbat-mongodb:27017" "has been changed from docker-compose default - only change this value if you are deploying with --no-db"
    check_infrastructure_value "MONGODB_DATABASE" "xbat" "has been changed from default database name"
    check_infrastructure_value "MONGODB_USER" "xbat" "has been changed from default user name"
}

validate_restapi_section() {
    print_section "REST API Configuration"
    
    check_section_exists "restapi" || return 1
    
    check_required_var "RESTAPI_HOST" && print_success "host is set"
    check_required_var "RESTAPI_PORT" && print_success "port is set"
    check_required_var "RESTAPI_CLIENT_ID" && print_success "client_id is set"
    check_required_var "RESTAPI_CLIENT_SECRET" && print_success "client_secret is set"
    
    check_default_value "RESTAPI_HOST" "changeme" "must be replaced with a valid hostname or IP that is accessible for the xbatd"
    check_default_value "RESTAPI_CLIENT_SECRET" "changeme" "must be replaced with the secret configured in MongoDB for the xbatd user"
}


validate_clickhouse_section() {
    print_section "ClickHouse Configuration"

    check_section_exists "clickhouse" || return 1

    check_required_var "CLICKHOUSE_HOST" && print_success "host is set"
    check_required_var "CLICKHOUSE_EXTERNAL_HOST" && print_success "external_host is set"
    check_required_var "CLICKHOUSE_PORT" && print_success "port is set"
    check_required_var "CLICKHOUSE_DAEMON_PORT" && print_success "daemon_port is set"
    check_required_var "CLICKHOUSE_DATABASE" && print_success "database is set"
    check_required_var "CLICKHOUSE_USER" && print_success "user is set"
    check_required_var "CLICKHOUSE_PASSWORD" && print_success "password is set"
    check_required_var "CLICKHOUSE_DAEMON_PASSWORD" && print_success "daemon_password is set"
    check_required_var "CLICKHOUSE_DAEMON_USER" && print_success "daemon_user is set"
    
    # Check for default values that need to be changed
    check_default_value "CLICKHOUSE_PASSWORD" "changeme" "uses default password 'changeme'"
    check_default_value "CLICKHOUSE_DAEMON_PASSWORD" "changeme" "uses default daemon password 'changeme'"
    check_default_value "CLICKHOUSE_EXTERNAL_HOST" "changeme" "must be changed to a valid external hostname or IP that is accessible for the xbatd"

    check_infrastructure_value "CLICKHOUSE_HOST" "xbat-clickhouse" "has been changed from docker-compose default - only change this value if you are deploying with --no-db"
    check_infrastructure_value "CLICKHOUSE_PORT" "9005" "has been changed from docker-compose default port - only change this value if you are deploying with --no-db"
    check_infrastructure_value "CLICKHOUSE_USER" "xbat" "has been changed from default user name"
    check_infrastructure_value "CLICKHOUSE_DAEMON_USER" "xbatd" "has been changed from default daemon user name"
    check_infrastructure_value "CLICKHOUSE_DATABASE" "xbat" "has been changed from default database name"
    check_infrastructure_value "CLICKHOUSE_DAEMON_PORT" "9000" "has been changed from default daemon port (9000)"
}

validate_pgbouncer_section() {
    print_section "PgBouncer Configuration"

    check_section_exists "pgbouncer" || return 1

    check_required_var "PGBOUNCER_HOST" && print_success "host is set"
    check_required_var "PGBOUNCER_PORT" && print_success "port is set"
    check_required_var "PGBOUNCER_DATABASE" && print_success "database is set"
    check_required_var "PGBOUNCER_USER" && print_success "user is set"
    check_required_var "PGBOUNCER_PASSWORD" && print_success "password is set"
    
    check_infrastructure_value "PGBOUNCER_HOST" "xbat-pgbouncer" "must not be changed (default 'xbat-pgbouncer')"
    check_infrastructure_value "PGBOUNCER_PORT" "6432" "must not be changed (default '6432')"

    # PgBouncer database must match ClickHouse database
    if [[ -n "${PGBOUNCER_DATABASE:-}" && -n "${CLICKHOUSE_DATABASE:-}" ]]; then
        if [[ "${PGBOUNCER_DATABASE}" != "${CLICKHOUSE_DATABASE}" ]]; then
            print_error "[pgbouncer] database '${PGBOUNCER_DATABASE}' does not match ClickHouse database '${CLICKHOUSE_DATABASE}' - they must be the same"
        else
            print_success "pgbouncer database matches ClickHouse database"
        fi
    fi
}

validate_valkey_section() {
    print_section "Valkey Configuration"

    check_section_exists "valkey" || return 1

    check_required_var "VALKEY_HOST" && print_success "host is set"
    check_required_var "VALKEY_PORT" && print_success "port is set"
    check_required_var "VALKEY_DATABASE" && print_success "database is set"
    
    check_infrastructure_value "VALKEY_HOST" "xbat-valkey" "has been changed from docker-compose default - ensure this is correct for your setup"
    check_infrastructure_value "VALKEY_PORT" "6379" "has been changed from default port '6379'"
    check_infrastructure_value "VALKEY_DATABASE" "0" "has been changed from default database '0'"
}

validate_authentication_section() {
    print_section "Authentication Configuration"

    check_section_exists "authentication" || return 1
    
    check_required_var "AUTHENTICATION_PROVIDER" && print_success "provider is set"
    
    # Check provider-specific requirements
    if [[ -n "${AUTHENTICATION_PROVIDER:-}" ]]; then
        case "${AUTHENTICATION_PROVIDER}" in
            pam)
                print_success "authentication provider 'pam' - no additional config required"
                ;;
            ldap)
                check_required_var "AUTHENTICATION_ADDRESS" && print_success "LDAP address is set"
                check_required_var "AUTHENTICATION_BASEDN" && print_success "LDAP basedn is set"
                check_required_var "AUTHENTICATION_USER_IDENTIFIER" && print_success "LDAP user_identifier is set"
                ;;
            ipa)
                check_required_var "AUTHENTICATION_ADDRESS" && print_success "IPA address is set"
                check_optional_var "AUTHENTICATION_VERIFY_SSL"
                ;;
            *)
                print_error "[authentication] provider '${AUTHENTICATION_PROVIDER}' is not supported (pam|ipa|ldap)"
                ;;
        esac
    fi
}

validate_demo_section() {
    print_section "Demo Configuration"
    
    check_required_var "DEMO_ENABLED" && print_success "enabled is set"
    
    if [[ "${DEMO_ENABLED:-}" == "true" ]]; then
        check_required_var "DEMO_USER" && print_success "demo user is set"
        check_required_var "DEMO_PASSWORD" && print_success "demo password is set"
        
        print_warning "[demo] Demo mode is enabled - should be disabled in production!"
    else
        print_success "demo mode is disabled"
    fi
}


main() {
    echo -e "${BLUE}xbat Configuration Validation${NC}"
    echo "Configuration file: ${CONF_PATH}"
    echo "================================================"
    
    validate_general_section || true
    validate_mongodb_section || true
    validate_restapi_section || true
    validate_clickhouse_section || true
    validate_pgbouncer_section || true
    validate_valkey_section || true
    validate_authentication_section || true
    validate_demo_section || true
    
    echo
    echo "================================================"
    echo -e "${BLUE}Validation Summary${NC}"
    
    if [[ $errors -eq 0 ]]; then
        print_success "All required variables are present"
    else
        print_error "Found $errors missing required or misconfigured variables"
    fi
    
    if [[ $warnings -gt 0 ]]; then
        echo -e "${YELLOW}Found $warnings warnings${NC}"
    fi
    
    echo
    if [[ $errors -eq 0 ]]; then
        echo -e "${GREEN}✓ Configuration validation passed${NC}"
        exit 0
    else
        echo -e "${RED}✗ Configuration validation failed${NC}"
        exit 1
    fi
}

# Run main function
main "$@"

