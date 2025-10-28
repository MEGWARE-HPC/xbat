import http
import os
import warnings
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple, TypeVar, cast
from urllib.parse import urlparse

import keyring
import requests
import urllib3


class AccessTokenError(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)


class MeasurementLevel(str, Enum):
    job = "job"
    node = "node"
    socket = "socket"
    numa = "numa"
    core = "core"
    thread = "thread"

    def __str__(self):
        return self.value


class MeasurementType(str, Enum):
    # TODO are there more?
    all = "all"
    cpu = "cpu"
    cache = "cache"
    memory = "memory"
    energy = "energy"
    interconnect = "interconnect"

    def __str__(self):
        return self.value


F = TypeVar("F", bound=Callable[..., Any])


def _localhost_suppress_security_warning(method: F) -> F:
    @wraps(method)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        host = getattr(self, "_Api__host", None)
        if host == "localhost":
            with warnings.catch_warnings():
                warnings.simplefilter(
                    "ignore", urllib3.exceptions.InsecureRequestWarning
                )
                return method(self, *args, **kwargs)
        else:
            return method(self, *args, **kwargs)

    return cast(F, wrapper)


class Api(object):
    def __init__(self, base_url: str, version: str, client_id: str):
        self.__base_url = base_url
        host = urlparse(self.__base_url).hostname
        assert host
        self.__host = host
        self.__token_url = f"{self.__base_url}/oauth/token"
        self.__api_version = version
        self.__api_url = f"{self.__base_url}/api/{self.__api_version}"
        self.__client_id = client_id
        self.__keyring_system = f"xbat-{self.__client_id}"
        self.__verify_ssl = self.__host != "localhost"

    @_localhost_suppress_security_warning
    def authorize(self, user: str, password: str):
        headers = {
            "accept": "text/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = dict(
            grant_type="password",
            username=user,
            password=password,
            client_id=self.__client_id,
        )
        token_response = requests.post(
            self.__token_url,
            headers=headers,
            data=data,
            verify=self.__verify_ssl,
        )
        if token_response.status_code == http.HTTPStatus.UNAUTHORIZED:
            raise AccessTokenError("Invalid credentials provided.")
        token_response.raise_for_status()
        access_token = token_response.json()["access_token"]
        try:
            keyring.set_password(self.__keyring_system, self.__host, access_token)
        except keyring.errors.NoKeyringError:
            pass
        return access_token

    @property
    def access_token(self):
        try:
            access_token = keyring.get_password(self.__keyring_system, self.__host)
        except keyring.errors.NoKeyringError:
            # Fall back on environment
            access_token = os.getenv("XBAT_ACCESS_TOKEN")
        if not access_token:
            raise AccessTokenError("No access token found.")
        return access_token

    @_localhost_suppress_security_warning
    def validate_access_token(self):
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.get(
            f"{self.__api_url}/current_user",
            headers=headers,
            verify=self.__verify_ssl,
        )
        if response.status_code == http.HTTPStatus.UNAUTHORIZED:
            raise AccessTokenError("Access token invalid.")
        response.raise_for_status()

    @property
    @_localhost_suppress_security_warning
    def benchmark_runs(self) -> List[Dict[str, Any]]:
        benchmark_runs_url = f"{self.__api_url}/benchmarks"
        headers = {
            "accept": "text/json",
            "Authorization": f"Bearer {self.access_token}",
        }
        response = requests.get(
            benchmark_runs_url,
            headers=headers,
            verify=self.__verify_ssl,
        )
        response.raise_for_status()
        return response.json()["data"]

    @_localhost_suppress_security_warning
    def get_jobs(
        self,
        run_ids: List[int] | None = None,
        job_ids: List[int] | None = None,
        short: bool = True,
    ) -> List[Dict[str, Any]]:
        jobs_url = f"{self.__api_url}/jobs?short={short}"
        if run_ids and False:  # FIXME Filtering by runs does not seem to work
            jobs_url += "&runNrs="
            for i, run in enumerate(run_ids):
                if i > 0:
                    jobs_url += ","
                jobs_url += str(run)
        if job_ids and False:  # FIXME Filtering by jobs does not seem to work
            jobs_url += "jobIds="
            for i, job in enumerate(job_ids):
                if i > 0:
                    jobs_url += ","
                jobs_url += str(job)
        headers = {
            "accept": "text/json",
            "Authorization": f"Bearer {self.access_token}",
        }
        response = requests.get(
            jobs_url,
            headers=headers,
            verify=self.__verify_ssl,
        )
        response.raise_for_status()
        jobs = response.json()["data"]
        # FIXME Workaround for issues above
        if run_ids:
            jobs = [j for j in jobs if j["runNr"] in run_ids]
        if job_ids:
            jobs = [j for j in jobs if j["jobId"] in job_ids]
        return jobs

    @_localhost_suppress_security_warning
    def get_job_output(self, job_id: int) -> Tuple[str, str]:
        jobs_url = f"{self.__api_url}/jobs/{job_id}/output"
        headers = {
            "accept": "text/json",
            "Authorization": f"Bearer {self.access_token}",
        }
        response = requests.get(
            jobs_url,
            headers=headers,
            verify=self.__verify_ssl,
        )
        response.raise_for_status()
        output = response.json()
        return output["standardOutput"], output["standardError"]

    @_localhost_suppress_security_warning
    def get_job_metrics(self, job_id: int) -> List[str]:
        jobs_url = f"{self.__api_url}/jobs/{job_id}/metrics"
        headers = {
            "accept": "text/json",
            "Authorization": f"Bearer {self.access_token}",
        }
        response = requests.get(
            jobs_url,
            headers=headers,
            verify=self.__verify_ssl,
        )
        response.raise_for_status()
        output = response.json()
        print(output)
        exit()

    @_localhost_suppress_security_warning
    def download_job_measurements(
        self,
        job_id: int,
        output_path: Path,
        type: MeasurementType,
        metric: str | None,
        level: MeasurementLevel,
        node: str | None,
        progress_callback: Callable[[float], None] | None = None,
    ) -> Path:
        if not isinstance(job_id, int):
            raise ValueError("job_id must be an integer.")
        if metric and type == MeasurementType.all:
            raise ValueError('Cannot select metric when type is "all".')
        if not node and level == MeasurementLevel.node:
            raise ValueError('Node must be provided when level is "node"')
        params: Dict[str, Any] = dict(level=level)
        if type != MeasurementType.all:
            params["group"] = type
        if metric:
            params["metric"] = metric
        if node:
            params["node"] = node
        for k, v in params.items():
            params[k] = str(v)
        measurement_url = f"{self.__api_url}/measurements/{job_id}/csv"
        headers = {"accept": "text/csv", "Authorization": f"Bearer {self.access_token}"}
        response = requests.get(
            measurement_url,
            headers=headers,
            params=params,
            stream=True,
            verify=self.__verify_ssl,
        )
        if response.status_code == http.HTTPStatus.OK:
            total = int(response.headers.get("content-length", 0))
            downloaded = 0
            chunk_size = 8192
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            progress_callback(downloaded / total)
        elif response.status_code == http.HTTPStatus.NOT_FOUND:
            raise FileNotFoundError(
                f"job_id {job_id} or combination of job_id, type, and metric not found."
            )
        response.raise_for_status()
        return output_path

    @_localhost_suppress_security_warning
    def export_runs(
        self,
        run_ids: List[int],
        output_path: Path,
        anonymise: bool = False,
        progress_callback: Callable[[float], None] | None = None,
    ) -> Path:
        export_url = f"{self.__api_url}/benchmarks/export"
        headers = {
            "accept": "application/octet-stream",
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "runNrs": run_ids,
            "anonymise": anonymise,
        }
        response = requests.post(
            export_url,
            headers=headers,
            json=payload,
            stream=True,
            verify=self.__verify_ssl,
        )
        if response.status_code == http.HTTPStatus.NO_CONTENT:
            raise FileNotFoundError("No benchmark data available for export.")
        response.raise_for_status()
        total = int(response.headers.get("content-length", 0))
        downloaded = 0
        chunk_size = 8192
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total:
                        progress_callback(downloaded / total)
        return output_path
