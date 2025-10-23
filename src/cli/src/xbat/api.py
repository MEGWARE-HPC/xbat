import http
import warnings
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, TypeVar, cast
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
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
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
        keyring.set_password(self.__keyring_system, self.__host, access_token)

    @property
    def access_token(self):
        access_token = keyring.get_password(self.__keyring_system, self.__host)
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

    @_localhost_suppress_security_warning
    def pull(
        self,
        job_id: int,
        output_path: Path,
        type: MeasurementType,
        metric: str | None,
        level: MeasurementLevel,
        node: str | None,
        progress_callback: Callable[[float], None] | None = None,
    ):
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
