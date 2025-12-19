from shared.configuration import set_logger, set_app

NAME = "xbatctld"

set_logger(NAME)
set_app(NAME)

import os
import sys
import signal
import threading
import logging
import logging.config
from pathlib import Path
from shared import configuration
from shared.mongodb import MongoDB
from shared.exceptionHandler import handle_exception
from shared.helpers import overwrite_log_level, get_service_configuration
from shared.questdb import questdb_maintenance
from xbatctld import registration
from xbatctld.grpc_server import serve
from xbatctld.pipe import clear_run_files

LOGGING_CONFIG_PATH = Path().absolute().parent / "shared" / "logging.conf"
JOB_STATE_INTERVAL = 10

RUN_PATH = "/run/xbatctld"

BUILD = os.getenv('BUILD', "dev")

db = MongoDB()
sys.excepthook = handle_exception
threading.excepthook = handle_exception

service_configuration = get_service_configuration()
configuration.set_config(service_configuration)
configuration.set_build(BUILD)

DEMO = service_configuration["demo"][
    "enabled"] if "demo" in service_configuration and "enabled" in service_configuration[
        "demo"] else False

configuration.set_demo(DEMO)

logging.config.fileConfig(LOGGING_CONFIG_PATH, disable_existing_loggers=False)
overwrite_log_level(NAME, service_configuration["general"]["log_level"])
logger = logging.getLogger(NAME)

cancelled = threading.Event()


def signalHandler(sig, frame):
    logger.info(
        "Received signal %s\nShutting down.\nRepeat signal for immediate shutdown.",
        sig)
    global cancelled
    if cancelled.is_set():
        sys.exit(1)
    cancelled.set()


def main():
    logger.debug("Starting %s", NAME)

    signal.signal(signal.SIGINT, signalHandler)
    signal.signal(signal.SIGTERM, signalHandler)

    # remove potentially left over files
    clear_run_files()

    db_settings = service_configuration["mongodb"]

    db.set(db_settings["address"], db_settings["database"],
           db_settings["user"], db_settings["password"])

    # if BUILD == "prod":
    #     questdb_maintenance()

    grpc_t = threading.Thread(target=serve, args=(cancelled, ), daemon=True)

    grpc_t.start()

    if BUILD == "prod" and not DEMO:
        registration_t = threading.Thread(
            target=registration.registration_handler, args=(cancelled, ))
        registration_t.start()
        registration_t.join()

    grpc_t.join()

    logger.debug("Shutting down %s", NAME)


if __name__ == "__main__":
    set_logger(NAME)
    set_app(NAME)
    main()
