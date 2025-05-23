import json
import csv
import asyncio
import logging
import time
import shutil
import subprocess
from pathlib import Path
from bson.objectid import ObjectId
from flask import current_app as app
from aiohttp import ClientSession, BasicAuth, FormData
from concurrent.futures import ThreadPoolExecutor
from shared import questdb as qdb
from shared import httpErrors
from shared.files import recreate_folder, contains_files
from shared.helpers import sanitize_mongo
from shared.configuration import get_logger, get_config

logger = logging.getLogger(get_logger())

questdb = qdb.QuestDB()


class QuestDBAPI:

    def __init__(self):
        """
        Initialize QuestDB API.
        """
        self.config = get_config()
        if "questdb" not in self.config:
            logger.error("Invalid configuration: missing 'questdb' config.")
            return
        self.config = self.config["questdb"]
        self.host = self.config.get("host", "localhost")
        self.port = self.config.get("api_port", 9000)
        self.username = self.config.get("api_user")
        self.password = self.config.get("api_password")

    def _get_auth(self):
        """
        Get authentication information.
        """
        auth = {}
        if self.username and self.password:
            auth["auth"] = BasicAuth(self.username, self.password)
        return auth

    async def export_to_csv(self, table_name, path, job_id=None):
        """
        Export the data in the QuestDB table to a CSV file.
        :param session: aiohttp ClientSession object
        :param table_name: the name of the table to be exported
        :param path: the path of the output CSV file
        """
        query = f"SELECT * FROM {table_name}"
        if job_id:
            query += f" WHERE jobId IN {job_id}"
        url = f"http://{self.host}:{self.port}/exp"
        params = {"query": query}
        auth = self._get_auth()
        try:
            async with ClientSession() as session:
                async with session.get(url, params=params, **auth) as response:
                    if response.status == 200:
                        data = await response.read()
                        csv_content = data.decode('utf-8').strip()
                        csv_row = csv_content.split('\n')
                        if len(csv_row) < 2:
                            return False
                        with open(path, "wb") as file:
                            file.write(data)
                        return True
                    else:
                        logger.error(
                            f"Export failed for table '{table_name}', status code: {response.status}, "
                            f"error message: {await response.text()}")
                        return False
        except Exception as e:
            logger.error(
                f"An error occurred while exporting data from table '{table_name}': {e}"
            )

    async def export_tables(self, table_names, runNr_path, job_id=None):
        """
        Asynchronously export multiple tables to CSV files based on the provided job IDs.

        :param table_names: list of table names to be exported
        :param job_id: list of job IDs to filter by (optional)
        """
        start_time = time.time()
        tasks = []
        for table_name in table_names:
            path = runNr_path / Path(table_name + ".csv")
            task = self.export_to_csv(table_name, path, job_id)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        logger.debug(
            f"Export duration from QuestDB: {end_time - start_time: .2f} seconds"
        )
        success_count = sum(1 for result in results if result is True)
        skip_count = sum(1 for result in results if result is False)
        failure_count = len(results) - (success_count + skip_count)
        logger.info(
            f"Export completed: {success_count} successful, {skip_count} skipped (no data), {failure_count} failed"
        )
        return success_count

    async def import_from_csv(self, table_name, path):
        """
        Import data from CSV file into QuestDB table
        
        :param table_name: the name of the table to be imported
        :param path: the path to the CSV file to import from
        """
        url = f"http://{self.host}:{self.port}/imp"
        auth = self._get_auth()
        params = {
            "name": table_name,
            "partitionBy": "DAY",
            "timestamp": "timestamp",
            "create": "true"
        }
        try:
            with open(path, 'r', encoding='utf-8') as file:
                csv_reader = csv.reader(file)
                csv_header = next(csv_reader)
            schema_list = []
            for column in csv_header:
                if column == "value":
                    col_type = "DOUBLE"
                    schema_list.append({"name": column, "type": col_type})
                elif column == "timestamp":
                    col_type = "TIMESTAMP"
                    pattern = "yyyy-MM-ddTHH:mm:ss.SSSUUUz"
                    schema_list.append({
                        "name": column,
                        "type": col_type,
                        "pattern": pattern
                    })
                else:
                    col_type = "SYMBOL"
                    schema_list.append({"name": column, "type": col_type})
            schema_str = json.dumps(schema_list)
            form_data = FormData()
            form_data.add_field('schema', schema_str)

            with open(path, "r", encoding='utf-8') as csvfile:
                csv_data = csvfile.read()
                form_data.add_field('data',
                                    csv_data,
                                    filename=table_name + ".csv")
                async with ClientSession() as session:
                    async with session.post(url,
                                            params=params,
                                            data=form_data,
                                            **auth) as response:
                        if response.status == 200:
                            return True
                        else:
                            return False
        except Exception as e:
            logger.error(
                f"Error occurred while importing data into  '{table_name}': {e}"
            )
            return False

    async def import_csvs(self, table_paths):
        """
        Import CSV files into QuestDB tables
        
        :param table_paths: a dictionary mapping table names to CSV file paths
        """
        start_time = time.time()
        tasks = []
        for table_name, path in table_paths.items():
            task = self.import_from_csv(table_name, path)
            tasks.append(task)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        logger.debug(
            f"Import duration to QuestDB: {end_time - start_time: .2f} seconds"
        )
        success_count = sum(1 for result in results if result is True)
        failure_count = len(results) - success_count
        logger.info(
            f"Import completed: {success_count} successful, {failure_count} failed"
        )


questapi = QuestDBAPI()


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


async def get_table_names():
    """
    Get all the table names from QuestDB.

    :return: List of table names.
    """
    query = "SELECT table_name FROM tables() ORDER BY table_name ASC;"
    result = await questdb.execute_query(query)
    if not result:
        return []
    table_names = [row["table_name"] for row in result]

    return table_names


async def save_as_csv(job_id, runNr_path):
    if job_id == "()" or not job_id:
        raise httpErrors.NotFound("JobId not found")
    table_names = await get_table_names()
    csv_count = await questapi.export_tables(table_names, runNr_path, job_id)
    return csv_count


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


async def replace_jobId_csv(path, jobId_map):
    """
    Replace jobIds in CSV files with new jobIds based on the provided mapping.

    :param path: Path to the directory containing CSV files.
    :param jobId_map: Dictionary mapping old jobIds to new jobIds (dict)
    """
    if not isinstance(path, Path) or not path.is_dir():
        logger.error(f"Invalid path or directory not found: {path}")
        return
    jobId_map_str = {str(k): str(v) for k, v in jobId_map.items()}
    with ThreadPoolExecutor() as executor:
        loop = asyncio.get_running_loop()
        tasks = []
        for csv_file in path.glob("*.csv"):
            task = loop.run_in_executor(executor, process_csv, csv_file,
                                        jobId_map_str)
            tasks.append(task)

        await asyncio.gather(*tasks)


def get_new_jobIds(benchmark_db, db, maxjobId):
    """
    Generate a new jobId mapping relationship.

    :param jobIds: old jobId array.
    :param maxjobId: current maximum jobId.

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
    for i, jobId in enumerate(jobIds):
        new_jobId = maxjobId + 1 + i
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
            job_list = []
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

        job_id = '(' + ', '.join(f"'{str(item)}'" for item in job_list) + ')'
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

        for collection in collections:
            file_path = runNr_path / Path(collection + '.json')
            try:
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
                    csv_count = await save_as_csv(job_id, runNr_path)
                else:
                    save_as_json(file_path, collection,
                                 collections[collection]['filter'],
                                 collections[collection]['value'], anonymise,
                                 orig_username, db)
            except Exception as e:
                app.logger.error("Error occurred while saving: %s" % e)
                raise httpErrors.InternalServerError(
                    "Error saving %s for runNr %s to file." %
                    (collection, runNr))
        return csv_count


async def get_import_runNr(data, db, reassignRunNr):
    """
    Get the runNr and maxJobId for importing data.

    :return: new_runNr and maxJobId
    """
    # The type of the parameter (reassignRunNr) from the FormData is String
    if reassignRunNr == "true":
        if db.getOne("benchmarks", {"_id": ObjectId(data["_id"])}):
            new_runNr = db.getOne("benchmarks",
                                  {"_id": ObjectId(data["_id"])})["runNr"]
            maxJobId = 0
        else:
            new_runNr = db.getNextRunNr()
            jobID_questdb = await questdb.execute_query(
                "SELECT MAX(jobId) AS maxJobId FROM cpu_usage;")
            jobID_mongodb = list(
                db.aggregate("jobs", [{
                    "$group": {
                        "_id": "null",
                        "maxJobId": {
                            "$max": "$jobId"
                        }
                    }
                }]))
            if jobID_mongodb or jobID_questdb:
                maxJobId = max(int(jobID_questdb[0]['maxJobId']),
                               int(jobID_mongodb[0]['maxJobId']))
            else:
                maxJobId = 30000

        if db.getOne("benchmarks", {"runNr": data["runNr"]}):
            return (new_runNr, maxJobId)
        else:
            return (data["runNr"],
                    0) if data["runNr"] < new_runNr else (new_runNr, maxJobId)
    else:
        return (data["runNr"], 0)


def get_tablepath_dict(path):
    """
    Get a dictionary mapping table names to their corresponding CSV file paths

    """
    csv_files = path.glob("*.csv")
    if not list(csv_files):
        logger.error(f"No CSV files found in the directory:{path}")
    table_dict = {}
    for csv_file in csv_files:
        table_name = csv_file.stem
        table_dict[table_name] = csv_file
    return table_dict


def process_collection(collection, data, db, updateColl):
    if collection == "configurations":
        for item in data if isinstance(data, list) else [data]:
            if not db.getOne(collection, {"_id": ObjectId(item["_id"])}):
                db.insertOne(collection, item)
            else:
                if updateColl:
                    db.replaceOne(collection, {"_id": ObjectId(item["_id"])},
                                  item)
    elif collection == "projects":
        if isinstance(data, list):
            for item in data:
                if not db.getOne(collection, {"_id": ObjectId(item["_id"])}):
                    db.insertOne(collection, item)
                else:
                    if updateColl:
                        db.replaceOne(collection,
                                      {"_id": ObjectId(item["_id"])}, item)
        else:
            if not db.getOne(collection, {"_id": ObjectId(data["_id"])}):
                db.insertOne(collection, data)
            else:
                if updateColl:
                    db.replaceOne(collection, {"_id": ObjectId(data["_id"])},
                                  data)
    elif collection == "users":
        if not db.getOne(collection, {"user_name": data["user_name"]}):
            db.insertOne(collection, data)
        else:
            if updateColl:
                db.replaceOne(collection, {"user_name": data["user_name"]},
                              data)
    elif collection == "nodes":
        if isinstance(data, list):
            for item in data:
                if not db.getOne(collection, {"hash": item["hash"]}):
                    db.insertOne(collection, item)
                else:
                    if updateColl:
                        db.replaceOne(collection, {"hash": item["hash"]}, item)
        else:
            if not db.getOne(collection, {"hash": data["hash"]}):
                db.insertOne(collection, data)
            else:
                if updateColl:
                    db.replaceOne(collection, {"hash": data["hash"]}, data)
    elif collection in ["benchmarks", "jobs", "outputs"]:
        if isinstance(data, list):
            for item in data:
                if not db.getOne(collection, {"_id": ObjectId(item["_id"])}):
                    db.insertOne(collection, item)
                else:
                    if updateColl:
                        db.replaceOne(collection,
                                      {"_id": ObjectId(item["_id"])}, item)
        else:
            if not db.getOne(collection, {"_id": ObjectId(data["_id"])}):
                db.insertOne(collection, data)
            else:
                if updateColl:
                    db.replaceOne(collection, {"_id": ObjectId(data["_id"])},
                                  data)


async def process_table(csvs_path, jobId_map):
    table_dict = get_tablepath_dict(csvs_path)
    # TODO: Consider adding logic to conditionally import data when QuestDB data is absent.
    # This can be achieved by checking if not table_dict.
    if table_dict:
        jobId_list = []
        try:
            with open(table_dict["cpu_usage"],
                      'r',
                      newline='',
                      encoding='utf-8') as cpu_usage_file:
                reader = csv.DictReader(cpu_usage_file)
                if 'jobId' not in reader.fieldnames:
                    logger.error(f"'jobId' column not found in {csvs_path}")
                for row in reader:
                    job_id = row["jobId"]
                    if job_id not in jobId_list:
                        jobId_list.append(job_id)
        except Exception as e:
            logger.error(f"Error reading CPU usage CSV: {e}")
        jobId_list_str = [f"'{x}'" for x in jobId_list]
        jobIds = f"({', '.join(jobId_list_str)})"
        data_count = await questdb.execute_query(
            f"SELECT COUNT(*) AS count FROM cpu_usage WHERE jobId IN {jobIds};"
        )
        if data_count:
            data_count = int(data_count[0]['count'])
        else:
            data_count = 0
        if data_count > 0:
            logger.info(
                "The data already exists in the QuestDB database, skip the write process"
            )
            return
        else:
            if jobId_map:
                await replace_jobId_csv(csvs_path, jobId_map)
            await questapi.import_csvs(table_dict)


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
            output_path.as_posix(),
            source_folder.as_posix()
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
        extract_folder.as_posix(), '--strip-components=4'
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
