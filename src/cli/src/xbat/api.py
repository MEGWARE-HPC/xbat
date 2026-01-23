from dataclasses import dataclass
import http
import json
import os
import warnings
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Iterable, TypeVar, cast
from urllib.parse import urlparse

import keyring
from keyrings.alt.file import PlaintextKeyring  # type: ignore[import-untyped]
import keyring.backend
from keyring.errors import NoKeyringError
import requests
import urllib3


class AccessTokenError(Exception):
    def __init__(self, reason: str, no_credentials: bool = True) -> None:
        super().__init__(reason)
        self.no_credentials = no_credentials


class MeasurementLevel(str, Enum):
    job = "job"
    node = "node"
    socket = "socket"
    numa = "numa"
    core = "core"
    thread = "thread"

    def __str__(self) -> str:
        return self.value


class MeasurementGroup(str, Enum):
    cpu = "cpu"
    cache = "cache"
    memory = "memory"
    energy = "energy"
    interconnect = "interconnect"

    def __str__(self) -> str:
        return self.value


@dataclass
class Project:
    project_id: str
    name: str


@dataclass
class Configuration:
    config_id: str
    name: str
    shared_projects: list[Project]

    def __str__(self) -> str:
        if len(self.shared_projects) > 0:
            return f"{self.name} ({', '.join([p.name for p in self.shared_projects])})"
        else:
            return self.name


@dataclass
class BenchmarkRun:
    run_number: int
    name: str
    issuer: str
    config_id: str | None
    config_name: str | None
    state: str
    job_ids: list[int]


@dataclass
class Job:
    job_id: int
    state: str
    run_number: int
    variant: str | None
    node_hashes: set[str]


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
    def __init__(
        self,
        base_url: str,
        version: str,
        client_id: str,
    ) -> None:
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
        self.__access_token: str | None = None
        self.__init_noninteractive_keyring()

    def __init_noninteractive_keyring(self):
        old_umask = os.umask(0o077)  # Ensure restricted access to keyring file
        unsuitable_backends = set(
            [
                "FailKeyring",
                "ChainerBackend",
                "PlaintextKeyring",  # Only explicit fallback
                "CryptFileKeyring",  # Interactive only
            ]
        )
        try:
            has_suitable = False
            for backend in keyring.backend.get_all_keyring():
                name = backend.__class__.__name__
                priority = getattr(backend, "priority", 0)
                if name not in unsuitable_backends and priority > 0:
                    has_suitable = True
                    break
            if not has_suitable:
                keyring.set_keyring(PlaintextKeyring())
                return True
            return False
        finally:
            os.umask(old_umask)

    def __headers_accept(self, mime_type: str) -> dict[str, str]:
        return {"accept": mime_type}

    @_localhost_suppress_security_warning
    def authorize(self, user: str, password: str, update_keystore: bool) -> str:
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        } | self.__headers_accept("application/json")
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
            raise AccessTokenError("Invalid credentials provided.", False)
        token_response.raise_for_status()
        access_token = token_response.json()["access_token"]
        if update_keystore:
            try:
                keyring.set_password(self.__keyring_system, self.__host, access_token)
            except NoKeyringError:
                raise AccessTokenError("Could not store access token.")
        return access_token

    def __load_access_token(self) -> str:
        access_token = os.getenv("XBAT_ACCESS_TOKEN")
        if not access_token:
            # Fall back on keyring
            try:
                access_token = keyring.get_password(self.__keyring_system, self.__host)
            except NoKeyringError:
                pass
        if not access_token:
            raise AccessTokenError("No access token found.")
        return access_token

    @property
    def access_token(self) -> str:
        # Cache access token to avoid repeated password queries
        if not self.__access_token:
            self.__access_token = self.__load_access_token()
        return self.__access_token

    @property
    def __headers_auth(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.access_token}"}

    @_localhost_suppress_security_warning
    def validate_access_token(self) -> None:
        response = requests.get(
            f"{self.__api_url}/current_user",
            headers=self.__headers_auth,
            verify=self.__verify_ssl,
        )
        if response.status_code == http.HTTPStatus.UNAUTHORIZED:
            raise AccessTokenError("Access token invalid.")
        response.raise_for_status()

    # region benchmarks
    @property
    @_localhost_suppress_security_warning
    def benchmark_runs(self) -> dict[int, BenchmarkRun]:
        benchmark_runs_url = f"{self.__api_url}/benchmarks"
        headers = self.__headers_accept("application/json") | self.__headers_auth
        response = requests.get(
            benchmark_runs_url,
            headers=headers,
            verify=self.__verify_ssl,
        )
        response.raise_for_status()
        runs = response.json()["data"]
        return {
            r["runNr"]: BenchmarkRun(
                r["runNr"],
                r["name"],
                r["issuer"],
                r["configuration"]["_id"] if r.get("configuration") else None,
                r["configuration"]["configuration"]["configurationName"]
                if r.get("configuration")
                else None,
                r["state"],
                r["jobIds"],
            )
            for r in runs
        }

    @_localhost_suppress_security_warning
    def export_runs(
        self,
        run_ids: list[int],
        output_path: Path,
        anonymise: bool = False,
        progress_callback: Callable[[float], None] | None = None,
    ) -> Path:
        export_url = f"{self.__api_url}/benchmarks/export"
        headers = (
            {"Content-Type": "application/json"}
            | self.__headers_accept("application/octet-stream")
            | self.__headers_auth
        )
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

    @_localhost_suppress_security_warning
    def start_run(
        self,
        config_id: str,
        name: str,
        share_project_ids: Iterable[str] = [],
        variables: list[str] = [],
    ) -> int:
        url = f"{self.__api_url}/benchmarks"
        headers = self.__headers_auth
        payload = dict(
            name=name,
            configId=config_id,
            sharedProjects=list(share_project_ids),
            variables=variables,
        )
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            verify=self.__verify_ssl,
        )
        response.raise_for_status()
        # TODO Temporary error handling. (Only necessary until API update.)
        try:
            return response.json()["data"]["runNr"]
        except Exception:
            raise RuntimeError(
                (
                    "Benchmark was started, but could not determine the run number."
                    + " (Check the web UI!)"
                )
            )

    @_localhost_suppress_security_warning
    def update_run(
        self,
        run_number: int,
        name: str | None = None,
        share_projects_ids: Iterable[str] | None = None,
    ) -> None:
        if name is None and share_projects_ids is None:
            raise ValueError("No values to update run with provided.")
        url = f"{self.__api_url}/benchmarks/{run_number}"
        headers = self.__headers_auth
        payload: dict[str, Any] = dict()
        if name is not None:
            payload["name"] = name
        if share_projects_ids is not None:
            payload["sharedProjects"] = list(share_projects_ids)
        response = requests.patch(
            url,
            headers=headers,
            json=payload,
            verify=self.__verify_ssl,
        )
        response.raise_for_status()

    @_localhost_suppress_security_warning
    def cancel_run(self, run_id: int) -> None:
        cancelation_url = f"{self.__api_url}/benchmarks/{run_id}/cancel"
        headers = self.__headers_auth
        response = requests.post(
            cancelation_url,
            headers=headers,
            verify=self.__verify_ssl,
        )
        response.raise_for_status()

    @_localhost_suppress_security_warning
    def delete_run(self, run_id: int) -> None:
        deletion_url = f"{self.__api_url}/benchmarks/{run_id}"
        headers = self.__headers_auth
        response = requests.delete(
            deletion_url,
            headers=headers,
            verify=self.__verify_ssl,
        )
        response.raise_for_status()

    # endregion benchmarks

    # region jobs
    @_localhost_suppress_security_warning
    def get_jobs(
        self,
        run_ids: list[int] | None = None,
        job_ids: list[int] | None = None,
    ) -> list[Job]:
        jobs_url = f"{self.__api_url}/jobs?short=true"
        if run_ids:
            jobs_url += "&runNrs="
            for i, run in enumerate(run_ids):
                if i > 0:
                    jobs_url += ","
                jobs_url += str(run)
        if job_ids:
            jobs_url += "&jobIds="
            for i, job in enumerate(job_ids):
                if i > 0:
                    jobs_url += ","
                jobs_url += str(job)
        headers = self.__headers_accept("application/json") | self.__headers_auth
        response = requests.get(
            jobs_url,
            headers=headers,
            verify=self.__verify_ssl,
        )
        response.raise_for_status()

        def parse_job(job_dict: dict[str, Any]) -> Job:
            variant: str | None = None
            try:
                variant = str(job_dict["configuration"]["jobscript"]["variantName"])
            except Exception:
                pass  # No variant found for this job
            job_state = None
            try:
                job_state = job_dict["jobInfo"]["jobState"]
                if isinstance(job_state, list):
                    job_state = ",".join(job_state)
                job_state = job_state.lower()
            except Exception:
                pass  # Could not determine job state
            return Job(
                int(job_dict["jobId"]),
                str(job_state),
                int(job_dict["runNr"]),
                variant,
                {n["hash"] for n in job_dict["nodes"].values()},
            )

        return [parse_job(j) for j in response.json()["data"]]

    @_localhost_suppress_security_warning
    def get_job_output(self, job_id: int) -> tuple[str, str]:
        jobs_url = f"{self.__api_url}/jobs/{job_id}/output"
        headers = self.__headers_accept("application/json") | self.__headers_auth
        response = requests.get(
            jobs_url,
            headers=headers,
            verify=self.__verify_ssl,
        )
        response.raise_for_status()
        output = response.json()
        return output["standardOutput"], output["standardError"]

    @_localhost_suppress_security_warning
    def get_job_metrics(self, job_id: int) -> dict[str, list[str]]:
        jobs_url = f"{self.__api_url}/metrics?jobIds={job_id}"
        headers = self.__headers_accept("application/json") | self.__headers_auth
        response = requests.get(
            jobs_url,
            headers=headers,
            verify=self.__verify_ssl,
        )
        response.raise_for_status()
        grouped_metrics: dict[str, list[str]] = dict()
        for group_name, group in response.json()["metrics"].items():
            grouped_metrics[group_name] = list(group.keys())
        return grouped_metrics

    @_localhost_suppress_security_warning
    def get_job_roofline(self, job_ids: list[int]) -> dict[str, dict]:
        roofline_model_data_url = f"{self.__api_url}/metrics/roofline?jobIds={','.join([str(i) for i in job_ids])}"
        headers = self.__headers_accept("application/json") | self.__headers_auth
        response = requests.get(
            roofline_model_data_url,
            headers=headers,
            verify=self.__verify_ssl,
        )
        response.raise_for_status()
        return response.json()["data"]

    @_localhost_suppress_security_warning
    def cancel_job(self, job_id: int) -> None:
        cancelation_url = f"{self.__api_url}/slurm/jobs/{job_id}/cancel"
        headers = self.__headers_auth
        response = requests.post(
            cancelation_url,
            headers=headers,
            verify=self.__verify_ssl,
        )
        response.raise_for_status()

    # endregion jobs

    # region nodes
    @property
    @_localhost_suppress_security_warning
    def nodes(self) -> dict[str, dict]:
        nodes_url = f"{self.__api_url}/nodes"
        headers = self.__headers_accept("application/json") | self.__headers_auth
        response = requests.get(
            nodes_url,
            headers=headers,
            verify=self.__verify_ssl,
        )
        response.raise_for_status()
        return response.json()

    # endregion nodes

    # region configurations
    @property
    @_localhost_suppress_security_warning
    def configurations(self) -> dict[str, Configuration]:
        configurations_url = f"{self.__api_url}/configurations"
        headers = self.__headers_accept("application/json") | self.__headers_auth
        response = requests.get(
            configurations_url,
            headers=headers,
            verify=self.__verify_ssl,
        )
        response.raise_for_status()
        configurations = response.json()["data"]
        projects = {p.project_id: p for p in self.projects}

        return {
            c["_id"]: Configuration(
                c["_id"],
                c["configuration"]["configurationName"],
                [
                    projects[project_id]
                    for project_id in c["configuration"]["sharedProjects"]
                ],
            )
            for c in configurations
        }

    # endregion configurations

    # region projects
    @property
    @_localhost_suppress_security_warning
    def projects(self) -> list[Project]:
        projects_url = f"{self.__api_url}/projects"
        headers = self.__headers_accept("application/json") | self.__headers_auth
        response = requests.get(
            projects_url,
            headers=headers,
            verify=self.__verify_ssl,
        )
        return [Project(p["_id"], p["name"]) for p in response.json()["data"]]

    # endregion projects

    # region measurements
    @_localhost_suppress_security_warning
    def download_job_measurements(
        self,
        job_id: int,
        output_path: Path,
        group: MeasurementGroup | None,
        metric: str | None,
        level: MeasurementLevel,
        node: str | None,
        file_format: str = "json",
        progress_callback: Callable[[float], None] | None = None,
    ) -> Path:
        if not isinstance(job_id, int):
            raise ValueError("job_id must be an integer.")
        if metric and not group:
            raise ValueError("Cannot select metric if group is not provided.")
        if not metric and group:
            raise ValueError("Metric must be provided if group is given.")
        if not node and level != MeasurementLevel.job:
            raise ValueError('Node must be provided if level is not "job".')
        if file_format not in ["csv", "json"]:
            raise ValueError("Invalid file format.")
        if file_format == "json" and not metric:
            raise ValueError('Single metric must be provided if file format is "json".')
        params: dict[str, Any] = dict(level=level)
        if group:
            params["group"] = group
        if metric:
            params["metric"] = metric
        if node:
            params["node"] = node
        for k, v in params.items():
            params[k] = str(v)
        measurement_url = f"{self.__api_url}/measurements/{job_id}/{file_format}"
        headers = self.__headers_accept(f"text/{file_format}") | self.__headers_auth
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
                        if progress_callback and total:
                            progress_callback(downloaded / total)
            if file_format == "json":
                # Pretty-print
                data = json.loads(output_path.read_text())
                output_path.write_text(json.dumps(data, indent=3))
        elif response.status_code == http.HTTPStatus.BAD_REQUEST:
            raise ValueError(
                "Could not fulfill request for combination of job_id, group and metric."
            )
        elif response.status_code == http.HTTPStatus.NOT_FOUND:
            raise FileNotFoundError(
                f"job_id {job_id} or combination of job_id, group and metric not found."
            )
        response.raise_for_status()
        return output_path

    # endregion measurements
