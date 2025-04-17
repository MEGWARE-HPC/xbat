from shared import httpErrors
from shared.mongodb import MongoDB
from backend.restapi.user_helper import get_user_from_token

db = MongoDB()


def check_access(runNr=None, jobId=None):

    benchmark = None
    benchmarkFilter = None

    if runNr is not None:
        benchmarkFilter = {"runNr": runNr}
    elif jobId is not None:
        job = db.getOne("jobs", {"jobId": int(jobId)})
        if job is not None:
            benchmarkFilter = {"runNr": job["runNr"]}

    benchmark = db.getOne("benchmarks", benchmarkFilter)

    if benchmark is None: raise httpErrors.NotFound()

    user = get_user_from_token()

    if user is None: raise httpErrors.Unauthorized()

    if user["user_type"] == "admin" or user["user_type"] == "manager":
        return

    if benchmark["issuer"] != user["user_name"]:
        raise httpErrors.Forbidden()


def check_user_permissions(func):
    """
    Decorator to check if user has rights to delete or patch specified benchmark/job.

    Currently only the issuer of the benchmark/job and managers/admin are allowed to delete or patch.
    """

    def wrapper(*args, **kwargs):
        runNr = None
        jobId = None
        if "runNr" in kwargs:
            runNr = kwargs["runNr"]
        elif "jobId" in kwargs:
            jobId = kwargs["jobId"]

        if runNr is None and jobId is None:
            raise httpErrors.InternalServerError()

        check_access(runNr=runNr, jobId=jobId)

        return func(runNr or jobId)

    return wrapper
