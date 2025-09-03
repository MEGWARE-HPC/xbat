import json
import uuid
import shutil
from pathlib import Path
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
from flask import send_from_directory, request, current_app as app
from shared import httpErrors
from shared.mongodb import MongoDB
from shared.files import recreate_folder, check_extension
from shared.helpers import sanitize_mongo, replace_runNr, desanitize_mongo, str_to_bool
from backend.restapi.grpc_client import XbatCtldRpcClient
from backend.restapi.access_control import check_user_permissions
from backend.restapi.user_helper import get_user_from_token, create_user_benchmark_filter
from backend.restapi.backup import save_benchmarks, get_import_runNr, get_new_jobIds, process_collection, replace_jobId_json, process_table, pigz_compress, pigz_decompress

db = MongoDB()
rpcClient = XbatCtldRpcClient()

EXPORT_PATH = Path("/tmp/xbat/export")
IMPORT_PATH = Path("/tmp/xbat/import")

READ_EXCLUDE = {
    "_id": False,
    # for compatibility with old benchmark format
    "ref_permutations": False,
    "configuration.project": False,
    # for compatibility with old benchmark format
    "config._id": False
}


def _create_aggregation_pipeline(filterQuery):
    """
    The function creates an aggregation pipeline to join jobIds to benchmarks
    
    :param filterQuery: query object
    :return: pipeline
    """
    # TODO this aggregation is only required for backwards compatibility as jobIds are already present
    return [{
        "$match": filterQuery
    }, {
        '$lookup': {
            'from': "jobs",
            'localField': "runNr",
            'foreignField': "runNr",
            'as': "tmpJobs"
        },
    }, {
        "$addFields": {
            "jobIds": "$tmpJobs.jobId"
        }
    }, {
        "$project": {
            "tmpJobs": False,
            **READ_EXCLUDE
        }
    }]


def _set_benchmark_state(benchmarks):
    # TODO remove
    # for compatibility with old benchmarks due to incorrect setting of stage/state/status
    for b in benchmarks:
        if "stage" in b:
            b["state"] = b["stage"]
        elif "status" in b:
            b["state"] = b["status"]
    return benchmarks


def get_user_benchmarks(runNrs=[]):
    """
    Retrieves benchmarks based on user's permissions and project
    access with optional runNr filter.
    
    :param runNr: run number
    :return: Returns a list of benchmarks if `runNr` is `None`,
    otherwise it returns a single benchmark or an empty dictionary.
    """
    user = get_user_from_token()

    filterQuery = create_user_benchmark_filter(user)

    if len(runNrs):
        filterQuery["$and"] = [{"runNr": {"$in": runNrs}}]

    return _set_benchmark_state(
        list(
            db.aggregate("benchmarks",
                         _create_aggregation_pipeline(filterQuery))))


def get_all(runNrs=[]):
    """
    Returns all benchmarks of user including ones shared from project.

    :return: benchmarks
    """
    result = get_user_benchmarks(runNrs=runNrs)
    return {"data": sanitize_mongo(result)}, 200


def get(runNr):
    """
    Returns benchmark with specified runNr.
    
    :param runNr: run number of benchmark
    :return: benchmark
    """

    result = get_user_benchmarks(runNrs=[runNr])
    return {"data": sanitize_mongo(result[0]) if len(result) else {}}, 200


@check_user_permissions
def patch(runNr):
    """
    Update specified benchmark.
    
    :param runNr: run number of benchmark
    :return: updated benchmark
    """

    data = request.get_json()

    if not runNr or not ("sharedProjects" in data or "name" in data):
        raise httpErrors.BadRequest(
            "Invalid run number or no patchable properties provided")

    if "name" in data:
        update = {"name": data["name"]}
    elif "sharedProjects" in data:
        update = {
            "sharedProjects": [ObjectId(p) for p in data["sharedProjects"]]
        }

    result = db.updateOne("benchmarks", {"runNr": runNr}, {"$set": update})

    return sanitize_mongo(result), 200


@check_user_permissions
def delete(runNr):
    """
    Delete specified benchmark and all related information.
    
    :param runNr: run number of benchmark
    :return: empty response
    """

    run_nr_filter = {"runNr": runNr}

    db.deleteOne("benchmarks", run_nr_filter)

    jobIds = db.getMany("jobs", run_nr_filter, {"jobId": True})
    if jobIds is not None:
        jobIds = [j["jobId"] for j in jobIds]

    db.deleteMany("jobs", run_nr_filter)

    db.deleteMany("outputs", {"jobId": {"$in": jobIds}})

    return {}, 204


def post():
    """
    Start benchmark by forwarding request to controld.
    
    :return: empty response
    """

    data = request.get_json()
    user = get_user_from_token()

    # admin must not launch benchmarks
    # in theory this should already be caught by the missing benchmarks_submit permission for admins
    if user is None or user["user_type"] == "admin":
        raise httpErrors.Forbidden()

    response = rpcClient.submit_benchmark({
        "issuer":
        user["user_name"],
        "name":
        data["name"],
        "configId":
        data["configId"],
        "variables":
        data["variables"] if "variables" in data else [],
        "sharedProjects":
        data["sharedProjects"] if "sharedProjects" in data else [],
    })

    if not response:
        raise httpErrors.InternalServerError("Failed to submit benchmark")

    return {}, 204


def backup_mongoDB():
    """
    Backup the entire MongoDB database (admin only).
    """
    user = get_user_from_token()
    if user is None or user["user_type"] != "admin":
        raise httpErrors.Forbidden(
            "Only administrators are allowed to perform this action")

    backup_uuid = str(uuid.uuid1())
    folder_path = EXPORT_PATH / backup_uuid
    folder_path.mkdir(parents=True, exist_ok=True)

    try:
        collections = db.list_collection_names()
        if not collections:
            return {}, 204

        for collection_name in collections:
            file_path = folder_path / f"{collection_name}.json"
            database = db.getMany(collection_name, {})
            with open(file_path, "w") as f:
                json.dump(sanitize_mongo(database), f)
    except Exception as e:
        app.logger.error("MongoDB backup failed: %s", e)
        raise httpErrors.InternalServerError("MongoDB backup failed")

    try:
        compress_status = pigz_compress(EXPORT_PATH, backup_uuid)
    except Exception as e:
        app.logger.error("Error occurred while compressing backup: %s", e)
        raise httpErrors.InternalServerError("Error compressing files")

    if compress_status:
        response = send_from_directory(
            directory=EXPORT_PATH,
            path=f"{backup_uuid}.tgz",
            mimetype="application/octet-stream",
            as_attachment=True,
            download_name=f"MongoDB_{backup_uuid}.tgz",
        )
        return response, 200
    else:
        return {}, 204


async def export_benchmark():
    """
    Export specified benchmark(s) and all related information (manager and admin only). 

    """
    user = get_user_from_token()
    if user is None or user["user_type"] not in ["admin", "manager"]:
        raise httpErrors.Forbidden(
            "Only managers and administrators are allowed to perform this action"
        )
    data = request.get_json()
    runNrs = data["runNrs"]
    anonymise = data["anonymise"]
    manager_uuid = str(uuid.uuid1())
    folder_path = EXPORT_PATH / manager_uuid
    folder_path.mkdir(parents=True, exist_ok=True)
    csv_counts = 0

    for runNr in runNrs:
        try:
            csv_count = await save_benchmarks(runNr, anonymise, folder_path,
                                              db)
            csv_counts += csv_count
        except Exception as e:
            app.logger.error("Benchmark export failed: %s" % e)
            raise httpErrors.InternalServerError("Benchmark runNr %s failed." %
                                                 runNr)
    try:
        compress_status = pigz_compress(EXPORT_PATH, manager_uuid)
    except Exception as e:
        app.logger.error("Error occurred while compressing: %s" % e)
        raise httpErrors.InternalServerError("Error compressing files")

    if compress_status:
        response = send_from_directory(
            directory=EXPORT_PATH,
            path=f"{manager_uuid}.tgz",
            mimetype="application/octet-stream",
            as_attachment=True,
            download_name=f"exported_{manager_uuid}.tgz",
        )
        headers = {"CSV-Counts": csv_counts}
        return response, 200, headers
    else:
        return {}, 204


async def import_benchmark():
    """
    Import benchmark(s) from a backup file (manager and admin only).

    """
    user = get_user_from_token()
    if user is None or user["user_type"] not in ["admin", "manager"]:
        raise httpErrors.Forbidden(
            "Only managers and administrators are allowed to perform this action"
        )
    if 'file' not in request.files:
        raise httpErrors.BadRequest("No file provided")
    file = request.files["file"]
    if file.filename == '' or not file.filename:
        raise httpErrors.BadRequest("No file selected")
    if not check_extension(file.filename, 'tgz') and not check_extension(
            file.filename, 'tar.gz') and not check_extension(
                file.filename, 'gz'):
        raise httpErrors.BadRequest("Invalid file extension")

    file_name = secure_filename(file.filename)
    IMPORT_PATH.mkdir(parents=True, exist_ok=True)
    tar_path = IMPORT_PATH / file_name
    manager_uuid = str(uuid.uuid1())
    reassignRunNr = request.form.get("reassignRunNr")
    updateColl = request.form.get("updateColl")
    if isinstance(updateColl, str):
        updateColl = str_to_bool(updateColl)

    try:
        file.save(tar_path)
        extract_folder = IMPORT_PATH / manager_uuid
        recreate_folder(extract_folder)
        pigz_decompress(tar_path, extract_folder)
    except Exception as e:
        app.logger.error("Error occurred while extracting: %s" % e)
        raise httpErrors.InternalServerError("Error extracting files")
    runNr_cache = {}
    for jsonfile_path in Path(extract_folder).rglob("*.json"):
        folder = jsonfile_path.relative_to(extract_folder).parent
        if folder not in runNr_cache:
            benchmarks_path = extract_folder / folder / "benchmarks.json"
            if benchmarks_path.exists():
                with open(benchmarks_path, 'r') as benchmark_json:
                    benchmark_data = json.load(benchmark_json)
                    if not benchmark_data:
                        raise httpErrors.InternalServerError(
                            f"Failed to load {benchmarks_path}")
                    else:
                        temp_runNr, maxJobId = await get_import_runNr(
                            benchmark_data, db, reassignRunNr)
                        runNr_cache[folder] = temp_runNr
                        jobId_map = {}
                        if maxJobId:
                            jobId_map = get_new_jobIds(benchmark_data, db,
                                                       maxJobId)
        new_runNr = runNr_cache[folder]
        with open(jsonfile_path, "r") as file:
            try:
                data = json.load(file)
                if not data:
                    continue
                collection = jsonfile_path.stem
                data = desanitize_mongo(data)
                if reassignRunNr == "true":
                    replace_runNr(data, new_runNr)
                if maxJobId:
                    if collection in ["benchmarks", "jobs", "outputs"]:
                        replace_jobId_json(data, collection, jobId_map)
                process_collection(collection, data, db, updateColl)
                if collection == "benchmarks":
                    await process_table(jsonfile_path.parent, jobId_map)
            except json.JSONDecodeError as e:
                raise httpErrors.BadRequest(
                    "Invalid JSON file causing errors: %s" % e)
            except Exception as e:
                raise httpErrors.InternalServerError(
                    "An unexpected error occurred while processing: %s" % e)
    try:
        shutil.rmtree(extract_folder)
    except Exception as e:
        raise RuntimeError("Error during deletion of extracted folder: " +
                           str(e))

    return {}, 204


def purge():
    """
    Purge benchmarks from QuestDB.
    
    :return: empty response
    """

    user = get_user_from_token()
    if user is None or user["user_type"] != "admin":
        raise httpErrors.Forbidden(
            "Only administrators are allowed to perform this action")

    response = rpcClient.purge_questdb()

    if not response:
        raise httpErrors.InternalServerError("Failed to purge benchmarks")

    return {}, 204
