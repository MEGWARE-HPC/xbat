import contextlib
import os
import sys
import time
import webbrowser
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple
from urllib.parse import urlparse

import click
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

from .api import (
    AccessTokenError,
    Api,
    BenchmarkRun,
    Configuration,
    MeasurementLevel,
    MeasurementType,
)


def warn(*args: Any, category: str = "Warning", **kwargs: Any) -> None:
    print(f"[bold yellow]{category}:[/bold yellow]", *args, **kwargs, file=sys.stderr)


class App(typer.Typer):
    base_url: str
    local_port: int
    api: Api
    connection: Connection | None = None
    forward_ctx: contextlib.ExitStack | None = None

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
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
            help="Local port being forwarded. (Otherwise, use remote port.)",
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
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if isinstance(e, typer.Exit):
                sys.exit(e.exit_code)
            if isinstance(e, click.exceptions.Abort):
                raise e
            print("[bold red]Error![/bold red]", e, file=sys.stderr)
            if isinstance(e, AccessTokenError):
                app_name = os.path.basename(sys.argv[0])
                print(
                    f"Authenticate by running [green]{app_name} login[/green]!",
                    file=sys.stderr,
                )
            else:
                print(e, file=sys.stderr)
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
    if not ci:
        print(f"[italic white]Setting credentials for {app.base_url}[/italic white]")
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
            raise AccessTokenError("Implicit credentials were invalid")
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
def validate_access_token() -> None:
    app.api.validate_access_token()


def require_valid_access_token() -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
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
    runs = list(app.api.benchmark_runs.values())
    if filter_issuer:
        runs = [r for r in runs if r.issuer == filter_issuer]

    configs = app.api.configurations

    def get_config(run: BenchmarkRun) -> Tuple[str, str]:
        if run.config_id:
            return (
                run.config_id,
                "N/A" if run.config_id not in configs else str(configs[run.config_id]),
            )
        else:
            return ("N/A", "N/A")

    if filter_config:
        runs = [r for r in runs if get_config(r) == filter_config]
    columns = ["run", "name", "config", "config_name", "issuer", "run_state"]
    job_variant_state: Dict[int, Tuple[str, str]] = {}
    if filter_variant and not list_jobs:
        print(
            "[bold yellow]Warning![/bold yellow] Option [italic]--variant[/italic]/[italic]-v[/italic] implies option [italic]--list-jobs[/italic]/[italic]-j[/italic]."
        )
        list_jobs = True
    if list_jobs:
        columns += ["job", "variant", "job_state"]
        for job in app.api.get_jobs(run_ids=[r.run_number for r in runs]):
            variant = job.variant if job.variant else "N/A"
            job_variant_state[job.job_id] = (variant, job.state)
    table = Table(
        show_header=not no_header,
        show_lines=False,
        box=None,
        pad_edge=False,
    )
    for column in columns:
        table.add_column(column)
    for run in runs:
        values: List[str] = [
            str(v)
            for v in [
                run.run_number,
                run.name,
                *get_config(run),
                run.issuer,
                run.state,
            ]
        ]
        if list_jobs:
            for job_id in run.job_ids:
                variant, job_state = job_variant_state[job_id]
                if filter_variant and filter_variant != variant:
                    continue
                table.add_row(*values, str(job_id), variant, job_state)
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
    job_id: Annotated[
        int | None, typer.Option("--job-id", "-j", help="ID of a finished job.")
    ] = None,
    output_path: Annotated[
        Path,
        typer.Option("--output-path", "-o", help="Path to CSV output folder/file."),
    ] = Path().absolute(),
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
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Do not output status and result.")
    ] = False,
):
    if job_id is None:
        runs = app.api.benchmark_runs
        for k in list(runs):
            if runs[k].state != "done":
                del runs[k]
        jobs = dict()
        for job in app.api.get_jobs(run_ids=[r for r in runs]):
            run = runs[job.run_number]
            label = run.name
            if run.config_name:
                label += " ["
                label += run.config_name
                if job.variant:
                    label += f" ({job.variant})"
                label += "]"
            jobs[job.job_id] = label
        job_id = questionary.select(
            "Select a job ID:",
            choices=[dict(name=f"{k} {v}", value=k) for k, v in jobs.items()],
        ).ask()
        if not job_id:
            raise typer.Abort()
    if output_path.is_dir():
        output_path = output_path / (
            f"xbat_job-{job_id}_type-{type}"
            + (f"_metric-{metric}" if metric else "")
            + f"_level-{level}"
            + (f"_node-{node}" if node else "")
            + ".csv"
        )
        print(f"[italic white]Saving output to {output_path}[/italic white]")
    if output_path.suffix.lower() != ".csv":
        print(
            f'[bold yellow]Warning![/bold yellow] Output path {output_path} does not end in ".csv"'
        )
    # FIXME This currently always returns a 404 through the API.
    # TODO Metrics should be matched against available ones.
    # available_metrics = app.api.get_job_metrics(job_id)
    # print(available_metrics);exit()
    pull_args = (job_id, output_path, type, metric, level, node)
    if not verbose:
        app.api.download_job_measurements(*pull_args)
    else:
        with Progress() as progress:
            task = progress.add_task("Download", total=1)
            app.api.download_job_measurements(
                *pull_args,
                lambda x: progress.update(task, completed=x),
            )
    if verbose:
        df = pd.read_csv(output_path)
        print(df)


@app.command(help="Start a benchmark run using a config ID or Slurm job script path.")
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
            help="The path to a Slurm script on the cluster to execute as a benchmark run.",
        ),
    ] = None,
    name: Annotated[
        str | None,
        typer.Option(
            "--name",
            "-n",
            help="Explicitly name the benchmark run.",
        ),
    ] = None,
    share_flag: Annotated[
        bool,
        typer.Option(
            "--share",
            "-s",
            help="Share the benchmark run with the benchmark shared projects.",
        ),
    ] = False,
    share_projects: Annotated[
        List[str],
        typer.Option(
            "--share-project",
            "-p",
            help="Explicitly share the benchmark run with these projects.",
        ),
    ] = [],
    ci: Annotated[
        bool,
        typer.Option(
            "--ci",
            help="Only print the job ID to stdout on success. (Only for starting by benchmark ID.)",
        ),
    ] = False,
):
    share_projects_ids = set()
    projects = app.api.projects
    projects_by_name = {p.name: p for p in projects}
    for project_name in share_projects:
        if len(projects_by_name) != len(projects):
            warn(
                "Project names are not unique.",
                "(Ignoring explicit sharing.)",
            )
            break
        if project_name not in projects_by_name:
            raise ValueError(f"No such project: {project_name}")
        share_projects_ids.add(projects_by_name[project_name].project_id)
    if config_id and job_script:
        raise ValueError(
            "Either a configuration ID or path to a job script may be given, not both."
        )
    configs: Dict[str, Configuration] = {} if job_script else app.api.configurations
    if config_id is None and not job_script:
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
        sbatch_args = [
            "sbatch",
            "--constraint=xbat",
            "--exclusive",
            "--wait-all-nodes=1",
            "--parsable",
            str(job_script),
        ]
        if name:
            sbatch_args.insert(1, f"--job-name={name}")
        status, stdout, stderr = app.exec_cmd(" ".join(sbatch_args))
        if status != os.EX_OK:
            raise RuntimeError((stdout + stderr).strip())
        if ci:
            print(stdout)
        else:
            print(f"Started benchmark run with job ID {stdout}.")
        if share_flag:
            warn("No shared projects exist for Slurm job script based benchmark runs")
        if len(share_projects_ids) > 0:
            # TODO Consider resolving the benchmark run from the job ID and updating the shared projects
            raise NotImplementedError(
                "Sharing Slurm job script based benchmark runs is not yet implemented. (Use the web interface!)",
            )
    elif config_id not in configs:
        raise FileNotFoundError(f"No configuration found with ID: {config_id}")
    else:
        assert config_id
        config = configs[config_id]
        if share_flag:
            share_projects_ids.update(p.project_id for p in config.shared_projects)
            if len(share_projects_ids) == 0:
                warn(
                    "No shared projects found for this benchmark config:",
                    config.name,
                )
        app.api.start_run(
            config_id,
            name if name else config.name,
            share_projects_ids,
        )
        print("Benchmark was started. (Open web UI for details.)")


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


# TODO Could not yet be tested due to HTTP 403
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
            "Job is ignored if benchmark run is given.",
        )
        job = None
    if run:
        validate_access_token()
        if run not in app.api.benchmark_runs:
            raise FileNotFoundError("No benchmark run #{run} found.")
    elif job:
        validate_access_token()
        jobs = app.api.get_jobs(job_ids=[job])
        if len(jobs) == 0:
            raise FileNotFoundError("No job {job} found.")
        run = jobs[0].run_number
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
