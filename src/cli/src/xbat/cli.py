import contextlib
import os
import sys
import time
import webbrowser
from functools import wraps
from pathlib import Path
from typing import Callable, Dict, List, Tuple
from urllib.parse import urlparse

import pandas as pd
import typer
from fabric import Connection  # type: ignore[import-untyped]
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


@app.command(help="Update the xbat API access token.")
def login(
    user: Annotated[str | None, typer.Option(envvar="XBAT_USER")] = None,
    password: Annotated[str | None, typer.Option(envvar="XBAT_PASS")] = None,
    output_access_token: Annotated[
        bool, typer.Option("--ci", help="Output access token.")
    ] = False,
):
    user = user if user else typer.prompt("User")
    password = password if password else typer.prompt("Password", hide_input=True)
    try:
        access_token = app.api.authorize(user, password)
        if output_access_token:
            print(access_token)
        else:
            print("Access token was updated.")
    except Exception as e:
        print("[bold red]Error![/bold red]", e)
        raise typer.Exit(code=1)


def validate_access_token():
    try:
        app.api.validate_access_token()
    except AccessTokenError as e:
        print("[bold red]Error![/bold red]", e)
        app_name = os.path.basename(sys.argv[0])
        print(f"Authenticate by running [green]{app_name} login[/green]!")
        raise typer.Exit(code=1)


def require_valid_access_token() -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            validate_access_token()
            return func(*args, **kwargs)

        return wrapper

    return decorator


@app.command(help="List benchmark runs/jobs.")
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

    def get_config(run):
        try:
            return run["configuration"]["configuration"]["configurationName"]
        except Exception:
            return "N/A"

    if filter_config:
        runs = [r for r in runs if get_config(r) == filter_config]
    columns = ["run", "name", "config", "issuer", "run_state"]
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
            get_config(run),
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


@app.command(help="Show the output and error of a job.")
def log(
    job: Annotated[int, typer.Argument(help="ID of the finished job.")],
):
    stdout, stderr = app.api.get_job_output(job)
    if not stdout and not stderr:
        print(f"[bold red]Error![/bold red] No output or error found for job {job}.")
        raise typer.Exit(1)
    if stdout:
        Console(highlight=False).print(stdout)
        sys.stdout.flush()
    if stderr:
        Console(highlight=False, stderr=True).print(
            typer.style(stderr, fg=typer.colors.RED)
        )
        sys.stderr.flush()


@app.command(help="Download measurements for a finished job.")
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
    try:
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
    except Exception as e:
        print("[bold red]Error![/bold red]", e)
        raise typer.Exit(1)
    if not quiet:
        df = pd.read_csv(output_path)
        print(df)


# TODO I could not test this yet due to HTTP 403
@app.command(help="Create a backup of benchmark runs.")
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
    try:
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
    except Exception as e:
        print("[bold red]Error![/bold red]", e)
        raise typer.Exit(1)


@app.command(help="Open the xbat web UI.")
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
            print("[bold red]Error![/bold red]", f"No benchmark run #{run} found.")
            raise typer.Exit(1)
    elif job:
        validate_access_token()
        jobs = app.api.get_jobs(job_ids=[job])
        if len(jobs) == 0:
            print("[bold red]Error![/bold red]", f"No job {job} found.")
            raise typer.Exit(1)
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
        time.sleep(1)
        print("Web UI opened at", url)
    else:
        print("Web UI running at", url)
    if app.connection:
        input("(Press enter to shut down)")


if __name__ == "__main__":
    app()
