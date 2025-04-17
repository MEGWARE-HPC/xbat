import logging
import time
import traceback
from bson.objectid import ObjectId

from shared import exc
from shared.mongodb import MongoDB
from xbatctld.slurm import SlurmConnector
from xbatctld.paths import get_xbat_directories, HOME_MOUNT_PREFIX
from shared.helpers import strip_first_slash
from shared.files import read_file_to_str, parse_to_json
from shared.date import seconds_to_time, iso8601_to_datetime, get_current_datetime, unix_ts_to_datetime

JOB_STATE_INTERVAL = 30  # should not be smaller than slurm REFRESH_TIMER otherwise WATCH_MIN_ITERATIONS mechanism must be adjusted
WATCH_MIN_ITERATIONS = 3

logger = logging.getLogger("xbatctld")
db = MongoDB()

slurm = SlurmConnector()

STATES = {
    "COMPLETED": {
        "value": 0,
        "label": "done"
    },
    "DEADLINE": {
        "value": 1,
        "label": "deadline"
    },
    "TIMEOUT": {
        "value": 2,
        "label": "timeout"
    },
    "CANCELLED": {
        "value": 3,
        "label": "cancelled"
    },
    "FAILED": {
        "value": 4,
        "label": "failed"
    },
}


def _process_job(jobId, directories, job_info):
    """
    Processes and saves available job data.
    
    :param jobId: Job ID
    :param directories: xbat directories (if not CLI benchmark)
    :param job_info: Slurm job information
    """

    job = db.getOne("jobs", {"jobId": jobId})

    if job is None:
        logger.error("Could not update job %d - not found in database", jobId)
        return

    # update job timestamps
    if directories is not None:
        time_log_path = directories["internal"]["logs"] / "{}.time.log".format(
            jobId)

        if time_log_path.is_file():
            time = parse_to_json(time_log_path)
            runtime_seconds = time["end"] - time[
                "start"] if "start" in time and "end" in time else 0

            capture_start = time[
                "captureStart"] if "captureStart" in time else 0
            capture_end = time["captureEnd"] if "captureEnd" in time else 0

            capturetime_s = max(capture_end - capture_start, 0)

            job = {
                **job,
                **{
                    "runtime":
                    seconds_to_time(runtime_seconds),
                    "runtimeSeconds":
                    runtime_seconds,
                    "capturetime":
                    seconds_to_time(capturetime_s),
                    "capturetimeSeconds":
                    capturetime_s,
                    "captureStart":
                    unix_ts_to_datetime(capture_start) if capture_start > 0 else None,
                    "captureEnd":
                    unix_ts_to_datetime(capture_end) if capture_end > 0 else None,
                }
            }
    else:
        start_time = job_info["startTime"] if "startTime" in job_info else None
        end_time = job_info["endTime"] if "endTime" in job_info else None
        if start_time is not None:
            start_time = iso8601_to_datetime(start_time)
        if end_time is not None:
            end_time = iso8601_to_datetime(end_time)

        if start_time is not None and end_time is not None:
            runtime_seconds = (end_time - start_time).total_seconds()
            job["runtime"] = seconds_to_time(runtime_seconds)
            job["runtimeSeconds"] = runtime_seconds

        job["startTime"] = start_time
        job["endTime"] = end_time

    # update jobInfo every time as data may change
    if bool(job_info):
        job["jobInfo"] = job_info

    # try to retrieve job script for CLI jobs
    if not job["userJobscriptFile"]:
        jobscript_path = HOME_MOUNT_PREFIX / strip_first_slash(
            job_info["command"]) if "command" in job_info else None
        if jobscript_path is not None and jobscript_path.is_file():
            job["userJobscriptFile"] = read_file_to_str(jobscript_path)

    db.replaceOne("jobs", {"_id": ObjectId(job["_id"])}, job)

    # update output if available
    # currently stdout and stderr point to the same file for non-CLI jobs -> provide only as stdout
    slurm_stdout = None
    slurm_stderr = None
    if directories is not None:
        output_path = directories["internal"]["outputs"] / "{}.out".format(
            jobId)

        if not output_path.is_file():
            return

        slurm_stdout = read_file_to_str(output_path)
    else:
        # read Slurm output location from job_info for CLI jobs in the hope that we have access the directory from within the container
        if "standardOutput" in job_info:
            # strip leading slash as concatenation of an absolute path will ignore all previous parts
            slurm_stdout_path = HOME_MOUNT_PREFIX / strip_first_slash(
                job_info["standardOutput"])
            if slurm_stdout_path.is_file():
                slurm_stdout = read_file_to_str(slurm_stdout_path)

        if "standardError" in job_info:
            # stderr is only saved if it differs from stdout
            if not ("standardOutput" in job_info) or (
                    "standardOutput" in job_info and
                    job_info["standardOutput"] != job_info["standardError"]):
                slurm_stderr_path = HOME_MOUNT_PREFIX / strip_first_slash(
                    job_info["standardError"])
                if slurm_stderr_path.is_file():
                    slurm_stderr = read_file_to_str(slurm_stderr_path)

    db.replaceOne("outputs", {"jobId": jobId}, {
        "runNr": job["runNr"],
        "jobId": jobId,
        "standardOutput": slurm_stdout,
        "standardError": slurm_stderr,
        "lastUpdate": get_current_datetime()
    },
                  upsert=True)


def process(runNr):
    """
    Continuously checks and updates all jobs of the provided runNr until all jobs are completed.
    
    :param runNr: runNr of the benchmark to process
    """
    logger.debug("Processing benchmark #%d", runNr)
    try:
        benchmark = db.getOne("benchmarks", {"runNr": runNr})

        if benchmark is None: raise exc.ProcessingError()

        directories = None

        if not benchmark["cli"]:
            # get user and home directory
            user = db.getOne("users", {"user_name": benchmark["issuer"]})

            if user is None:
                raise exc.ProcessingError()

            if not "homedirectory" in user or not user[
                    "homedirectory"] or not ("home" in user["homedirectory"]):
                logger.error(
                    "Retrieving results failed - invalid home-directory for user '%s'",
                    benchmark["issuer"])
                raise exc.ProcessingError()

            directories = get_xbat_directories(user["homedirectory"])

        job_infos = {}
        remaining_jobs = benchmark["jobIds"][:]
        iteration = 0
        # update issuer and name once for first job for CLI benchmarks
        # as CLI benchmarks can only have a single job at the moment use job name as benchmark name
        initial_update_required = True if benchmark["cli"] else False

        # even after force_refresh new jobs might not be immediately present in squeue --json output
        # therefore each job must at least be checked WATCH_MIN_ITERATIONS times
        # to prevent false positives in detecting that a job completed/failed
        while len(remaining_jobs):
            active_jobs = list(slurm.get_active_jobs().keys())

            current_job_info = slurm.get_jobs()

            for jobId in remaining_jobs[:]:  # copy list to allow removal of elements while iterating over it

                # save copy of job info for later as it may already be gone from slurm while we
                # are still waiting for all jobs to finish
                if jobId in current_job_info:
                    job_infos[jobId] = current_job_info[jobId]

                    if initial_update_required:
                        db.updateOne("benchmarks", {"runNr": runNr}, {
                            "$set": {
                                "issuer": job_infos[jobId]["userName"],
                                "name": job_infos[jobId]["name"]
                            }
                        })
                        initial_update_required = False

                _process_job(
                    jobId, directories, current_job_info[jobId]
                    if jobId in current_job_info else {})

                if not (jobId
                        in active_jobs) and iteration >= WATCH_MIN_ITERATIONS:
                    remaining_jobs.remove(jobId)

            time.sleep(JOB_STATE_INTERVAL)
            iteration += 1

        # once again update all jobs to ensure that all data is up-to-date
        # as very short jobs may slip through
        for jobId in benchmark["jobIds"]:
            slurm.update_job_scontrol(jobId)

        # and reprocess to persist the updated data
        current_job_info = slurm.get_jobs()
        for jobId in benchmark["jobIds"]:
            if jobId in current_job_info:
                job_infos[jobId] = current_job_info[jobId]
                _process_job(jobId, directories, current_job_info[jobId])

        state = "COMPLETED"
        for jobId in benchmark["jobIds"]:
            job_info = job_infos[jobId] if jobId in job_infos else {}
            # state of benchmark is most-critical job state
            if "jobState" in job_info:
                job_states = job_info["jobState"]
                # job state is a list as multiple states may apply to a job
                for job_state in job_states:
                    if job_state in STATES and STATES[job_state][
                            "value"] > STATES[state]["value"]:
                        state = job_state

        benchmark_update = {
            "endTime": get_current_datetime(),
            "state": STATES[state]["label"] if state in STATES else "failed"
        }

        # cli benchmarks are missing submission and end time
        # FYI can't set start_time at job registration as submit_time may differ from start_time
        if benchmark["cli"] and len(job_infos.keys()):
            # disclaimer: at the moment CLI benchmarks can only have a single job attached to them
            all_job_infos = job_infos.values()

            # submitTime of all jobs should be identical but this approach helps when a job is missing submitTime
            all_submit_times = [
                v["submitTime"] for v in all_job_infos if "submitTime" in v
            ]
            benchmark_update["startTime"] = iso8601_to_datetime(
                min(all_submit_times)) if len(all_submit_times) else None

            all_end_times = [
                v["endTime"] for v in all_job_infos if "endTime" in v
            ]
            benchmark_update["endTime"] = iso8601_to_datetime(
                max(all_end_times)) if len(all_end_times) else None

        db.updateOne("benchmarks", {"runNr": runNr},
                     {"$set": benchmark_update})

        logger.debug("Inserted data for benchmark #%d into database", runNr)

    except Exception as e:
        logger.error("Processing of benchmark #%d failed\n%s\n%s", runNr, e,
                     traceback.print_exc())

        error_msg = str(e)
        if isinstance(e, exc.ProcessingError) and len(
                exc.ProcessingError.args):
            error_msg = exc.ProcessingError.args[0]

        db.updateOne("benchmarks", {"runNr": runNr},
                     {"$set": {
                         "failureReason": error_msg,
                         "state": "failed"
                     }})
