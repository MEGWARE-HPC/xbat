import logging
import os
import redis
import pickle
from flask import current_app as app
from shared.helpers import format_error
from shared.configuration import get_logger

logger = logging.getLogger(get_logger())

EXPIRE_TIME = 60 * 60 * 24 * 7  # one week (seconds)


class Valkey():
    connection_pool = None
    conninfo = ""
    pool_name = ""
    pool_instance = 0

    def __init__(self):
        pass

    def connect(self):
        with app.app_context():
            if not "valkey" in app.config["CONFIG"]:
                logger.error(
                    "Invalid xbat.conf. Missing valkey configuration.")
                return False
            config = app.config["CONFIG"]["valkey"]
            self.conninfo = f'redis://{config["host"]}:{config["port"]}/{config["database"]}'
        try:
            self.pool_name = f"redis-pool-{os.getpid()}-{self.pool_instance}"
            self.pool_instance += 1
            logger.debug("Creating %s", self.pool_name)
            # decode_responses=True (handled by pickle)
            # TODO use async connection pool
            # https://redis-py.readthedocs.io/en/stable/connections.html#connectionpool-async
            self.connection_pool = redis.ConnectionPool.from_url(
                self.conninfo, socket_timeout=0.5)
            return True
        except (redis.exceptions.ConnectionError) as e:
            app.logger.error(format_error(e))
            self.connection_pool = None
        return False

    def disconnect(self):
        if self.connection_pool is not None:
            self.connection_pool.close()

    def _execute(self, operation, key, value=None):
        if self.connection_pool is None:
            if not self.connect():
                return None

        result = None

        try:
            logger.debug(
                f"[valkey {operation}] {key} on pool {self.pool_name}")
            with redis.Redis(connection_pool=self.connection_pool) as client:
                if operation == "get":
                    result = client.get(key)
                    if result is not None:
                        result = pickle.loads(result)
                elif operation == "set":
                    result = client.set(key,
                                        pickle.dumps(value),
                                        ex=EXPIRE_TIME)

        except (redis.exceptions.RedisError) as e:
            logger.error("Error calling valkey.\n %s", format_error(e))

        return result

    def get(self, key):
        return self._execute("get", key)

    def set(self, key, value):
        return self._execute("set", key, value)
