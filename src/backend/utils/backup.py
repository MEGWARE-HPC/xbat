import json
import csv
import asyncio
import logging
import time
import shutil
import subprocess
import re
from pathlib import Path
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from flask import current_app as app
from shared import httpErrors
from shared.files import recreate_folder, contains_files
from shared.helpers import sanitize_mongo
from shared.configuration import get_logger, get_config
from shared import clickhouse as cdb

logger = logging.getLogger(get_logger())
clickhouse = cdb.ClickHouse()


def data_anonymise(collection_db, username):
    target_keys = [
        'issuer', 'owner', 'configuration.misc.owner',
        'configuration.OUTPUT_DIRECTORY', 'configuration.LOG_DIRECTORY',
        'jobscriptFile', 'jobInfo.command', 'jobInfo.standardError',
        'jobInfo.standardOutput', 'jobInfo.userName',
        'jobInfo.currentWorkingDirectory', 'standardOutput', 'user_name',
        'homedirectory', 'misc.owner', 'members', 'user_type', 'uidnumber',
        'gidnumber', 'last_login'
    ]

    collection_db = replace_key_fields(collection_db,
                                       target_keys,
                                       username,
                                       replaced_value='demo')

    return collection_db


def save_as_json(path, collection, filter_key, filter_value, anonymise,
                 username, db):
    """
    Build a function to save the data results obtained from MongoDB 
    and save it in a json file.
    """
    if filter_value:
        if collection != 'benchmarks' and collection != 'jobs':
            if collection == 'outputs':
                collection_db = list(
                    db.getMany(collection, {filter_key: filter_value}))
            elif collection == 'nodes' or collection == 'projects':
                collection_db = list(
                    db.getMany(collection, {filter_key: {
                        '$in': filter_value
                    }}))
            else:
                collection_db = db.getOne(collection,
                                          {filter_key: filter_value})
            if anonymise:
                collection_db = data_anonymise(collection_db, username)
            if collection_db:
                with open(path, "w") as file:
                    json.dump(sanitize_mongo(collection_db), file)


def _get_clickhouse_base_cmd():
    """
    Get ClickHouse client base command with configuration.
    
    :return: Base command array for clickhouse-client
    """
    config = get_config()
    if "clickhouse" not in config:
        logger.error("Invalid configuration: missing 'clickhouse' config.")
        return None

    ch_config = config["clickhouse"]
    host = ch_config.get("host", "localhost")
    port = ch_config.get("daemon_port", 9000)
    user = ch_config.get("user")
    password = ch_config.get("password")
    database = ch_config.get("database")

    base_cmd = ["clickhouse-client", "--host", host, "--port", str(port)]
    if database:
        base_cmd.extend(["--database", database])
    if user:
        base_cmd.extend(["--user", user])
    if password:
        base_cmd.extend(["--password", password])

    return base_cmd


async def clickhouse_import_csvs(csv_paths, old_jobId, new_jobId):
    """
    Replace jobId in CSV files and import them into ClickHouse in parallel.
    
    :param csv_paths: List of CSV file paths to import
    :param old_jobId: Old jobId to replace
    :param new_jobId: New jobId to use as replacement
    """

    start_time = time.time()
    semaphore = asyncio.Semaphore(8)

    base_cmd = _get_clickhouse_base_cmd()
    if base_cmd is None:
        return False

    def _replace_csv_job_id(csv_file, old_jobId, new_jobId):
        try:
            if old_jobId == new_jobId:
                return True

            with open(csv_file, mode='r', encoding='utf-8') as infile:
                content = infile.read()

            # Replace jobId in the first column
            pattern = rf'^{re.escape(str(old_jobId))},'
            replacement = f'{new_jobId},'
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

            with open(csv_file, mode='w', encoding='utf-8') as outfile:
                outfile.write(content)
            return True
        except Exception as e:
            logger.error(
                f"Unexpected error replacing jobId in file {csv_file}: {e}")
            return False

    async def _import_csv(csv_file):
        async with semaphore:
            return await _import_csv_inner(csv_file)

    async def _import_csv_inner(csv_file):
        table_name = csv_file.stem

        # First replace jobId if needed
        replace_success = await asyncio.to_thread(_replace_csv_job_id,
                                                  csv_file, old_jobId,
                                                  new_jobId)
        if not replace_success:
            return False

        # Then import the CSV into ClickHouse
        query = f"INSERT INTO {table_name} FORMAT CSV"
        cmd = base_cmd + ["--query", query]

        def _run():
            try:
                with open(csv_file, "rb") as csvfile:
                    result = subprocess.run(cmd,
                                            stdin=csvfile,
                                            stderr=subprocess.PIPE,
                                            check=False)
                return result
            except Exception as e:
                logger.error(f"Error importing {csv_file}: {e}")
                return None

        result = await asyncio.to_thread(_run)
        if result is None or result.returncode != 0:
            error_msg = result.stderr.decode(
                "utf-8", errors="ignore")[:512] if result else "Unknown error"
            logger.error("ClickHouse import failed for table '%s': %s",
                         table_name, error_msg)
            return False
        return True

    tasks = []
    for csv_path in csv_paths:
        tasks.append(_import_csv(csv_path))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    total_duration = time.time() - start_time

    success_count = sum(1 for result in results if result is True)
    failure_count = len(results) - success_count

    logger.debug("ClickHouse import total duration: %.2f seconds",
                 total_duration)
    logger.info(
        f"ClickHouse import completed: {success_count} successful, {failure_count} failed"
    )

    return success_count > 0


async def clickhouse_save_as_csv(job_id, runNr_path):
    path = runNr_path / Path(str(job_id))
    recreate_folder(path, parents=True)

    tables = await clickhouse.get_table_names()
    export_start_time = time.time()
    # Use a semaphore to limit the number of concurrent exports
    semaphore = asyncio.Semaphore(8)

    base_cmd = _get_clickhouse_base_cmd()
    if base_cmd is None:
        return

    async def _export_table(table_name, output_path):
        async with semaphore:
            return await _export_table_inner(table_name, output_path)

    async def _export_table_inner(table_name, output_path):
        query = f"SELECT * FROM {table_name} WHERE job_id = '{job_id}'"
        cmd = base_cmd + ["--format", "CSV", "--query", query]

        def _run():
            start_time = time.time()
            with open(output_path, "wb") as csvfile:
                result = subprocess.run(cmd,
                                        stdout=csvfile,
                                        stderr=subprocess.PIPE,
                                        check=False)
            duration = time.time() - start_time
            logger.debug(
                "ClickHouse export duration for table '%s': %.2f seconds",
                table_name, duration)
            return result

        result = await asyncio.to_thread(_run)
        if result.returncode != 0:
            logger.error("ClickHouse export failed for table '%s': %s",
                         table_name,
                         result.stderr.decode("utf-8", errors="ignore")[:512])
            if output_path.exists():
                output_path.unlink()
            return False

        if output_path.exists() and output_path.stat().st_size == 0:
            output_path.unlink()
            return False
        return True

    tasks = []
    for table in tables:
        csv_file_path = path / Path(f"{table}.csv")
        tasks.append(_export_table(table, csv_file_path))
    await asyncio.gather(*tasks)
    total_duration = time.time() - export_start_time
    logger.debug("ClickHouse export total duration: %.2f seconds",
                 total_duration)


def replace_key_fields(data, target_keys, target_value, replaced_value='demo'):
    """
    Replace target_value with replaced_value('demo') in the value of the specified key in the Dict.
    Skip if key does not exist.

    :param data: input Dict
    :param target_keys: list of keys to check (nested paths are supported, use "." to indicate nesting levels)
    :param target_value: original username
    :return: new Dict after replacement
    """

    def replace_nested_key(data, keys, target_value, replaced_value):

        if not keys:
            return

        key = keys[0]

        if isinstance(data, dict):
            if key in data:
                if len(keys) == 1:
                    if key == "members":
                        data[key] = [replaced_value]
                    # Treat the user type of 'demo' as demo now.
                    elif key == 'user_type':
                        data[key] = 'demo'
                    elif key == 'owner':
                        data[key] = 'demo'
                    elif key == 'uidnumber':
                        data[key] = "1001"
                    elif key == 'gidnumber':
                        data[key] = "1001"
                    elif key == 'last_login':
                        data[key] = ''
                    elif isinstance(data[key], str):
                        data[key] = data[key].replace(target_value,
                                                      replaced_value)
                    elif isinstance(data[key], list):
                        data[key] = [
                            v.replace(target_value, replaced_value)
                            if isinstance(v, str) else v for v in data[key]
                        ]
                else:
                    replace_nested_key(data[key], keys[1:], target_value,
                                       replaced_value)
        elif isinstance(data, list):
            for item in data:
                replace_nested_key(item, keys, target_value, replaced_value)
        else:
            return

    for target_key in target_keys:
        key_path = target_key.split('.')
        replace_nested_key(data, key_path, target_value, replaced_value)

    return data


def replace_jobId_json(data, collection, jobId_map):
    """
    Replace jobIds in data with new jobIds based on the provided mapping.
    
    :param data: old data
    :param collection: collection name
    :param jobId_map: mapping of old jobIds to new jobIds (dict)
    """

    def replace_job_id(obj):
        if isinstance(obj, list):
            for item in obj:
                replace_job_id(item)
        elif isinstance(obj, dict):
            if collection == "benchmarks":
                job_ids = obj.get("jobIds", [])
                for i in range(len(job_ids)):
                    old_id = job_ids[i]
                    new_id = jobId_map.get(old_id, old_id)
                    job_ids[i] = new_id
            elif collection == "jobs":
                obj["jobId"] = jobId_map.get(obj["jobId"], obj["jobId"])
                if "jobInfo" in obj and isinstance(obj["jobInfo"], dict):
                    nested_job_id = obj["jobInfo"].get("jobId")
                    new_nested_job_id = jobId_map.get(nested_job_id,
                                                      nested_job_id)
                    obj["jobInfo"]["jobId"] = new_nested_job_id
            elif collection == "outputs":
                job_id = obj.get("jobId")
                if job_id in jobId_map:
                    obj["jobId"] = jobId_map[job_id]

    if isinstance(data, list):
        for item in data:
            replace_job_id(item)
    else:
        replace_job_id(data)


def process_csv(csv_file, jobId_map):
    try:
        with open(csv_file, mode='r', newline='', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            fieldnames = reader.fieldnames

            if not ('jobId' in fieldnames):
                logger.error(
                    f"Warning: 'jobId' column not found in file {csv_file}")
                return

            rows = []
            for row in reader:
                old_jobId = row['jobId']
                new_jobId = jobId_map.get(old_jobId, old_jobId)
                row['jobId'] = new_jobId
                rows.append(row)

        with open(csv_file, mode='w', newline='', encoding='utf-8') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
    except PermissionError as e:
        logger.error(f"Permission error accessing file {csv_file}: {e}")
    except csv.Error as e:
        logger.error(f"CSV error processing file {csv_file}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error processing file {csv_file}: {e}")


def get_new_jobIds(benchmark_db, db):
    """
    Generate a new jobId mapping relationship.

    :param benchmark_db: Benchmark database entry
    :param db: MongoDB database instance

    :return dict: Contains the mapping relationship from old jobId to new jobId.
    """
    if 'jobIds' in benchmark_db and benchmark_db['jobIds']:
        jobIds = benchmark_db['jobIds']
    else:
        jobIds = []
        if benchmark_db['runNr']:
            job_db = list(db.getMany("jobs", {"runNr": benchmark_db['runNr']}))
            if job_db is None:
                raise httpErrors.NotFound(
                    "Job with runNr %s not found in jobs collection" %
                    benchmark_db['runNr'])
            for job_data in job_db:
                if 'jobId' in job_data:
                    if job_data['jobId'] not in jobIds:
                        jobIds.append(job_data['jobId'])

    jobId_map = {}
    for jobId in jobIds:
        new_jobId = db.getNextAvailableJobId()
        jobId_map[jobId] = new_jobId

    return jobId_map


def extract_hash(node_hashes):
    if node_hashes is None:
        return []
    nodes_list = []
    for element in node_hashes:
        if isinstance(element, str):
            nodes_list.append(element)
        elif isinstance(element, list):
            for sub_element in element:
                if isinstance(sub_element, str):
                    nodes_list.append(sub_element)
    return nodes_list


async def save_benchmarks(runNr, anonymise, folder_path, db):
    if runNr is not None:
        benchmark_db = db.getOne("benchmarks", {"runNr": runNr})
        if benchmark_db is None:
            raise httpErrors.NotFound(
                "Benchmark with runNr %s not found in benchmarks collection" %
                runNr)
        if 'state' in benchmark_db and benchmark_db['state'] in [
                "pending", "queued", "running"
        ]:
            logger.error(
                f"The Benchmark with runNr{runNr} is still {benchmark_db['state']}, it will not be exported."
            )
            return
        node_hashes = []
        job_list = []
        if 'jobIds' in benchmark_db and benchmark_db['jobIds']:
            if len(benchmark_db['jobIds']) > 1:
                job_db = list(db.getMany("jobs", {"runNr": runNr}))
                if job_db is None:
                    raise httpErrors.NotFound(
                        "Job with runNr %s not found in jobs collection" %
                        runNr)
                for job_data in job_db:
                    if 'nodes' in job_data and isinstance(
                            job_data['nodes'], dict):
                        node_hash = [
                            value['hash']
                            for value in job_data['nodes'].values()
                            if 'hash' in value
                        ]
                    else:
                        node_hash = None
                    if node_hash not in node_hashes:
                        node_hashes.append(node_hash)
            else:
                job_db = db.getOne("jobs", {"runNr": runNr})
                if job_db is None:
                    raise httpErrors.NotFound(
                        "Job with runNr %s not found in jobs collection" %
                        runNr)
                if 'nodes' in job_db and isinstance(job_db['nodes'], dict):
                    node_hashes = [
                        value['hash'] for value in job_db['nodes'].values()
                        if 'hash' in value
                    ]
                else:
                    node_hashes = None
            job_list = benchmark_db['jobIds']
        else:
            # for compatibility with old benchmarks that did not save jobIds in the benchmark.
            job_db = list(db.getMany("jobs", {"runNr": runNr}))
            if job_db is None:
                raise httpErrors.NotFound(
                    "Job with runNr %s not found in jobs collection" % runNr)
            for job_data in job_db:
                if 'jobId' in job_data:
                    job_list.append(job_data["jobId"])
                if 'nodes' in job_data and isinstance(job_data['nodes'], dict):
                    node_hash = [
                        value['hash'] for value in job_data['nodes'].values()
                        if 'hash' in value
                    ]
                else:
                    node_hash = None
                if node_hash not in node_hashes:
                    node_hashes.append(node_hash)

        nodes_list = extract_hash(list(node_hashes))

        collections = {
            'benchmarks': {
                'filter': 'runNr',
                'value': runNr
            },
            'jobs': {
                'filter': 'runNr',
                'value': runNr
            },
            'outputs': {
                'filter': 'runNr',
                'value': runNr
            },
            'nodes': {
                'filter': 'hash',
                'value': nodes_list if nodes_list is not None else None
            },
            'users': {
                'filter': 'user_name',
                'value': benchmark_db['issuer']
            },
            'projects': {
                'filter':
                '_id',
                'value':
                list(benchmark_db['sharedProjects'])
                if benchmark_db['sharedProjects'] else None
            },
            'configurations': {
                'filter':
                '_id',
                'value':
                benchmark_db['configuration']['_id']
                if benchmark_db['configuration'] else None
            }
        }

        runNr_path = folder_path / str(runNr)
        orig_username = benchmark_db['issuer']
        recreate_folder(runNr_path)

        try:
            for collection in collections:
                file_path = runNr_path / Path(collection + '.json')
                if collection == 'benchmarks':
                    if anonymise:
                        benchmark_db = data_anonymise(benchmark_db,
                                                      orig_username)
                    with open(file_path, "w") as file:
                        json.dump(sanitize_mongo(benchmark_db), file)
                elif collection == 'jobs':
                    if anonymise:
                        job_db = data_anonymise(job_db, orig_username)
                    with open(file_path, "w") as file:
                        json.dump(sanitize_mongo(job_db), file)
                else:
                    save_as_json(file_path, collection,
                                 collections[collection]['filter'],
                                 collections[collection]['value'], anonymise,
                                 orig_username, db)
            for job_id in job_list:
                await clickhouse_save_as_csv(job_id, runNr_path / "jobs")
        except Exception as e:
            app.logger.error("Error occurred while saving: %s" % e)
            raise httpErrors.InternalServerError(
                "Error saving %s for runNr %s to file." % (collection, runNr))


def count_csv_files(path: Path) -> int:
    """Count all CSV files under path recursively."""
    if not isinstance(path, Path):
        path = Path(path)
    if not path.exists():
        return 0
    return sum(1 for _ in path.rglob("*.csv"))


def _remove_id(item):
    """Remove _id field from item to avoid duplication during inserts."""
    item.pop("_id", None)
    return item


def _process_item(collection,
                  item,
                  db,
                  update_collections,
                  is_reassigned_run_nr,
                  lookup_key="_id"):
    """
    Process a single item for insert or update.
    
    :param collection: Collection name
    :param item: Item to process
    :param db: Database instance
    :param update_collections: Whether to update existing items
    :param is_reassigned_run_nr: Whether runNr was reassigned
    :param lookup_key: Key to use for looking up existing items
    """
    # Prepare lookup filter
    if lookup_key == "_id" and "_id" in item:
        lookup_filter = {lookup_key: ObjectId(item["_id"])}
    else:
        lookup_filter = {lookup_key: item[lookup_key]}

    # Check if item exists
    existing_item = db.getOne(collection, lookup_filter)

    # For reassigned runNr or benchmarks/jobs/outputs, always insert as new
    if is_reassigned_run_nr and collection in [
            "benchmarks", "jobs", "outputs"
    ]:
        _remove_id(item)
        db.insertOne(collection, item)
    elif not existing_item:
        _remove_id(item)
        db.insertOne(collection, item)
    elif update_collections:
        _remove_id(item)
        db.replaceOne(collection, lookup_filter, item)


def process_collection(collection, data, db, update_collections,
                       is_reassigned_run_nr):
    """
    Process collection data for import.
    
    :param collection: Collection name
    :param data: Data to process (single item or list)
    :param db: Database instance
    :param update_collections: Whether to update existing items
    :param is_reassigned_run_nr: Whether runNr was reassigned
    """
    # Normalize data to list
    items = data if isinstance(data, list) else [data]

    # Determine lookup key based on collection
    lookup_keys = {
        "users": "user_name",
        "nodes": "hash",
        "configurations": "_id",
        "projects": "_id",
        "benchmarks": "_id",
        "jobs": "_id",
        "outputs": "_id"
    }

    lookup_key = lookup_keys.get(collection, "_id")

    # Process each item
    for item in items:
        _process_item(collection, item, db, update_collections,
                      is_reassigned_run_nr, lookup_key)


def pigz_compress(input_path, uuid):
    """
    Compress all files with pigz in the specified folder to tar format and delete the original files and folders.
    :return: compressed file path, or error message
    """
    start_time = time.time()
    source_folder = input_path / Path(str(uuid))
    if not source_folder.is_dir():
        raise FileNotFoundError("The specified folder does not exist")
    if not contains_files(source_folder):
        logger.error(
            f"The folder '{source_folder}' does not contain any files.")
        compress_status = False
    else:
        output_path = input_path / Path(str(uuid) + '.tgz')
        # Weighing compression efficiency and compressed file size, the current compression rate rating is chosen to be '3'
        command = [
            'tar', '--use-compress-program=pigz -3', '-cpf',
            output_path.as_posix(), '-C',
            source_folder.as_posix(), '.'
        ]
        try:
            subprocess.run(command, stderr=subprocess.PIPE, check=True)
            end_time = time.time()
            logger.debug(
                f"Compression duration: {end_time - start_time:.2f} seconds")
        except subprocess.CalledProcessError as e:
            logger.error(f"Compression failed: {e.stderr.decode('utf-8')}")
        except Exception as e:
            raise RuntimeError("Error during compression: " + str(e))
        compress_status = True

    start_time = time.time()
    try:
        shutil.rmtree(source_folder)
    except Exception as e:
        raise RuntimeError("Error during deletion of original folder: " +
                           str(e))
    end_time = time.time()
    logger.debug(f"Cleanup duration: {end_time - start_time:.2f} seconds")
    return compress_status


def pigz_decompress(input_path, extract_folder):
    """
    Decompress the tgz file with pigz to the specified folder, and delete the tgz file.
    """
    start_time = time.time()
    if not input_path.is_file():
        raise FileNotFoundError("The specified file does not exist")
    command = [
        'tar', '--use-compress-program=pigz', '-xpf',
        input_path.as_posix(), '-C',
        extract_folder.as_posix()
    ]
    try:
        subprocess.run(command, stderr=subprocess.PIPE, check=True)
        end_time = time.time()
        logger.debug(f"File {input_path} decompressed to {extract_folder}")
        logger.debug(
            f"Decompression duration: {end_time - start_time:.2f} seconds")
    except subprocess.CalledProcessError as e:
        logger.error(f"Decompression failed: {e.stderr.decode('utf-8')}")
    except Exception as e:
        raise RuntimeError("Error during decompression: " + str(e))
    input_path.unlink()
