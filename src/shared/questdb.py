import time
import logging
import asyncio
import itertools
import threading
import psycopg as pg
from psycopg.rows import dict_row
from shared.helpers import format_error
from shared.configuration import get_logger, get_config

CONCURRENT_TABLE_PURGE_LIMIT = 3  # Limit concurrent purges to prevent overloading the database or exhausting the RAM
CONCURRENT_QUERY_LIMIT = 64  # Limit concurrent queries to prevent exhausting the database connections

logger = logging.getLogger(get_logger())

_purge_lock = threading.Lock()


class QuestDB:
    """Async wrapper for psycopg/pgbouncer to query QuestDB"""

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
            f"dbname=questdb host={config['host']} port={config['port']} user={config['user']} password={config['password']}"
        )

    async def _execute(self, query):
        """Execute query with connection from pgbouncer"""

        result = []
        try:
            async with await pg.AsyncConnection.connect(self.conninfo) as conn:
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


def questdb_maintenance():
    """
    Adds missing indexes to tables in QuestDB and checks for suspended Write Ahead Log (WAL).

    Tables are dynamically created with ILP without any indexes - scan all tables and add indexe if missing.
    WAL may be suspended for certain tables in case of a database crash or insufficient disk space.
    """

    async def _questdb_maintenance():
        questdb = QuestDB()
        # check for missing indexes
        tables = await questdb.execute_query("SHOW TABLES")
        if not len(tables): return

        indexed_cols = ["jobId", "node", "level"]

        # support for older questdb versions
        table_column = 'table_name' if 'table_name' in tables[0] else 'table'

        cols = await questdb.execute_queries(
            [f"SHOW COLUMNS FROM {t[table_column]}" for t in tables])
        indexing_queries = []

        for idx, table in enumerate(tables):
            if not len(cols[idx]): continue
            for col in cols[idx]:
                if col["column"] in indexed_cols and col[
                        "type"] == "SYMBOL" and not col["indexed"]:
                    indexing_queries.append(
                        f"ALTER TABLE {table[table_column]} ALTER COLUMN {col['column']} ADD INDEX"
                    )

        logger = logging.getLogger(__name__)

        if len(indexing_queries):
            await questdb.execute_queries(indexing_queries)
            logger.info(f"Added indexes to {len(indexing_queries)} tables")

        # check for suspended WAL
        wal_tables = await questdb.execute_query("wal_tables()")
        suspended_tables = [t["name"] for t in wal_tables if t["suspended"]]

        if len(suspended_tables):
            logger.warning(
                f"Suspended WAL for {len(suspended_tables)} tables detected")
            await questdb.execute_queries(
                [f"ALTER TABLE {t} RESUME WAL" for t in suspended_tables])
            logger.info(f"Resumed WAL for {len(suspended_tables)} tables")

    asyncio.run(_questdb_maintenance())


def questdb_purge():
    """
    Purges deleted jobs from QuestDB.

    QuestDB does not support DELETE queries, so we need to create a temporary table, copy the valid data and drop the original table.
    Make a backup of the database and only execute this when no xbat jobs are running!
    """

    async def _questdb_purge():

        from shared.mongodb import MongoDB
        mongodb = MongoDB()
        questdb = QuestDB()

        logger.info("Purging QuestDB of deleted jobs")

        tables = await questdb.execute_query("SHOW TABLES")

        if not len(tables): return

        # support for older questdb versions
        table_column = 'table_name' if 'table_name' in tables[0] else 'table'

        queries = [
            f"SELECT DISTINCT jobId FROM {t[table_column]}" for t in tables
        ]

        table_jobIds = {}
        results = await questdb.execute_queries(queries)

        for idx, table in enumerate(tables):
            ids = results[idx]
            table_jobIds[table[table_column]] = [int(i["jobId"]) for i in ids]

        questdb_jobIds = list(set(itertools.chain(*table_jobIds.values())))

        if not len(questdb_jobIds):
            logger.info("No jobs found in QuestDB for purge")
            return

        registered_jobs = mongodb.getMany("jobs",
                                          {"jobId": {
                                              "$in": questdb_jobIds
                                          }}, {"jobId": True})

        registered_jobIds = [j["jobId"] for j in registered_jobs]

        jobIds_to_delete = list(
            set(questdb_jobIds).difference(registered_jobIds))

        if not len(jobIds_to_delete):
            logger.info("No jobs to delete from QuestDB")
            return

        logger.info(
            f"Deleting {len(jobIds_to_delete)} jobs from QuestDB [{','.join(map(str, jobIds_to_delete))}]"
        )

        affected_tables = []
        for table, jobIds in table_jobIds.items():
            if len(set(jobIds).intersection(jobIds_to_delete)):
                affected_tables.append(table)

        semaphore = asyncio.Semaphore(CONCURRENT_TABLE_PURGE_LIMIT)

        async def _purge_table(table):
            where = " AND ".join([f"jobId != {j}" for j in jobIds_to_delete])
            async with semaphore:
                await questdb.execute_query(
                    f"CREATE TABLE {table}_backup AS (SELECT * FROM {table} WHERE {where}) TIMESTAMP(timestamp) PARTITION BY DAY;"
                )
                await questdb.execute_query(f"DROP TABLE {table}")
                await questdb.execute_query(
                    f"RENAME TABLE {table}_backup TO {table}")

        start = time.time()

        tasks = [_purge_table(table) for table in affected_tables]
        await asyncio.gather(*tasks)

        logger.info(
            f"Deleted {len(jobIds_to_delete)} jobs from QuestDB in {time.time() - start:.2f}s"
        )

    # prevent concurrent purges
    acquired = _purge_lock.acquire(blocking=False)
    if not acquired:
        logger.info("QuestDB purge already in progress. Skipping new request.")
        return

    try:
        asyncio.run(_questdb_purge())
    except Exception as e:
        logger.error(f"QuestDB purge failed: {e}")
    finally:
        _purge_lock.release()
