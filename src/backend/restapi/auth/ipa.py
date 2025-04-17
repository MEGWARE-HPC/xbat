import logging
import threading
import python_freeipa
from flask import current_app as app

logger = logging.getLogger(__name__)


# singleton pattern based upon https://stackoverflow.com/a/40542664/8212473
class IPAConnector(object):

    def __init__(self):
        self.client = None

    def create_client(self):
        logger.info("Creating client to %s",
                    app.config["CONFIG"]["authentication"]["address"])
        return python_freeipa.ClientMeta(
            app.config["CONFIG"]["authentication"]["address"],
            verify_ssl=app.config["CONFIG"]["authentication"].getboolean(
                "verify_ssl"))

    def __enter__(self):
        self.client = self.create_client()
        return self.client

    def __exit__(self, exc_type, exc_val, exc_tb):
        # TODO check if connection has to be terminated
        pass


class IPAConnection(object):
    client = None
    _lock = threading.Lock()

    @classmethod
    def get_client(cls, new=False):
        # double check client for None reduces number expensive lock operations
        if new or not cls.client:
            with cls._lock:
                if new or not cls.client:
                    cls.client = IPAConnector().create_client()
        return cls.client

    @classmethod
    def auth_user(cls, user, password):
        client = cls.get_client()
        try:
            client.login(user, password).logout()
            return True
        except (python_freeipa.exceptions.InvalidSessionPassword,
                python_freeipa.exceptions.Unauthorized) as e:
            logger.error("Login attempt at IPA failed for user '%s' - %s",
                         user, e)
            pass
        return False

    @classmethod
    def get_user(cls, user, password):
        # user must be logged in to query for information
        client = cls.get_client()
        try:
            session = client.login(user, password)
            user_info = client.user_show(user)
            session.logout()
            return user_info
        except (python_freeipa.exceptions.InvalidSessionPassword,
                python_freeipa.exceptions.Unauthorized) as e:
            logger.error(
                "Retrieval of IPA information failed for user '%s' - %s", user,
                e)
        return None
