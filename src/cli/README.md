# xbat Command Line Interface (CLI)

## Quickstart

1. Install [uv](https://docs.astral.sh/uv/).
2. Set up the project by running `uv sync` and `uv lock`.
3. _Optionally_, create a `.env` configuration file from `.env.example` and test the CLI by running `uv run --env-file .env xbat --help`.
4. Package the app with `uv build --wheel`.

## Development

+ Upgrade dependencies by running `uv sync --upgrade` and `uv lock --upgrade`.
+ Run `uvx black .` reformat the code.
+ Use `uv run mypy ./src` to perform static code analysis.

## Installation

1. Using [pipx](https://pipx.pypa.io/stable/) and `pip install ./dist/xbat_cli*.whl` the application can be installed in an isolated environment.
2. Run `sed 's/^/export /' .env >> ~/.bashrc` to install the custom CLI configuration for bash.
