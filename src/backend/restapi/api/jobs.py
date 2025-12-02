import numpy as np
from filelock import FileLock
from flask import request, current_app as app
from shared import httpErrors
from shared.mongodb import MongoDB
from shared.helpers import sanitize_mongo
from shared.date import get_current_timestamp
from backend.restapi.access_control import check_user_permissions
from backend.restapi.user_helper import get_user_from_token, create_user_benchmark_filter

BENCHMARKING_WINDOW = 900  # 15 minutes

db = MongoDB()

register_lock = FileLock("/tmp/register-jobs.lock")


# TODO remove
# TEMPORARY IMPLEMENTATION TO MIGRATE TO NEW SCHEMA
def _job_maintenance():
    if "outputs" in db.list_collection_names():
        return

    jobs = db.getMany("jobs", {})

    for job in jobs:
        db.insertOne(
            "outputs", {
                "runNr": job["runNr"],
                "jobId": job["jobId"],
                "output": job["slurmOutput"],
            })
    db.updateMany("jobs", {}, {"$unset": {"slurmOutput": ""}})


def get_all(runNrs=None, jobIds=None, short=False):
    """
    Retrieves jobs based on user access permissions and specified filters.
    
    :param runNrs: filter by runNrs
    :param jobIds: filter by job Ids
    :param short: shortened output
    :return: all jobs matching filter and user permissions
    """

    _job_maintenance()

    user = get_user_from_token()

    benchmarkQuery = create_user_benchmark_filter(user)

    benchmarks = db.getMany("benchmarks", benchmarkQuery, {"runNr": True})
    accessable_runs = [b["runNr"] for b in benchmarks]
    jobs = db.getMany("jobs", {"runNr": {
        "$in": accessable_runs
    }}, {"jobId": True})
    accessable_jobs = [j["jobId"] for j in jobs]

    if runNrs is not None:
        for run in runNrs:
            if not (run in accessable_runs): raise httpErrors.Unauthorized()

    if jobIds is not None:
        for job in jobIds:
            if not (job in accessable_jobs): raise httpErrors.Unauthorized()

    query_filter = {}
    if runNrs is not None:
        query_filter = {"runNr": {"$in": runNrs}}
    elif jobIds is not None:
        query_filter = {"jobId": {"$in": jobIds}}
    else:
        query_filter = {"runNr": {"$in": accessable_runs}}

    exclude_filter = {
        "_id": False,
    }

    if short:
        exclude_filter = {
            **exclude_filter,
            "runNr": True,
            "jobId": True,
            "iteration": True,
            "runtime": True,
            "capturetime": True,
            "configuration.jobscript.variantName": True,
            "nodes": True,
            "jobInfo.jobState": True,
            "variables": True,
        }

    result = db.getMany("jobs", query_filter, exclude_filter)

    return {
        "data": sanitize_mongo(list(result)) if result is not None else []
    }, 200


@check_user_permissions
def patch(jobId):
    """
    Patches job related data if user has the required permissions.
    
    Currently only variantName may be patched.

    :param jobId: JobId to patch
    :return: patched job data
    """
    data = request.get_json()

    if not jobId or not ("variantName" in data):
        raise httpErrors.BadRequest(
            "Invalid jobId or no patchable properties provided")

    result = db.updateOne(
        "jobs", {"jobId": jobId},
        {"$set": {
            "configuration.jobscript.variantName": data["variantName"]
        }})

    return sanitize_mongo(result), 200


def get_output(jobId):
    """
    Retrieves job output for specific jobId.
    
    :param jobId: job id
    is returned along with a status code of 200. If the output is
    :return: output with meta data
    """
    result = db.getOne("outputs", {"jobId": int(jobId)}, {"_id": False})

    if result is None:
        return {
            "jobId": int(jobId),
            "standardOutput": None,
            "standardError": None,
            "lastUpdate": None
        }, 200

    # convert old outputs to new format
    if "output" in result:
        result["standardOutput"] = result["output"]
        result["standardError"] = None
        del result["output"]

    return result, 200


def register(jobId):
    """
    Registers a new job to the database if not yet present and returns job monitoring settings.

    Jobs (and therefore benchmarks) submitted through the REST-API are already registered and will simply return the monitoring settings.
    All jobs submitted via the CLI (sbatch with --constraint=xbat) must be registered first and will receive default settings. These jobs are assigned
    a benchmark for consistency reasons. When a job is registered, the node hash is checked to determine whether a benchmark is required.
    Usage of FileLock to prevent race conditions when multi-node jobs are trying to register a job simultaneously.
    Due to the low volume of jobs submitted via the CLI, this should not be a bottleneck.
    
    :param jobId: job id
    :return: job settings required for monitoring
    """

    interval = app.config["CONFIG"][
        "cli_interval"] if "cli_interval" in app.config["CONFIG"] else 10
    enable_monitoring = True
    enable_likwid = True
    hash_missing = False

    data = request.get_json()
    node_hash = data["hash"]
    hostname = data["hostname"]

    with register_lock:
        job = db.getOne("jobs", {"jobId": jobId})
        if job is None:
            # wrap job with benchmark for consistency
            benchmark_data = {
                "name": None,
                "issuer": None,
                "configId": None,
                "state": "running",
                "sharedProjects": [],
                "variables": [],
                "cli": True,
                "jobIds": [jobId],
            }
            benchmark_id = db.createBenchmark(**benchmark_data)

            # retrieve runNr
            benchmark = db.getOne("benchmarks", {"_id": benchmark_id})
            if benchmark is None:
                raise httpErrors.InternalServerError()
            runNr = benchmark["runNr"]

            # insert empty job
            job_data = {
                "configuration": None,
                "identificator": jobId,
                "iteration": None,
                "jobId": jobId,
                "jobscriptFile": None,
                "userJobscriptFile": None,
                "permutationNr": None,
                "jobInfo": None,
                "runNr": runNr,
                "variables": [],
                "nodes": {},
                "cli": True,
                "nodes": {
                    hostname: {
                        "hash": node_hash,
                        "hostname": hostname
                    }
                }
            }
            db.insertOne("jobs", job_data)
            app.logger.debug("Registered job: %s", jobId)
        else:

            job_configuration = job["configuration"]
            interval = int(
                job_configuration["interval"]
            )  # int conversion for compatibility with older job configurations
            enable_monitoring = job_configuration["enableMonitoring"]
            enable_likwid = job_configuration["enableLikwid"]

            # register node to job
            db.updateOne("jobs", {"jobId": jobId}, {
                "$set": {
                    f"nodes.{hostname}": {
                        "hash": node_hash,
                        "hostname": hostname
                    }
                }
            })
            app.logger.debug("Updated registered job: %s", jobId)

        # determine whether node must be benchmarked by checking if benchmarks for this particular hash are present
        node = db.getOne("nodes", {"hash": node_hash})
        if node is None:
            hash_missing = True
            # insert empty node details to prevent benchmarking multiple times on multi-node jobs or identical node configurations
            db.insertOne("nodes", {
                "hash": node_hash,
                "lastUpdate": get_current_timestamp()
            })
            app.logger.debug("Registered new empty node with hash: %s",
                             node_hash)
        else:
            # check when node was last updated since benchmarking may have failed and therefore a new benchmark is required
            # if no benchmarks are present

            # determine whether required benchmarks are present: require bandwidth_mem and at least one peakflops* entry
            benchmarks = node.get("benchmarks") or {}
            # check presence of memory bandwidth benchmark
            has_bandwidth = "bandwidth_mem" in benchmarks
            # check if there's any peakflops* entry
            has_peakflops = any(
                key.startswith("peakflops") and benchmarks.get(key) is not None
                for key in benchmarks)
            # required benchmark completeness
            has_required_benchmarks = has_bandwidth and has_peakflops
            # check if benchmarking window expired
            benchmarking_window_expired = not (
                "lastUpdate" in node) or get_current_timestamp(
                ) - node["lastUpdate"] > BENCHMARKING_WINDOW

            if not has_required_benchmarks and benchmarking_window_expired:
                hash_missing = True
                db.updateOne("nodes", {"hash": node_hash},
                             {"$set": {
                                 "lastUpdate": get_current_timestamp()
                             }})
                app.logger.debug("Commissioned new benchmarks for: %s",
                                 node_hash)

    return {
        "jobId": jobId,
        "interval": interval,
        "enableMonitoring": enable_monitoring,
        "enableLikwid": enable_likwid,
        "benchmarkRequired": hash_missing
    }, 200
