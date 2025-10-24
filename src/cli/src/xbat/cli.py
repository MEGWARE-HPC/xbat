import contextlib
import os
import sys
import time
import webbrowser
from functools import wraps
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

import pandas as pd
import typer
from fabric import Connection  # type: ignore[import-untyped]
from rich import print
from rich.progress import Progress
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


def validate_access_token() -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                app.api.validate_access_token()
            except AccessTokenError as e:
                print("[bold red]Error![/bold red]", e)
                app_name = os.path.basename(sys.argv[0])
                print(f"Authenticate by running [green]{app_name} login[/green]!")
                raise typer.Exit(code=1)
            return func(*args, **kwargs)

        return wrapper

    return decorator


@app.command(help="Download measurements for a finished job.")
@validate_access_token()
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
            app.api.pull(*pull_args)
        else:
            with Progress() as progress:
                task = progress.add_task("Download", total=1)
                app.api.pull(
                    *pull_args,
                    lambda x: progress.update(task, completed=x),
                )
    except Exception as e:
        print("[bold red]Error![/bold red]", e)
        raise typer.Exit(1)
    if not quiet:
        df = pd.read_csv(output_path)
        print(df)


@app.command(help="Open the xbat web UI.")
def ui():
    url = f"http://localhost:{app.local_port}" if app.connection else app.base_url

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
