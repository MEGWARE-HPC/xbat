import ldap
import logging
from flask import current_app as app

logger = logging.getLogger(__name__)

TIMEOUT = 15


def _get_dn(user):
    config = app.config['CONFIG']['authentication']
    # fallback in case configuration is not updated to contain user_identifier
    user_identifier = config[
        'user_identifier'] if 'user_identifier' in config else 'cn'
    return f"{user_identifier}={user},{config['basedn']}"


class LDAPConnector(object):

    def __init__(self):
        self.client = None

    def create_client(self):
        logger.info("Establishing connection with %s",
                    app.config["CONFIG"]["authentication"]["address"])
        try:
            client = ldap.initialize(
                app.config["CONFIG"]["authentication"]["address"])
            client.set_option(ldap.OPT_TIMEOUT, TIMEOUT)
            client.set_option(ldap.OPT_NETWORK_TIMEOUT, TIMEOUT)
            return client
        except ldap.LDAPError as e:
            logger.error("Could not establish connection - %s", e)

    def __enter__(self):
        self.client = self.create_client()
        return self.client

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            try:
                self.client.unbind_s()
                logger.info("LDAP connection successfully unbound.")
            except ldap.LDAPError as e:
                logger.error("Failed to unbind LDAP connection - %s", e)
            finally:
                self.client = None


class LDAPConnection(object):

    @classmethod
    def auth_user(cls, user, password):
        with LDAPConnector() as client:
            if client is None: return False
            try:
                client.simple_bind_s(_get_dn(user), password)
                return True
            except ldap.LDAPError as e:
                logger.error("Login attempt at LDAP failed for user '%s' - %s",
                             user, e)
            return False
