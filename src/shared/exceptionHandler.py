import sys
import logging
from shared.configuration import get_logger

logger = logging.getLogger(get_logger())


def handle_exception(*args):
    exc_type = args[0] if len(args) > 1 else args[0].exc_type
    exc_value = args[1] if len(args) > 1 else args[0].exc_value
    exc_traceback = args[2] if len(args) > 1 else args[0].exc_traceback

    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.error("Uncaught exception",
                 exc_info=(exc_type, exc_value, exc_traceback))
