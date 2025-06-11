import grpc
import json
from flask import current_app as app
import google.protobuf.empty_pb2 as empty_pb2
from google.protobuf.json_format import MessageToJson
from shared.grpc import xbat_pb2, xbat_pb2_grpc
import time

ADDRESS = "localhost:50051" if app.config[
    "BUILD"] == "dev" else "xbat-ctld:50051"


class XbatCtldRpcClient:

    def __init__(self):
        options = [('grpc.keepalive_time_ms', 60000),
                   ('grpc.keepalive_timeout_ms', 20000),
                   ('grpc.http2.min_time_between_pings_ms', 30000),
                   ('grpc.http2.max_pings_without_data', 5),
                   ('grpc.http2.keepalive_permit_without_calls', True)]
        self.channel = grpc.insecure_channel(ADDRESS, options=options)
        self.stub = xbat_pb2_grpc.xbatctldStub(self.channel)

    def close(self):
        self.channel.close()

    def _retry_rpc(func):
        max_retries = 3
        initial_delay = 1

        def wrapper(self, *args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(self, *args, **kwargs)
                except grpc.RpcError as e:
                    if e.code(
                    ) == grpc.StatusCode.UNAVAILABLE and attempt < max_retries - 1:
                        app.logger.warning(
                            f"RPC call failed with {e}, retrying ({attempt + 1}/{max_retries})..."
                        )
                        time.sleep(initial_delay * (2**attempt))
                    else:
                        raise

        return wrapper

    @_retry_rpc
    def get_nodes(self):
        try:
            response = self.stub.GetNodes(empty_pb2.Empty())
            data = json.loads(MessageToJson(response))
            return data["nodes"] if "nodes" in data else {}
        except grpc.RpcError as e:
            app.logger.error(f"Failed to get node data: {e}")
        return None

    @_retry_rpc
    def get_jobs(self):
        try:
            response = self.stub.GetJobs(empty_pb2.Empty())
            data = json.loads(MessageToJson(response))
            return data["jobs"] if "jobs" in data else {}
        except grpc.RpcError as e:
            app.logger.error(f"Failed to get job data: {e}")
        return None

    @_retry_rpc
    def get_partitions(self):
        try:
            response = self.stub.GetPartitions(empty_pb2.Empty())
            data = json.loads(MessageToJson(response))
            return data["partitions"] if "partitions" in data else {}
        except grpc.RpcError as e:
            app.logger.error(f"Failed to get partition data: {e}")
        return None

    @_retry_rpc
    def submit_benchmark(self, data):
        try:
            new_benchmark = xbat_pb2.NewBenchmark(**data)
            self.stub.SubmitBenchmark(new_benchmark)
            return True
        except grpc.RpcError as e:
            app.logger.error(f"Failed to submit benchmark: {e}")
        return False

    @_retry_rpc
    def get_user_info(self, user_name):
        try:
            user_request = xbat_pb2.UserName(userName=user_name)
            user_response = self.stub.GetUserInfo(user_request)
            return json.loads(MessageToJson(user_response))
        except grpc.RpcError as e:
            app.logger.error(f"Failed to get user info: {e}")
        return None

    @_retry_rpc
    def cancel_jobs(self, job_ids):
        try:
            job_ids_request = xbat_pb2.JobIds(jobIds=job_ids)
            self.stub.CancelJobs(job_ids_request)
        except grpc.RpcError as e:
            app.logger.error(f"Failed to cancel jobs: {e}")
            return False
        return True

    @_retry_rpc
    def purge_questdb(self):
        try:
            self.stub.PurgeQuestDB(empty_pb2.Empty())
            return True
        except grpc.RpcError as e:
            app.logger.error(f"Failed to purge QuestDB: {e}")
        return False
