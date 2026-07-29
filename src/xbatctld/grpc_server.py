import time
import grpc
import logging
import json
import threading
from concurrent import futures
from google.protobuf import empty_pb2
from google.protobuf import json_format
from google.protobuf.json_format import MessageToJson
from xbatctld.users import get_user_info
from xbatctld.slurm import SlurmConnector
from xbatctld.submission import create_benchmark_record, submit_benchmark_jobs

slurm = SlurmConnector()

from shared.grpc import xbat_pb2, xbat_pb2_grpc

logger = logging.getLogger("xbatctld")


class XbatCtldServicer(xbat_pb2_grpc.xbatctldServicer):

    def __init__(self):
        pass

    def SubmitBenchmark(self, request, context):
        """
        Submit a benchmark: create the record synchronously, submit jobs asynchronously.
        Returns immediately with runNr while jobs are submitted in background.
        """
        try:
            data = json.loads(MessageToJson(request))
            
            # Create benchmark and get runNr
            benchmark_info = create_benchmark_record(data)
            
            # Submit jobs 
            threading.Thread(
                target=submit_benchmark_jobs,
                args=(benchmark_info["benchmarkId"], benchmark_info["user"]),
                daemon=True
            ).start()
            
            # Return immediately with runNr
            benchmark_created = xbat_pb2.BenchmarkCreated()
            benchmark_created.runNr = benchmark_info["runNr"]
            
            return benchmark_created
            
        except Exception as e:
            logger.error(f"Failed to create benchmark: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            raise

    def GetNodes(self, request, context):
        node_data = xbat_pb2.NodeData()
        json_format.Parse(json.dumps({"nodes": slurm.get_nodes()}), node_data)
        return node_data

    def GetJobs(self, request, context):
        job_data = xbat_pb2.JobData()
        json_format.Parse(json.dumps({"jobs": slurm.get_jobs()}), job_data)
        return job_data

    def GetPartitions(self, request, context):
        partition_data = xbat_pb2.PartitionNodeMapping()
        json_format.Parse(json.dumps({"partitions": slurm.get_partitions()}),
                          partition_data)
        return partition_data

    def CancelJobs(self, request, context):
        result = slurm.cancel_jobs(request.jobIds)

        if not result:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Job cancellation failed")

        return empty_pb2.Empty()

    def GetUserInfo(self, request, context):
        user_data = xbat_pb2.UserData()
        user_info = get_user_info(request.userName)
        if user_info is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Unable to retrieve user information")
            return user_data
        user_info["userName"] = request.userName
        json_format.Parse(json.dumps(user_info), user_data)

        return user_data


def serve(cancelled):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    xbat_pb2_grpc.add_xbatctldServicer_to_server(XbatCtldServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    logger.debug("RPC server started on port 50051")

    while not cancelled.is_set():
        time.sleep(3)

    all_rpcs_done_event = server.stop(0)
    all_rpcs_done_event.wait(timeout=5)

    logger.debug("RPC server terminated")
