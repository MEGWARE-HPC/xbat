import grpc
import json
from flask import current_app as app
import google.protobuf.empty_pb2 as empty_pb2
from google.protobuf.json_format import MessageToJson
from shared.grpc import xbat_pb2, xbat_pb2_grpc

ADDRESS = "localhost:50051" if app.config[
    "BUILD"] == "dev" else "xbat-ctld:50051"


class XbatCtldRpcClient:

    def __init__(self):
        options = [('grpc.keepalive_time_ms', 30000),
                   ('grpc.keepalive_timeout_ms', 10000),
                   ('grpc.http2.min_ping_interval_without_data_ms', 15000),
                   ('grpc.http2.max_pings_without_data', 0),
                   ('grpc.keepalive_permit_without_calls', 1)]
        self.channel = grpc.insecure_channel(ADDRESS, options=options)
        self.stub = xbat_pb2_grpc.xbatctldStub(self.channel)

    def close(self):
        self.channel.close()

    def get_nodes(self):
        try:
            response = self.stub.GetNodes(empty_pb2.Empty())
            data = json.loads(MessageToJson(response))
            return data["nodes"] if "nodes" in data else {}
        except grpc.RpcError as e:
            app.logger.error(f"Failed to get node data: {e}")
        return None

    def get_jobs(self):
        try:
            response = self.stub.GetJobs(empty_pb2.Empty())
            data = json.loads(MessageToJson(response))
            return data["jobs"] if "jobs" in data else {}
        except grpc.RpcError as e:
            app.logger.error(f"Failed to get job data: {e}")
        return None

    def get_partitions(self):
        try:
            response = self.stub.GetPartitions(empty_pb2.Empty())
            data = json.loads(MessageToJson(response))
            return data["partitions"] if "partitions" in data else {}
        except grpc.RpcError as e:
            app.logger.error(f"Failed to get partition data: {e}")
        return None

    def submit_benchmark(self, data):
        try:
            new_benchmark = xbat_pb2.NewBenchmark(**data)
            self.stub.SubmitBenchmark(new_benchmark)
            return True
        except grpc.RpcError as e:
            app.logger.error(f"Failed to submit benchmark: {e}")
        return False

    def get_user_info(self, user_name):
        try:
            user_request = xbat_pb2.UserName(userName=user_name)
            user_response = self.stub.GetUserInfo(user_request)
            return json.loads(MessageToJson(user_response))
        except grpc.RpcError as e:
            app.logger.error(f"Failed to get user info: {e}")
        return None

    def cancel_jobs(self, job_ids):
        try:
            job_ids_request = xbat_pb2.JobIds(jobIds=job_ids)
            self.stub.CancelJobs(job_ids_request)
        except grpc.RpcError as e:
            app.logger.error(f"Failed to cancel jobs: {e}")
            return False
        return True

    def purge_questdb(self):
        try:
            self.stub.PurgeQuestDB(empty_pb2.Empty())
            return True
        except grpc.RpcError as e:
            app.logger.error(f"Failed to purge QuestDB: {e}")
        return False
