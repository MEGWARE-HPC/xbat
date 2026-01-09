#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

# trap cleanup EXIT INT TERM

#########################################
# Constants and Defaults                # 
#########################################

INSTALL_PATH="/usr/local/share/xbat"
SERVICE_DEST_PATH="/etc/systemd/system"
SERVICE_NAME="xbat.service"
BUILD_PATH="build"
CONF_DEST_PATH="/etc/xbat"
LOG_BASE_PATH="/var/log/xbat"
LIB_BASE_PATH="/var/lib/xbat"
RUN_PATH="/run/xbat"

EXECUTOR="podman"
EXECUTOR_COMPOSE="podman-compose"

HOME_MNT=""
HELP=false
NODB=false
EXPOSE_QUESTDB=false
FRONTEND_NETWORK="0.0.0.0"
QUESTDB_ADDRESS="xbat-questdb:9000"
QUESTDB_ADDRESS_SET=false
WORKERS=8
FRONTEND_PORT=7000
XBAT_USER="xbat"
CERT_DIR="/etc/xbat/certs"

SCRIPT_SRC_PATH="./scripts"
CONF_SRC_PATH="./conf"
CONF_FILE="xbat.conf"

#########################################
# Functions                             #
#########################################

log_info() { echo -e "[INFO] $*"; }
log_warning() { echo -e "[WARNING] $*" >&2; }
log_error() { echo -e "[ERROR] $*" >&2; }

check_root() {
    if [[ "$EUID" -ne 0 ]]; then
        log_error "Root privileges are required."
        exit 1
    fi
}

create_user_if_missing() {
    if ! id "$XBAT_USER" &>/dev/null; then
        log_info "Creating user '$XBAT_USER'..."
        useradd -r -s /bin/false "$XBAT_USER"
    else
        log_info "Using existing user '$XBAT_USER'."
    fi
}

check_prerequisites() {
    local cmds=("rsync" "wget" "$EXECUTOR" "$EXECUTOR_COMPOSE")
    for cmd in "${cmds[@]}"; do
        if ! command -v "$cmd" &>/dev/null; then
            log_error "$cmd is not installed. Please install it and try again."
            exit 1
        fi
    done
}

build_docker_images() {
    log_info "Building docker images..."
    "$EXECUTOR" build -t xbat_nginx -f ./docker/nginx.dockerfile .
    "$EXECUTOR" build -t xbat_ui --ulimit nofile=4096:4096 -f ./docker/ui.dockerfile .
    "$EXECUTOR" build -t xbat_backend -f ./docker/backend.dockerfile .
    "$EXECUTOR" build -t xbat_ctld -f ./docker/xbatctld.dockerfile .
}

prepare_directories() {
    log_info "Preparing directories..."
    mkdir -p -m 0700 "$INSTALL_PATH" "$CONF_DEST_PATH" "$RUN_PATH" "$LOG_BASE_PATH" "$CERT_DIR"
    mkdir -p -m 0750 "$LIB_BASE_PATH"
    chown -R "$XBAT_USER:$XBAT_USER" "$LOG_BASE_PATH" "$LIB_BASE_PATH"
    touch "$LOG_BASE_PATH/xbat.log"
}

configure_compose() {
    log_info "Configuring docker-compose..."
    local COMPOSE_FILE="docker-compose.yml"

    if [[ -n "$HOME_MNT" ]]; then
        sed -i "s!#- HOME_MNT#!- $HOME_MNT:/external/$HOME_MNT!g" "$COMPOSE_FILE"
    fi

    sed -i "s!#FRONTEND_NETWORK#!$FRONTEND_NETWORK!g" "$COMPOSE_FILE"
    sed -i "s!#XBAT_UID#!$(id -u "$XBAT_USER")!g" "$COMPOSE_FILE"
    sed -i "s!#XBAT_GID#!$(id -g "$XBAT_USER")!g" "$COMPOSE_FILE"
    sed -i "s!#VAR_LOG#!$LOG_BASE_PATH!g" "$COMPOSE_FILE"
    sed -i "s!#VAR_LIB#!$LIB_BASE_PATH!g" "$COMPOSE_FILE"
    sed -i "s!#FRONTEND_PORT#!$FRONTEND_PORT!g" "$COMPOSE_FILE"
    sed -i "s!#CERT_DIR#!$CERT_DIR!g" "$COMPOSE_FILE"

    cp "$COMPOSE_FILE" "$INSTALL_PATH"
}

prepare_scripts_and_configs() {
    log_info "Preparing scripts and configurations..."
    cp "${SCRIPT_SRC_PATH}/pipe"*.sh "$INSTALL_PATH"
    cp "${SCRIPT_SRC_PATH}/pgbouncer-setup.sh" "$INSTALL_PATH"
    cp "${SCRIPT_SRC_PATH}/conf-to-env.sh" "$INSTALL_PATH"
    cp "${SCRIPT_SRC_PATH}/validate-config.sh" "$INSTALL_PATH"
    cp "${SCRIPT_SRC_PATH}/clickhouse-setup.sh" "$INSTALL_PATH"
    cp "${SCRIPT_SRC_PATH}/create-xbatd-conf.sh" "$INSTALL_PATH"
    cp -r "${SCRIPT_SRC_PATH}/clickhouse" "$INSTALL_PATH/"
    cp "$CONF_SRC_PATH/pgbouncer.ini.in" "$CONF_DEST_PATH/pgbouncer.ini.in"
    cp --no-clobber "$CONF_SRC_PATH/$CONF_FILE" "$CONF_DEST_PATH/$CONF_FILE"

    chmod 640 $CONF_DEST_PATH/* # do not use quotes as this would try to exact match the * and not expand it
    chown "$XBAT_USER:$XBAT_USER" $CONF_DEST_PATH/*
}

prepare_databases() {
    log_info "Preparing databases..."

    MONGODB_PATH="$LIB_BASE_PATH/mongodb"
    MONGODB_LOG_PATH="$LOG_BASE_PATH/mongodb"
    QUESTDB_PATH="$LIB_BASE_PATH/questdb"
    QUESTDB_CONF_PATH="$QUESTDB_PATH/conf"
    QUESTDB_LOG_PATH="$LOG_BASE_PATH/questdb"
    CLICKHOUSE_PATH="$LIB_BASE_PATH/clickhouse"
    CLICKHOUSE_LOG_PATH="$LOG_BASE_PATH/clickhouse"

    if [[ "$NODB" == false ]]; then

        sudo -u "$XBAT_USER" mkdir -p "$MONGODB_PATH" "$MONGODB_LOG_PATH" "$QUESTDB_PATH" "$QUESTDB_LOG_PATH" "$QUESTDB_CONF_PATH" "$CLICKHOUSE_PATH" "$CLICKHOUSE_LOG_PATH"
        sudo -u "$XBAT_USER" touch "$MONGODB_LOG_PATH/mongod.log"

        cp "$CONF_SRC_PATH/mongod.conf" "$CONF_DEST_PATH/mongod.conf"
        cp --recursive "$CONF_SRC_PATH/clickhouse" "$CONF_DEST_PATH/"

        # TODO find out why this file is missing
        # temporary fix for missing mime.types file in questdb
        if [[ ! -f "$QUESTDB_CONF_PATH/mime.types" ]]; then
            wget -O "$QUESTDB_CONF_PATH/mime.types" https://raw.githubusercontent.com/questdb/questdb/refs/heads/master/core/conf/mime.types
        fi

        if [[ "$EXPOSE_QUESTDB" == true ]]; then
            sed -i "s!#- \"#FRONTEND_NETWORK#:8812:8812\"!- \"$FRONTEND_NETWORK:8812:8812\"!" docker-compose.yml
        fi
    else
        # override file disables questdb and mongodb
        cp docker-compose.override.yml "$INSTALL_PATH"
    fi

    VALKEY_PATH="$LIB_BASE_PATH/valkey"
    mkdir -p "$VALKEY_PATH"
    chown "$XBAT_USER:$XBAT_USER" "$VALKEY_PATH"

    if [[ -f "$VALKEY_PATH/dump.rdb" ]]; then
        rm -f "$VALKEY_PATH/dump.rdb"
    fi

    cp "$CONF_SRC_PATH/valkey.conf" "$CONF_DEST_PATH/valkey.conf"
}

install_action() {
    if [[ "$NODB" == true && "$QUESTDB_ADDRESS_SET" == false ]]; then
        log_error "Please provide --questdb-address when using --no-db."
        exit 1
    fi

    check_prerequisites
    create_user_if_missing
    prepare_directories

    [[ -d "$BUILD_PATH" ]] && rm -rf "$BUILD_PATH"
    mkdir "$BUILD_PATH"
    rsync -Rr --exclude 'build' . "$BUILD_PATH/"
    pushd "$BUILD_PATH" > /dev/null

    sed -i "s!#QUESTDB_ADDRESS#!$QUESTDB_ADDRESS!" ./conf/nginx.conf.in
    sed -i "s!workers = 8!workers = $WORKERS!" ./src/backend/config-prod.py
    sed -i "s!instances: \"8\"!instances: \"$WORKERS\"!" ./src/ui/ecosystem.config.cjs

    build_docker_images
    prepare_databases
    configure_compose
    prepare_scripts_and_configs
    setup_systemd_service

    popd > /dev/null
    log_info "Installation completed successfully."
}

setup_systemd_service() {
    log_info "Setting up systemd service..."
    sed -i "s!#EXECUTOR#!$EXECUTOR!g" "./services/$SERVICE_NAME"
    cp "./services/$SERVICE_NAME" "$SERVICE_DEST_PATH"
    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME"
}

remove_action() {
    log_info "Starting removal..."
    systemctl stop "$SERVICE_NAME" || true
    systemctl disable "$SERVICE_NAME" || true
    rm -f "$SERVICE_DEST_PATH/$SERVICE_NAME"
    systemctl daemon-reload

    if [[ -d "$INSTALL_PATH" ]]; then
        pushd "$INSTALL_PATH" > /dev/null
        "$EXECUTOR_COMPOSE" down
        popd > /dev/null
    fi

    rm -rf "$INSTALL_PATH" "$CONF_DEST_PATH" "$RUN_PATH" "$LOG_BASE_PATH" "$LIB_BASE_PATH"

    if id "$XBAT_USER" &>/dev/null; then
        read -rp "Remove user '$XBAT_USER'? [y/N]: " confirm
        if [[ "$confirm" =~ ^[Yy]$ ]]; then
            userdel "$XBAT_USER"
            log_info "User '$XBAT_USER' removed."
        fi
    fi

    log_info "Removal completed successfully."
}

validate_action(){
    if [[ -f "$INSTALL_PATH/validate-config.sh" ]]; then
        bash "$INSTALL_PATH/validate-config.sh"
    else
        log_error "Validation script not found at $INSTALL_PATH/validate-config.sh"
        exit 1
    fi
}

generate_xbatd_conf_action() {
    if [[ -f "./scripts/create-xbatd-conf.sh" ]]; then
        bash "./scripts/create-xbatd-conf.sh" "$@"
    elif [[ -f "$INSTALL_PATH/create-xbatd-conf.sh" ]]; then
        bash "$INSTALL_PATH/create-xbatd-conf.sh" "$@"
    else
        log_error "Script not found at ./scripts/create-xbatd-conf.sh or $INSTALL_PATH/create-xbatd-conf.sh"
        exit 1
    fi
}

migrate_action() {
    # Default to 'status' if no arguments provided
    if [[ $# -eq 0 ]]; then
        set -- "status"
    fi
    
    # Check if this is a status check (explicit or default)
    if [[ "$1" == "status" ]]; then
        # Run migration status and capture output
        local migration_output
        local migration_exit_code
        
        if migration_output=$(/usr/local/share/xbat/clickhouse/migrate.sh "$@" 2>&1); then
            migration_exit_code=0
        else
            migration_exit_code=$?
        fi
        
        # Display the migration output
        echo "$migration_output"
        
        # Check if there are any pending migrations
        if echo "$migration_output" | grep -q "Pending"; then
            echo
            log_info "   ! Pending database migrations detected !"
            log_info "   Run the following command to upgrade the database:"
            log_info "   sudo $0 migrate up"
            echo
            log_info "   Other migration commands:"
            log_info "   sudo $0 migrate down      # Rollback last migration"
            echo
        elif [[ $migration_exit_code -eq 0 ]]; then
            log_info "✓ Database is up to date - no pending migrations"
        fi
        
        exit $migration_exit_code
    elif [[ "$1" == "down" ]]; then
        # Warn about potential data loss for rollback
        echo
        log_warning "Rolling back migrations may result in DATA LOSS!"
        log_warning "This operation will revert the last applied migration."
        echo
        read -rp "Are you sure you want to proceed? Type 'yes' to confirm: " confirm
        if [[ "$confirm" != "yes" ]]; then
            log_info "Migration rollback cancelled."
            exit 0
        fi
        # Proceed with rollback
        /usr/local/share/xbat/clickhouse/migrate.sh "$@"
    else
        # For non-status commands, just pass through to migrate script
        /usr/local/share/xbat/clickhouse/migrate.sh "$@"
    fi
}

show_help() {
    echo "$0 (install|remove|validate|migrate|generate-xbatd-conf)"
    echo
    echo "Actions:"
    echo -e "\tinstall              Install XBAT with configuration options below"
    echo -e "\tremove               Remove XBAT installation"
    echo -e "\tvalidate             Validate configuration file"
    echo -e "\tmigrate              Manage database migrations"
    echo -e "\tgenerate-xbatd-conf  Generate xbatd configuration file"
    echo
    echo "Install configuration options:"
    echo -e "\t[--help] Print this message"
    echo -e "\t[--executor (docker|podman)] Container executor (default: podman)"
    echo -e "\t[--home-mnt <path>] Mount home directory path"
    echo -e "\t[--port <port>] Frontend port (default: 7000)"
    echo -e "\t[--frontend-network <ip>] Bind frontend network (default: 0.0.0.0)"
    echo -e "\t[--no-db] Deploy without databases"
    echo -e "\t[--questdb-address <address>] QuestDB address (required with --no-db)"
    echo -e "\t[--expose-questdb] Expose QuestDB PGWire port"
    echo -e "\t[--workers <count>] Number of workers (default: 8)"
    echo -e "\t[--certificate-dir <dir>] Certificates directory (default: /etc/xbat/certs)"
    echo -e "\t[--user <user>] System user to run xbat (default: xbat)"
    echo
    echo "Migration commands:"
    echo -e "\t$0 migrate [status]     Check for pending database migrations (default)"
    echo -e "\t$0 migrate up           Apply all pending migrations"
    echo -e "\t$0 migrate down         Rollback last migration"
    echo
    echo "Generate xbatd configuration commands:"
    echo -e "\t$0 generate-xbatd-conf               Generate config to /etc/xbat/xbatd.conf"
    echo -e "\t$0 generate-xbatd-conf --stdout      Print config to stdout"
    echo
    echo "Examples:"
    echo -e "\t$0 install --port 8080 --workers 4"
    echo -e "\t$0 migrate status"
    echo -e "\t$0 validate"
    echo -e "\t$0 generate-xbatd-conf --stdout"
}

#########################################
# Argument Parsing                      #
#########################################

POSITIONAL_ARGS=()
ACTION_FOUND=false

while [[ $# -gt 0 ]]; do
  case $1 in
    install|remove|validate|migrate|generate-xbatd-conf)
      if [[ "$ACTION_FOUND" == false ]]; then
        ACTION_FOUND=true
        POSITIONAL_ARGS+=("$1")
        ACTION_TYPE="$1"
        shift
        # For non-install actions, pass remaining args directly without parsing
        if [[ "$ACTION_TYPE" != "install" ]]; then
          POSITIONAL_ARGS+=("$@")
          break
        fi
      else
        # Action already found, collect as positional arg
        POSITIONAL_ARGS+=("$1")
        shift
      fi
      ;;
    --executor) EXECUTOR="$2"; shift; shift;;
    --home-mnt) HOME_MNT="$2"; shift; shift;;
    --no-db) NODB=true; shift;;
    --expose-questdb) EXPOSE_QUESTDB=true; shift;;
    --port) FRONTEND_PORT="$2"; shift; shift;;
    --questdb-address) QUESTDB_ADDRESS="$2"; QUESTDB_ADDRESS_SET=true; shift; shift;;
    --frontend-network) FRONTEND_NETWORK="$2"; shift; shift;;
    --workers) WORKERS="$2"; shift; shift;;
    --certificate-dir) CERT_DIR="$2"; shift; shift;;
    --user) XBAT_USER="$2"; shift; shift;;
    --help) HELP=true; shift;;
    -*|--*) log_error "Unknown option $1"; exit 1;;
    *) POSITIONAL_ARGS+=("$1"); shift;;
  esac
done

set -- "${POSITIONAL_ARGS[@]}"

#########################################
# Main Logic                            #
#########################################


if [[ ${#POSITIONAL_ARGS[@]} -eq 0 || "$HELP" == true ]]; then
    show_help
    exit 0
fi

check_root

ACTION="$1"
shift  # Remove the action from the arguments so remaining args can be passed to the action function

case "$ACTION" in
    install) install_action "$@";;
    remove) remove_action "$@";;
    migrate) migrate_action "$@";;
    validate) validate_action "$@";;
    generate-xbatd-conf) generate_xbatd_conf_action "$@";;
    *) log_error "Unknown action: $ACTION"; show_help; exit 1;;
    
esac