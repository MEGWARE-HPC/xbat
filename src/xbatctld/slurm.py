import threading
import datetime
import logging
import json
import re
from pathlib import Path
from xbatctld.pipe import execute_on_host
from shared import configuration as app_configuration, exc
from shared.helpers import keys_exist, Singleton, to_camel_case
from shared.files import read_file_to_str
from shared.date import get_current_timestamp, iso8601_to_datetime, unix_ts_to_datetime_str, get_current_datetime

logger = logging.getLogger("xbatctld")

TESTDATA_PATH = Path(__file__).parent.resolve() / "testdata"

REFRESH_TIMER = 30

lock = threading.Lock()


def use_testdata():
    return app_configuration.get_build(
    ) == "dev" or app_configuration.get_demo()


class SlurmConnector(object, metaclass=Singleton):
    """SlurmConnector is a stateful interface to the Slurm commandline."""
    last_update = None
    previously_recorded_jobs = []
    jobs = {}
    nodes = {}
    partitions = {}
    _sinfo = {}
    _squeue = {}
    version = {}

    def __init__(self):
        self.get_slurm_version()

    def _validate_data(func):
        """Decorator refreshing data if older than REFRESH_TIMER seconds"""

        def check(self, *args, **kwargs):
            with lock:
                if "force_refresh" in kwargs and kwargs["force_refresh"]:
                    self.last_update = None

                if self.last_update is None or (
                        get_current_timestamp() -
                        self.last_update) >= REFRESH_TIMER:
                    logger.debug("Refreshing data")
                    self._get_squeue()
                    self._get_sinfo()
                    self._set_last_update()

            return func(self, *args, **kwargs)

        return check

    def _replace_patterns(self, input, job):
        return input.replace("%j", str(job["jobId"])).replace(
            "%u", job["userName"]).replace("%x", job["name"])

    def _set_last_update(self):
        """Set last_update as current timestamp."""
        self.last_update = get_current_timestamp()

    def force_refresh(self):
        """Reset last_update to force refresh of data upon next request - usefull after job submission to not be stuck with old data."""
        with lock:
            self.last_update = None

    @_validate_data
    def get_jobs(self, force_refresh=False):
        """Returns all jobs.
        
        :param force_refresh: instruct validation decorator to force refresh of data
        """
        return self.jobs

    @_validate_data
    def get_active_jobs(self, force_refresh=False):
        """
        Returns all jobs that have not ended yet.

        Contrary to plain "squeue" jobs are present in "squeue --json" after completion for some time.

        :param force_refresh: instruct validation decorator to force refresh of data
        """
        with lock:
            active = {}
            for jobId, job in self.jobs.items():
                non_active = [
                    "FAILED", "CANCELLED", "COMPLETED", "TIMEOUT", "DEADLINE"
                ]

                if not True in [
                        state in job["jobState"] for state in non_active
                ]:
                    active[jobId] = job

            return active

    @_validate_data
    def get_nodes(self, force_refresh=False):
        """Returns all nodes.
        
        :param force_refresh: instruct validation decorator to force refresh of data
        """
        with lock:
            return self.nodes

    @_validate_data
    def get_partitions(self, force_refresh=False):
        """Returns parsed partitions.
        
        :param force_refresh: instruct validation decorator to force refresh of data
        """
        with lock:
            return self.partitions

    def get_slurm_version(self):
        """Detects slurm version."""
        if use_testdata():
            self.version = {"major": 22, "micro": 6, "minor": 5}
        else:
            [ret, output] = execute_on_host("sinfo --json")
            if ret != 0:
                logger.error("[%s] Error calling sinfo %s", ret, output)
                return

            output = json.loads(output)

            # TODO refactor
            if keys_exist(output, "meta", "slurm", "version"):
                self.version = output["meta"]["slurm"]["version"]
            elif keys_exist(output, "meta", "Slurm", "version"):
                self.version = output["meta"]["Slurm"]["version"]
            else:
                logger.error("Could not determine Slurm version")

    def update_job_scontrol(self, job_id):
        """Updates job by parsing 'scontrol show job'.

        This is used to update job information directly (e.g. after job completion as it may no longer be present in squeue).
        
        :param job_id: job id
        """
        if use_testdata():
            return

        [ret, output] = execute_on_host(f"scontrol show job {job_id} --json")
        if ret != 0:
            logger.error("[%s] Error calling scontrol show job %s", ret,
                         output)
            return

        output = json.loads(output or "{}")

        if not ("jobs" in output) or not len(output["jobs"]):
            return

        ret = self._parse_job(output["jobs"][0])

        if not bool(ret):
            return

        self.jobs[int(job_id)] = ret

    def _parse_job(self, job):

        keys = [
            'batch_host', 'cluster', 'command', 'current_working_directory',
            'job_id', 'job_state', 'name', 'nodes', 'partition',
            'standard_error', 'standard_output', 'user_name'
        ]

        time_keys = ["end_time", "start_time", "submit_time"]

        all_keys = [*keys, *time_keys]

        # only capture jobs that are started with the "xbat" constraint
        if not ("xbat" in job["features"]):
            return {}

        job_info = {}

        for k, v in job.items():
            if not (k in all_keys): continue
            # some values stored differently across slurm versions
            if isinstance(v, dict) and "number" in v:
                v = v["number"]
            if k in time_keys:
                v = unix_ts_to_datetime_str(v) if v != 0 else None
            job_info[to_camel_case(k)] = v

        # replace common patterns in paths
        # TODO extend to all patterns
        job_info["standardOutput"] = self._replace_patterns(
            job_info["standardOutput"], job_info)

        job_info["standardError"] = self._replace_patterns(
            job_info["standardError"], job_info)

        if not isinstance(job_info["jobState"], list):
            job_info["jobState"] = [job_info["jobState"]]

        return job_info

    def _get_squeue(self):
        """Retrieves and processes job information from Slurm squeue - returns camelCase."""

        output = ""
        if use_testdata():
            output = read_file_to_str(TESTDATA_PATH / "squeue --json v22")
        else:
            [ret, output] = execute_on_host("squeue --json --all")
            if ret != 0:
                logger.error("[%s] Error calling squeue %s", ret, output)
                output = ""

        output = json.loads(output or "{}")

        if not ("jobs" in output):
            return

        recorded_jobs = []

        for job in output["jobs"]:
            ret = self._parse_job(job)
            if not bool(ret):
                continue
            job_id = int(job["job_id"])
            self.jobs[job_id] = ret
            recorded_jobs.append(job_id)

        if use_testdata():
            return

        # get all jobs that are dropped from squeue
        # these must be updated one more time via scontrol as their last squeue record may be incomplete or outdated
        dropped = list(set(self.previously_recorded_jobs) - set(recorded_jobs))

        self.previously_recorded_jobs = recorded_jobs

        for job_id in dropped:
            self.update_job_scontrol(job_id)

        # drop all jobs that ended more than 7days ago to prevent "memory leak"
        max_time = get_current_datetime() - datetime.timedelta(days=7)

        delete = []
        for job_id in self.jobs:
            end_time = self.jobs[job_id]["endTime"]
            if end_time is None or end_time == 0: continue
            if iso8601_to_datetime(end_time) < max_time:
                delete.append(job_id)

        for job_id in delete:
            del self.jobs[job_id]

    def _get_sinfo(self):
        """Retrieves and processes node/partition information from Slurm sinfo - returns camelCase."""

        output = ""
        if use_testdata():
            output = read_file_to_str(TESTDATA_PATH / "sinfo --json v22")
        else:

            if not bool(self.version):
                return

            # slurm v23 changed output of "sinfo --json" -> use scontrol for legacy output
            [ret,
             output] = execute_on_host("scontrol show nodes --json" if int(
                 self.version["major"]) > 22 else "sinfo --json")
            if ret != 0:
                logger.error("[%s] Error calling sinfo %s", ret, output)
                output = ""

        output = json.loads(output or "{}")

        nodes = {}
        partitions = {}

        if not ("nodes" in output):
            return

        keys = [
            "hostname",
            "cpus",
            "cores",
            "threads",
            "state",
            "state_flags",
            "partitions",
            "sockets",
            "real_memory",
        ]

        for node in output["nodes"]:
            hostname = node["hostname"]
            nodes[hostname] = {
                to_camel_case(k): v
                for k, v in node.items() if k in keys
            }
            if "partitions" in node:
                for partition in node["partitions"]:
                    if not (partition in partitions):
                        partitions[partition] = []
                    partitions[partition].append(hostname)

        self.nodes = nodes
        self.partitions = partitions

    @classmethod
    def cancel_jobs(cls, ids=[]):
        """
        Class method canceling all provided jobs.
        
        :param ids: list of job ids
        :return: success or failure of operation
        """

        if use_testdata():
            return True

        [ret, _] = execute_on_host("scancel {}".format(" ".join(
            [str(i) for i in ids])))
        if ret != 0:
            logging.error("Could not cancel jobs %s", ids)
            return False

        # force refresh
        cls.last_update = None

        return True

    @classmethod
    def submit(cls,
               username,
               jobscript_path,
               homedir,
               configuration,
               variables={}):
        """Class method to submit job to Slurm and return the job ID."""

        exports = ""
        for key in variables:
            if len(exports):
                exports += ","
            exports += "{}={}".format(key, variables[key])

        command = "sbatch --constraint xbat --chdir={} --exclusive --wait-all-nodes=1".format(
            homedir)

        if len(exports):
            command += " --export={}".format(exports)

        if ("nodelist" in configuration and len(configuration["nodelist"])):
            command += " --nodelist={}".format(configuration["nodelist"])

        command += " {}".format(jobscript_path)

        # TODO move wrapping to execute_on_host
        user_wrapped_command = 'su - {} -c "{}"'.format(username, command)

        [ret, output] = execute_on_host(user_wrapped_command)
        if ret != 0:
            logger.error("[%s] Error submitting jobscript %s", ret, output)
            raise exc.SubmissionError(f"Submission of job failed - {output}")

        submitted = re.findall(r'\d+', output)

        if not len(submitted) or submitted[0] == "":
            logger.error("Could not determine job ID from submission")
            return None

        jobId = int(submitted[0])
        logger.debug("Submitted job %d", jobId)

        return jobId
