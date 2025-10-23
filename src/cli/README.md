# xbat Command Line Interface (CLI)

## Quickstart

1. Install [uv](https://docs.astral.sh/uv/).
2. Set up the project by running `uv sync` and `uv lock`.
3. _Optionally_, create a `.env` configuration file from `.env.example` and test the CLI by running `uv run --env-file .env xbat --help`.
4. Package the app with `uv build --wheel`.

## Development

+ Upgrade dependencies by running `uv sync --upgrade` and `uv lock --upgrade`.
+ Run `uvx isort .` and `uvx black .` to reformat the code.
+ Use `uv run mypy ./src` to perform static type checking.

## Installation

1. Using [pipx](https://pipx.pypa.io/stable/) and `pip install ./dist/xbat_cli*.whl` the application can be installed in an isolated environment.
2. Run `sed '/^\s*#/! s/^/export /' .env >> ~/.bashrc` to install the custom CLI configuration for bash.

## Locked Down xbat

If the xbat API and Web UI are only accessible via the system that running them, enable local port forwarding.  
Your `$HOME/.ssh/config` should have an entry for connecting to the system without a password:

```ssh
Host xbat-host
	HostName example.org
	User alice
	IdentityFile ~/.ssh/id_ed25519
```

Before using the CLI, export the environment variable `XBAT_SSH_FORWARDING_TARGET="xbat-host"`.  
Optionally, you can also export `XBAT_SSH_FORWARDING_PORT=1234`, if the remote port is not available locally.

## Non-interactive Use

When running in a CI pipeline, such as GitHub Actions,
you can provide the credentials through the environment:

```bash
export XBAT_ACCESS_TOKEN=$(
    XBAT_USER=${{ secrets.XbatUser }} \
    XBAT_PASS=${{ secrets.XbatPassword }} \
    xbat login --ci
)
xbat pull $JOB_ID measurements.csv
```
