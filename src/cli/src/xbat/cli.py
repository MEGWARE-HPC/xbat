from functools import wraps
import os
from pathlib import Path
import sys
from typing import Callable
import pandas as pd
from typing_extensions import Annotated
import typer
from rich import print
from rich.progress import Progress
from .api import AccessTokenError, Api, MeasurementLevel, MeasurementType


class App(typer.Typer):
    api: Api


app = App(
    no_args_is_help=True,
    context_settings=dict(help_option_names=["-h", "--help"]),
    help="extended benchmarking automation tool (xbat) CLI.",
)


@app.callback()
def main(
    base_url: Annotated[
        str, typer.Option(envvar="XBAT_BASE_URL")
    ] = "https://demo.xbat.dev",
    api_version: Annotated[str, typer.Option(envvar="XBAT_API_VERSION")] = "v1",
    client_id: Annotated[str, typer.Option(envvar="XBAT_API_CLIENT_ID")] = "demo",
):
    app.api = Api(base_url, api_version, client_id)


@app.command(help="Update the xbat API access token.")
def login():
    user = typer.prompt("User")
    password = typer.prompt("Password", hide_input=True)
    try:
        app.api.authorize(user, password)
    except Exception as e:
        print("[bold red]Error![/bold red]", e)
        raise typer.Exit(code=1)
    print("Access token was updated.")


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
        bool, typer.Option("--quiet", "-q", help="Do not output on success")
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


if __name__ == "__main__":
    app()
