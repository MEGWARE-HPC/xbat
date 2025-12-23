import itertools
import logging
import os
import traceback
from bson.objectid import ObjectId
from pathlib import Path
from shared import exc
from shared.mongodb import MongoDB
from shared.helpers import convert_jobscript_to_v0160
from shared.files import read_file_to_str, write_to_file, dir_permissions_match
from xbatctld.paths import get_xbat_directories
from xbatctld.slurm import SlurmConnector
from xbatctld.users import dir_owned_by_user

logger = logging.getLogger("xbatctld")
db = MongoDB()
TIMEOUT = 15

BASE_PATH = Path().absolute()
INTERNAL_VARIANT_PATH = Path("/tmp/variants")
JOB_SCRIPTS_PATH = BASE_PATH / "scripts"
JOB_SCRIPT_IN_PATH = BASE_PATH / "inputs" / "jobscript.sh.in"
USER_JOB_SCRIPT_IN_PATH = BASE_PATH / "inputs" / "userJobscript.sh.in"

JOB_SCRIPT_IN = read_file_to_str(str(JOB_SCRIPT_IN_PATH))
USER_JOB_SCRIPT_IN = read_file_to_str(str(USER_JOB_SCRIPT_IN_PATH))

METRICS = ["cpu", "memory", "io", "interconnect", "gpu", "energy"]

DIRECTORY_PERMISSIONS = 0o755
FILE_PERMISSIONS_EXECUTABLE = 0o755


def _substitute(config, dest):
    for entry in config:
        marker = "#{}#".format(entry.upper())
        if marker in dest:
            dest = dest.replace(
                marker,
                str(config[entry]) if not isinstance(config[entry], list) else
                ",".join(config[entry]))
    return dest


def _generate_variable_permutations(variables):
    single_value_variables = {}
    multi_value_variables = []
    for var in variables:
        if not len(var["key"]) or not len(var["selected"]):
            continue
        if len(var["selected"]) == 1:
            single_value_variables[var["key"]] = var["selected"][0] or ""
        else:
            multi_value_variables.append(
                list(itertools.product(*[[var["key"]], var["selected"]])))
    multi_value_permutations = list(itertools.product(*multi_value_variables))

    variable_permutations = []
    for perm in multi_value_permutations:
        variable_permutations.append({**single_value_variables, **dict(perm)})

    return variable_permutations


def _prepare_permutations(benchmarkId, output_path, log_path):
    if not JOB_SCRIPT_IN_PATH.is_file():
        logger.error("Job script '{}' not found".format(JOB_SCRIPT_IN_PATH))
        return []

    benchmark = db.getOne("benchmarks", {"_id": ObjectId(benchmarkId)})

    if benchmark is None:
        return []

    config = benchmark["configuration"]["configuration"]
    variables = benchmark["variables"]

    variable_permutations = _generate_variable_permutations(variables)

    permutations = []
    permutation_nr = 0
    for variant in range(0, len(config["jobscript"])):
        for variable_permutation in variable_permutations:
            for iteration in range(0, config["iterations"]):

                # get variant specific configuration
                variant_data = dict(config)
                job_variant = dict(variant_data["jobscript"][variant])

                variant_data["jobscript"] = convert_jobscript_to_v0160(
                    job_variant)
                variant_data = {
                    **variant_data, "OUTPUT_DIRECTORY":
                    str(output_path / "%j.out"),
                    "LOG_DIRECTORY": str(log_path)
                }

                input_data = {
                    **variant_data,
                    **job_variant,
                    # substitution of start/stop for measurements (will only take effect if the jobscript contains the respective markers)
                    "xbat-start":
                    f'echo "captureStart=$(date +%s)" >> "{log_path}/${{SLURM_JOBID}}.time.log" || true',
                    "xbat-stop":
                    f'echo "captureEnd=$(date +%s)" >> "{log_path}/${{SLURM_JOBID}}.time.log" || true',
                }

                if len(input_data["job-name"]):
                    input_data["job-name"] = input_data["job-name"].replace(
                        " ", "_")  # slurm job name cannot contain spaces
                else:
                    input_data[
                        "job-name"] = f"{benchmark['runNr']}-{config['configurationName'].replace(' ', '_')}-{input_data['variantName'].replace(' ', '_')}-{iteration}"

                # jobscript as submitted to job scheduler
                jobscript_str = _substitute(input_data, JOB_SCRIPT_IN)

                # jobscript as configured by user for frontend
                user_jobscript_str = _substitute(
                    {
                        **input_data, "xbat-start":
                        "## starting measurement ##",
                        "xbat-stop": "## xbat stopping measurement ##"
                    }, USER_JOB_SCRIPT_IN)

                # empty nodelist directive (which is supported by the frontend) leads to Slurm error "Requested node configuration is not available"
                # comment out directive in this case
                if "nodelist" in input_data and not len(
                        input_data["nodelist"]):
                    nodelist_directive = "#SBATCH --nodelist="
                    jobscript_str = jobscript_str.replace(
                        nodelist_directive, "#" + nodelist_directive)
                    user_jobscript_str = user_jobscript_str.replace(
                        nodelist_directive, "#" + nodelist_directive)

                permutations.append({
                    "configuration":
                    variant_data,
                    "identificator":
                    "{}-{}-{}".format(benchmark["runNr"], variant, iteration),
                    "iteration":
                    iteration,
                    "jobId":
                    None,
                    "jobscriptFile":
                    jobscript_str,
                    "userJobscriptFile":
                    user_jobscript_str,
                    "permutationNr":
                    permutation_nr,
                    "runNr":
                    benchmark["runNr"],
                    "variables":
                    variable_permutation,
                    "nodes": {},
                    "cli":
                    False
                })
                permutation_nr += 1
    return permutations


def create_benchmark_record(data):
    """
    Creates a benchmark record in the database and validates user data.
    
    Args:
        data: benchmark creation data (issuer, name, configId, variables, sharedProjects)
    
    Returns:
        dict with benchmarkId, runNr, name, state, and user info
    
    Raises:
        exc.SetupError: if benchmark creation or user validation fails
    """
    logger.debug("Creating benchmark record with: %s", data)

    try:
        benchmarkId = db.createBenchmark(**data)

        if not benchmarkId:
            raise exc.SetupError("Failed to create benchmark in database")

        # Get the created benchmark to retrieve runNr
        benchmark = db.getOne("benchmarks", {"_id": ObjectId(benchmarkId)})
        if not benchmark:
            raise exc.SetupError("Failed to retrieve created benchmark")

        runNr = benchmark.get("runNr")
        name = benchmark.get("name", data.get("name", ""))
        state = benchmark.get("state", "pending")

        # Validate user data
        user = db.getOne("users", {"user_name": data["issuer"]})

        if user is None or not {
                "uidnumber", "gidnumber", "homedirectory"
        } <= user.keys() or not user["uidnumber"] or not user[
                "gidnumber"] or not user["homedirectory"] or not (
                    "home" in user["homedirectory"]):
            # Mark benchmark as failed before raising
            db.updateOne("benchmarks", {"_id": ObjectId(benchmarkId)}, {
                "$set": {
                    "failureReason": "Invalid user data",
                    "state": "failed"
                }
            })
            raise exc.SetupError("Invalid user data")

        logger.debug("Created benchmark %s with runNr %s", benchmarkId, runNr)

        return {
            "benchmarkId": str(benchmarkId),
            "runNr": runNr,
            "name": name,
            "state": state,
            "user": user
        }

    except Exception as e:
        logger.error("Failed to create benchmark record: %s", e)
        raise


def submit_benchmark_jobs(benchmarkId, user):
    """
    Submits benchmark jobs to Slurm (asynchronous part).
    
    Args:
        benchmarkId: benchmark database id (as string)
        user: user data containing name, uid, gid and homedirectory
    """
    logger.debug("Submitting jobs for benchmark %s", benchmarkId)

    try:
        jobIds = submit(benchmarkId, user)

        if len(jobIds):
            logger.debug("Submitted benchmark %s with job ids [%s]",
                         benchmarkId, ",".join([str(j) for j in jobIds]))
            db.updateOne("benchmarks", {"_id": ObjectId(benchmarkId)},
                         {"$set": {
                             "jobIds": jobIds,
                             "state": "running"
                         }})
        else:
            logger.warning("No jobs submitted for benchmark %s", benchmarkId)
            db.updateOne("benchmarks", {"_id": ObjectId(benchmarkId)}, {
                "$set": {
                    "failureReason": "No jobs were submitted",
                    "state": "failed"
                }
            })

    except Exception as e:
        logger.error("Submission of benchmark %s jobs failed: %s\n%s",
                     benchmarkId, e, traceback.format_exc())

        error_msg = str(e)
        if not (isinstance(e, exc.SetupError)
                or isinstance(e, exc.SubmissionError)):
            error_msg = exc.SubmissionError().args[0]

        db.updateOne("benchmarks", {"_id": ObjectId(benchmarkId)},
                     {"$set": {
                         "failureReason": error_msg,
                         "state": "failed"
                     }})


#TODO get UID/GID/HOMEDIR from database
def submit(benchmarkId, user):
    """
    Submits a benchmark to Slurm.

    Creates all necessary directories and puts the jobscript into the users home directory.

    Args:
        benchmarkId: benchmark database id
        user: user data containing name, uid, gid and homedirectory
    """
    username = user["user_name"]
    homedir = user["homedirectory"]
    uid = int(user["uidnumber"])
    gid = int(user["gidnumber"])

    INTERNAL_VARIANT_PATH.mkdir(parents=True, exist_ok=True)

    directories = get_xbat_directories(homedir)

    required_directories = list(directories["internal"].values())

    # TODO check if su - <user> mkdir <dir> would be a better option (and how to allow exist_ok in bash without potentially creating missing parent directories)
    # ensure all directories are present and have the correct permissions
    for d in required_directories:
        if not d.is_dir():
            logger.debug("Creating directory '%s'", str(d))
            d.mkdir(
                exist_ok=True
            )  # exist_ok in case two simoultaneous submissions try to create the same directory
        if not dir_owned_by_user(d, username, uid, gid):
            logger.debug("Changing owner of '%s' to '%s", str(d), username)
            os.chown(d, uid, gid)

        if not dir_permissions_match(d, DIRECTORY_PERMISSIONS):
            logger.debug("Changing permissions of '%s' to '%s", str(d),
                         oct(DIRECTORY_PERMISSIONS))
            os.chmod(d, DIRECTORY_PERMISSIONS)

    # generate permutations (from variants and iterations)
    permutations = _prepare_permutations(benchmarkId,
                                         directories["external"]["outputs"],
                                         directories["external"]["logs"])
    jobIds = []
    for perm in permutations:
        jobscript_name = "{}.sh".format(perm["identificator"])

        jobscript_external = directories["external"][
            "jobscripts"] / jobscript_name
        jobscript_internal = directories["internal"][
            "jobscripts"] / jobscript_name

        write_to_file(jobscript_internal, perm["jobscriptFile"])
        os.chmod(jobscript_internal, FILE_PERMISSIONS_EXECUTABLE)
        os.chown(jobscript_internal, uid, gid)

        jobId = SlurmConnector.submit(username, jobscript_external, homedir,
                                      perm["configuration"]["jobscript"],
                                      perm["variables"])

        if jobId is None:
            continue

        jobIds.append(jobId)

        data = {**perm, "jobId": jobId}
        insert = db.insertOne("jobs", data)

        if not insert.acknowledged:
            logger.error("Error inserting job into database - \n%s", data)
            raise exc.SetupError()

    return jobIds
