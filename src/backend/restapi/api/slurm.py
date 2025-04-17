from shared import httpErrors
from shared.mongodb import MongoDB
from shared.braceNotation import encode_brace_notation
from backend.restapi.access_control import check_access, check_user_permissions
from backend.restapi.api.benchmarks import get_user_benchmarks
from backend.restapi.grpc_client import XbatCtldRpcClient

db = MongoDB()

rpcClient = XbatCtldRpcClient()


def get_nodes():
    nodes = rpcClient.get_nodes()
    if nodes is None:
        raise httpErrors.InternalServerError("Failed to get Slurm nodes")
    return nodes, 200


def get_jobs():
    jobs = rpcClient.get_jobs()
    if jobs is None:
        raise httpErrors.InternalServerError("Failed to get Slurm jobs")
    return rpcClient.get_jobs(), 200


def get_partitions():
    partitions = rpcClient.get_partitions()
    if partitions is None:
        raise httpErrors.InternalServerError("Failed to get Slurm partitions")
    for p in partitions:
        partitions[p] = encode_brace_notation(partitions[p])
    return partitions, 200


@check_user_permissions
def cancel_benchmark(runNr):
    benchmark = get_user_benchmarks(runNrs=[runNr])

    if not len(benchmark):
        raise httpErrors.NotFound()

    benchmark = benchmark[0]

    if not ("jobIds" in benchmark) or not len(benchmark["jobIds"]):
        return {}, 200

    response = rpcClient.cancel_jobs(benchmark["jobIds"])

    if not response:
        raise httpErrors.InternalServerError("Failed to cancel benchmark")

    return {}, 204


def cancel_job(jobId):
    benchmark = db.getOne("benchmarks", {"jobIds": jobId})
    if benchmark is None: raise httpErrors.NotFound()

    check_access(runNr=benchmark["runNr"])

    response = rpcClient.cancel_jobs([jobId])

    if not response:
        raise httpErrors.InternalServerError("Failed to cancel job")

    return {}, 204
