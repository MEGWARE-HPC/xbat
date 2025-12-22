import logging
import asyncio
import psycopg as pg
from psycopg.rows import dict_row
from shared.helpers import format_error
from shared.configuration import get_logger, get_config

CONCURRENT_QUERY_LIMIT = 64  # Limit concurrent queries to prevent exhausting the database connections

logger = logging.getLogger(get_logger())


class ClickHouse:
    """Async wrapper for psycopg/pgbouncer to query ClickHouse"""

    conninfo = ""

    def setup(self):
        """Defers connection setup to first query as configuration may not be available yet"""
        if self.conninfo != "":
            return

        config = get_config()
        if "pgbouncer" not in config:
            logger.error("Invalid configuration: missing 'pgbouncer' config.")
            return

        config = config["pgbouncer"]
        self.conninfo = (
            f"dbname=clickhouse host={config['host']} port={config['port']} user={config['user']} password={config['password']}"
        )

    async def _execute(self, query):
        """Execute query with connection from pgbouncer"""

        result = []
        try:
            async with await pg.AsyncConnection.connect(
                    self.conninfo,
                    autocommit=
                    True,  # For ClickHouse compatibility to prevent "Expected TRANSACTION" errors
            ) as conn:
                async with conn.cursor(row_factory=dict_row) as cursor:
                    logger.debug(query)
                    await cursor.execute(query)
                    result = await cursor.fetchall()
        except pg.OperationalError as e:
            logger.error("Connection error: %s", format_error(e))
        except pg.ProgrammingError as e:
            # no result present, e.g. no returning statement
            pass
        except pg.DatabaseError as e:
            logger.error("Database error: %s | SQL: %s", format_error(e),
                         query[:512])
        except pg.Error as e:
            logger.error(format_error(e))

        return result

    async def execute_queries(self,
                              queries,
                              concurrency=CONCURRENT_QUERY_LIMIT):
        """Execute multiple queries (with concurrency limit)"""
        self.setup()

        semaphore = asyncio.Semaphore(concurrency)

        async def _execute_concurrent(query):
            async with semaphore:
                return await self._execute(query)

        results = []
        for i in range(0, len(queries), concurrency):
            batch = queries[i:i + concurrency]
            results.extend(
                await asyncio.gather(*[_execute_concurrent(q) for q in batch]))
        return results

    async def execute_query(self, query):
        """Execute a single query"""
        return (await self.execute_queries([query]))[0]