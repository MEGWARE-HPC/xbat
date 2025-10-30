import contextlib
import os
import sys
import time
import webbrowser
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Callable, Dict, List, Tuple
from urllib.parse import urlparse

import pandas as pd
import questionary
import typer
from fabric import Connection  # type: ignore[import-untyped]
from invoke import Context
from rich import print
from rich.console import Console
from rich.progress import Progress
from rich.table import Table
from typing_extensions import Annotated

from .api import AccessTokenError, Api, MeasurementLevel, MeasurementType


class App(typer.Typer):
    base_url: str
    local_port: int
    api: Api
    connection: Connection | None = None
    forward_ctx: contextlib.ExitStack | None = None

    def __call__(self, *args, **kwargs):
        try:
            return super().__call__(*args, **kwargs)
        finally:
            if self.forward_ctx:
                self.forward_ctx.close()
            if self.connection:
                self.connection.close()

    def exec_cmd(self, cmd: str) -> Tuple[int, str, str]:
        runner = self.connection if self.connection is not None else Context()
        result = runner.run(cmd, hide=True, warn=True)
        assert result is not None
        return result.exited, result.stdout.strip(), result.stderr.strip()

    def check_command_exits(self, command: str) -> bool:
        return (
            os.EX_OK == self.exec_cmd(f"command -v {command}")[0]
            or
            # Try again for Windows CMD
            os.EX_OK == self.exec_cmd(f"where {command}")[0]
        )

    def check_file_exists(self, path: Path) -> bool:
        return (
            os.EX_OK == self.exec_cmd(f"ls {path}")[0]
            or
            # Try again for Windows CMD
            os.EX_OK == self.exec_cmd(f"dir {path}")[0]
        )


app = App(
    no_args_is_help=True,
    context_settings=dict(help_option_names=["-h", "--help"]),
    help="extended benchmarking automation tool (xbat) CLI.",
)


@app.callback()
def main(
    ssh_forwarding_target: Annotated[
        str | None,
        typer.Option(
            envvar="XBAT_SSH_FORWARDING_TARGET",
            help="SSH target for proxying xbat CLI through.",
        ),
    ] = None,
    ssh_forwarding_port: Annotated[
        int | None,
        typer.Option(
            envvar="XBAT_SSH_FORWARDING_PORT",
            help="Local port being forwarded. (Otherwise, use remote port.))",
        ),
    ] = None,
    base_url: Annotated[
        str, typer.Option(envvar="XBAT_BASE_URL")
    ] = "https://demo.xbat.dev",
    api_version: Annotated[str, typer.Option(envvar="XBAT_API_VERSION")] = "v1",
    client_id: Annotated[str, typer.Option(envvar="XBAT_API_CLIENT_ID")] = "demo",
    # Just for documentation in help
    access_token: Annotated[
        str | None,
        typer.Option(envvar="XBAT_ACCESS_TOKEN", help="Alternative to keyring."),
    ] = None,
):
    app.base_url = base_url
    show_help = "-h" in sys.argv or "--help" in sys.argv
    parsed_url = urlparse(app.base_url)
    remote_port = parsed_url.port
    if not remote_port:
        remote_port = 443 if parsed_url.scheme.lower() == "https" else 80
    app.local_port = ssh_forwarding_port if ssh_forwarding_port else remote_port
    if ssh_forwarding_target and not show_help:
        app.connection = Connection(ssh_forwarding_target)
        remote_host = app.connection.run("hostname", hide=True).stdout.strip()
        app.forward_ctx = contextlib.ExitStack()
        forward = app.connection.forward_local(
            app.local_port, remote_port=remote_port, remote_host=remote_host
        )
        app.forward_ctx.enter_context(forward)
    app.api = Api(app.base_url, api_version, client_id)


def handle_errors(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print("[bold red]Error![/bold red]", e)
            if isinstance(e, AccessTokenError):
                app_name = os.path.basename(sys.argv[0])
                print(f"Authenticate by running [green]{app_name} login[/green]!")
            raise typer.Exit(code=1)

    return wrapper


@app.command(help="Update the xbat API access token.")
@handle_errors
def login(
    ci: Annotated[
        bool,
        typer.Option("--ci", help="Use non-interactive mode (CI) and output token."),
    ] = False,
):
    access_token: str | None = None
    user = os.getenv("XBAT_USER")
    password = os.getenv("XBAT_PASS")
    if ci and (not user or not password):
        raise ValueError(
            " ".join(
                [
                    "When using the option --ci,",
                    "credential must be provided using environment variables",
                    "(XBAT_USER, XBAT_PASS)",
                ]
            )
        )
    if not ci and user and password:
        print("[bold blue]Found credentials in environment![/bold blue]")
        try:
            access_token = app.api.authorize(user, password)
        except AccessTokenError:
            print("[bold red]Error![/bold red] Implicit credentials were invalid.\n")
            password = None
    if not access_token:
        user = user if ci else typer.prompt("User", default=user)
        password = password if ci else typer.prompt("Password", hide_input=True)
        assert user, "User was None"
        assert password, "Password was None"
        access_token = app.api.authorize(user, password)
    if ci:
        print(access_token)
    else:
        print("Access token was updated.")


@handle_errors
def validate_access_token():
    app.api.validate_access_token()


def require_valid_access_token() -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            validate_access_token()
            return func(*args, **kwargs)

        return wrapper

    return decorator


@app.command(help="Output benchmark runs/jobs in a table.")
@handle_errors
@require_valid_access_token()
def ls(
    filter_config: Annotated[
        str | None,
        typer.Option("--config", "-c", help="Filter benchmark runs by config name."),
    ] = None,
    filter_issuer: Annotated[
        str | None,
        typer.Option("--issuer", "-i", help="Filter benchmark runs by issuer."),
    ] = None,
    list_jobs: Annotated[
        bool,
        typer.Option(
            "--list-jobs", "-j", help="List individual jobs instead of benchmark runs."
        ),
    ] = False,
    filter_variant: Annotated[
        str | None,
        typer.Option("--variant", "-v", help="Filter jobs by variant name."),
    ] = None,
    no_header: Annotated[
        bool,
        typer.Option(
            "--no-header", "-H", help="Do not print the header for the output table."
        ),
    ] = False,
):
    runs = app.api.benchmark_runs
    if filter_issuer:
        runs = [r for r in runs if r["issuer"] == filter_issuer]

    configs = app.api.configurations

    def get_config(run):
        try:
            config_id = run["configuration"]["_id"]
            return (config_id, configs[config_id])
        except Exception:
            return ("N/A", "N/A")

    if filter_config:
        runs = [r for r in runs if get_config(r) == filter_config]
    columns = ["run", "name", "config", "config_name", "issuer", "run_state"]
    job_variant_state: Dict[int, Tuple[str, str]] = {}
    if filter_variant and not list_jobs:
        print(
            f"[bold yellow]Warning![/bold yellow] Option [italic]--variant[/italic]/[italic]-v[/italic] implies option [italic]--list-jobs[/italic]/[italic]-j[/italic]."
        )
        list_jobs = True
    if list_jobs:
        columns += ["job", "variant", "job_state"]
        for job in app.api.get_jobs(run_ids=[r["runNr"] for r in runs]):
            variant = "N/A"
            try:
                variant = job["configuration"]["jobscript"]["variantName"]
            except Exception:
                pass  # No variant found for this job
            job_state = "unknown"
            try:
                job_state = job["jobInfo"]["jobState"]
                if isinstance(job_state, list):
                    job_state = ",".join(job_state)
                job_state = job_state.lower()
            except Exception:
                pass  # Could not determine job state
            job_variant_state[job["jobId"]] = (variant, job_state)
    table = Table(
        show_header=not no_header,
        show_lines=False,
        box=None,
        pad_edge=False,
    )
    for column in columns:
        table.add_column(column)
    for run in runs:
        values = [
            run["runNr"],
            run["name"],
            *get_config(run),
            run["issuer"],
            run["state"],
        ]
        values = [str(v) for v in values]
        if list_jobs:
            for job in run["jobIds"]:
                variant, job_state = job_variant_state[job]
                if filter_variant and filter_variant != variant:
                    continue
                table.add_row(*values, str(job), variant, job_state)
        else:
            table.add_row(*values)
    print(table)


@app.command(help="Delete benchmark runs.")
@handle_errors
@require_valid_access_token()
def rm(
    runs: Annotated[
        List[int], typer.Argument(help="The IDs of the benchmark runs to delete.")
    ],
    quiet: Annotated[
        bool,
        typer.Option("--quiet", "-q", help="Do not output and continue on failure."),
    ] = False,
):
    for run in runs:
        try:
            app.api.delete_run(run)
        except Exception:
            if not quiet:
                raise


@app.command(help="Show the output and error of a job.")
@handle_errors
@require_valid_access_token()
def log(
    job: Annotated[int, typer.Argument(help="ID of the finished job.")],
):
    stdout, stderr = app.api.get_job_output(job)
    if not stdout and not stderr:
        raise FileNotFoundError(f"No output or error found for job {job}.")
    if stdout:
        Console(highlight=False).print(stdout)
        sys.stdout.flush()
    if stderr:
        Console(highlight=False, stderr=True).print(
            typer.style(stderr, fg=typer.colors.RED)
        )
        sys.stderr.flush()


@app.command(help="Download measurements for a finished job.")
@handle_errors
@require_valid_access_token()
def pull(
    job_id: Annotated[int, typer.Argument(help="ID of a finished job.")],
    output_path: Annotated[Path, typer.Argument(help="CSV output path.")],
    type: Annotated[
        MeasurementType, typer.Option("--type", "-t", help="Measurement type.")
    ] = MeasurementType.all,
    metric: Annotated[
        str | None, typer.Option("--metric", "-m", help="Measurement type metric.")
    ] = None,
    level: Annotated[
        MeasurementLevel, typer.Option("--level", "-l", help="Measurement level.")
    ] = MeasurementLevel.job,
    node: Annotated[
        str | None, typer.Option("--node", "-n", help="Node of measurements.")
    ] = None,
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Do not output on success.")
    ] = False,
):
    if output_path.suffix.lower() != ".csv":
        print(
            f'[bold yellow]Warning![/bold yellow] Output path {output_path} does not end in ".csv"'
        )
    # FIXME This currently always returns a 404 through the API.
    # TODO Metrics should be matched against available ones.
    # available_metrics = app.api.get_job_metrics(job_id)
    # print(available_metrics);exit()
    pull_args = (job_id, output_path, type, metric, level, node)
    if quiet:
        app.api.download_job_measurements(*pull_args)
    else:
        with Progress() as progress:
            task = progress.add_task("Download", total=1)
            app.api.download_job_measurements(
                *pull_args,
                lambda x: progress.update(task, completed=x),
            )
    if not quiet:
        df = pd.read_csv(output_path)
        print(df)


@app.command(help="Start a benchmark run.")
@handle_errors
@require_valid_access_token()
def start(
    config_id: Annotated[
        str | None, typer.Argument(help="The config name of the benchmark to run.")
    ] = None,
    job_script: Annotated[
        Path | None,
        typer.Option(
            "--job-script",
            "-j",
            help="The path to a Slurm script on the remote to execute as a benchmark run.",
        ),
    ] = None,
    ci: Annotated[
        bool,
        typer.Option("--ci", help="Only output job ID on success."),
    ] = False,
):
    if config_id and job_script:
        raise ValueError(
            "Either a configuration ID or path to a job script may be given, not both."
        )
    configs = {} if job_script else app.api.configurations
    if not config_id and not job_script:
        config_id = questionary.select(
            "Select a configuration:",
            choices=[dict(name=f"{k} {v}", value=k) for k, v in configs.items()],
        ).ask()
        if not config_id:
            raise typer.Abort()
    if job_script:
        if not app.check_command_exits("sbatch"):
            raise RuntimeError(
                f"No sbatch executable found. (Is Slurm installed on {app.exec_cmd('hostname')[1]}?)"
            )
        if not app.check_file_exists(job_script):
            raise RuntimeError(f"No job script found at this path: {job_script}")
        status, stdout, stderr = app.exec_cmd(
            " ".join(
                [
                    "sbatch",
                    "--constraint=xbat",
                    "--exclusive",
                    "--wait-all-nodes=1",
                    "--parsable",
                    str(job_script),
                ]
            )
        )
        if status != os.EX_OK:
            raise RuntimeError((stdout + stderr).strip())
        if ci:
            print(stdout)
        else:
            print(f"Started benchmark run with job ID {stdout}.")
    elif config_id not in configs:
        raise FileNotFoundError(f"No configuration with id {config_id} found.")
    else:
        # TODO implement starting benchmark through API
        raise NotImplementedError("Start benchmark run with config_id")


class StopType(str, Enum):
    runs = "runs"
    jobs = "jobs"


@app.command(help="Stop benchmark runs/jobs.")
@handle_errors
@require_valid_access_token()
def stop(
    stop_type: Annotated[StopType, typer.Argument()],
    ids: Annotated[
        List[int], typer.Argument(help="The IDs benchmark runs/jobs to stop.")
    ],
    quiet: Annotated[
        bool,
        typer.Option("--quiet", "-q", help="Do not output and continue on failure."),
    ] = False,
):
    cancel_func = (
        app.api.cancel_run if stop_type == StopType.runs else app.api.cancel_job
    )
    for i in ids:
        try:
            cancel_func(i)
        except Exception:
            if not quiet:
                raise


# TODO I could not test this yet due to HTTP 403
@app.command(help="Create a backup of benchmark runs.")
@handle_errors
@require_valid_access_token()
def export(
    runs: Annotated[List[int], typer.Argument(help="IDs of benchmark runs to export.")],
    output_path: Annotated[Path, typer.Argument(help="CSV output path.")],
    anonymise: Annotated[
        bool, typer.Option("--anonymise", "-a", help="Anonymise data on export.")
    ] = False,
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Do not show progress.")
    ] = False,
):
    if output_path.suffix.lower() != ".tgz":
        print(
            f'[bold yellow]Warning![/bold yellow] Output path {output_path} does not end in ".tgz"'
        )
    pull_args = (runs, output_path, anonymise)
    if quiet:
        app.api.export_runs(*pull_args)
    else:
        with Progress() as progress:
            task = progress.add_task("Download", total=1)
            app.api.export_runs(
                *pull_args,
                lambda x: progress.update(task, completed=x),
            )


@app.command(help="Open the xbat web UI.")
@handle_errors
def ui(
    run: Annotated[
        int | None, typer.Option("--run", "-r", help="Benchmark run to open.")
    ] = None,
    job: Annotated[
        int | None,
        typer.Option("--job", "-j", help="Job for which to open the benchmark run."),
    ] = None,
):
    url = f"http://localhost:{app.local_port}" if app.connection else app.base_url
    if run and job:
        print(
            "[bold yellow]Warning![/bold yellow]",
            f"Job is ignored if benchmark run is given.",
        )
        job = None
    if run:
        validate_access_token()
        runs = [int(r["runNr"]) for r in app.api.benchmark_runs]
        if run not in runs:
            raise FileNotFoundError("No benchmark run #{run} found.")
    elif job:
        validate_access_token()
        jobs = app.api.get_jobs(job_ids=[job])
        if len(jobs) == 0:
            raise FileNotFoundError("No job {job} found.")
        run = jobs[0]["runNr"]
    if run:
        if not url.endswith("/"):
            url += "/"
        url += f"benchmarks/{run}"

    def can_open_url() -> bool:
        if sys.platform.startswith("linux"):
            display = os.environ.get("DISPLAY")
            wayland = os.environ.get("WAYLAND_DISPLAY")
            if not (display or wayland):
                # No GUI environment detected
                return False
        for browser_name in [
            None,
            "firefox",
            "mozilla",
            "netscape",
            "safari",
            "chrome",
            "chromium",
            "opera",
            "edge",
        ]:
            try:
                browser = (
                    webbrowser.get(browser_name) if browser_name else webbrowser.get()
                )
                if not isinstance(browser, webbrowser.BackgroundBrowser):
                    return True
            except webbrowser.Error:
                pass
        return False

    if can_open_url():
        webbrowser.open(url)
        time.sleep(3)
        print("Web UI opened at", url)
    else:
        print("Web UI running at", url)
    if app.connection:
        input("(Press enter to shut down)")


if __name__ == "__main__":
    app()
