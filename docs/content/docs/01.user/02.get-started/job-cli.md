---
title: CLI Submission
description: How to run a benchmark via the CLI
---

::Headline

## Use xbat via Slurm CLI

::

The easiest way of using xbat is to submit jobs via the Slurm CLI. This allows you to use your existing job scripts without any changes while benefiting from the monitoring and analysis capabilities of xbat. Simply add the `--constraint=xbat` and `--exclusive` parameters to your `sbatch` command. When submitting multi-node jobs, it is also advised to use `--wait-all-nodes=1` as xbat may defer the start of a job on individual nodes to assess their hardware capabilities.

::Codeblock

```bash
sbatch --constraint=xbat --exclusive --wait-all-nodes=1 my_job_script.sh
```

::

::Banner{type="warning"}
xbat currently monitors the entire compute node regardless of the number of cores requested. The `--exclusive` parameter is required to ensure that the measurements are not distorted by other jobs running on the same node.
::

xbat provides additional features like parameter studies, API support and collaboration when using job configurations via the UI. See here for more details on [job configurations](/docs/user/get-started/job-configuration).

## xbat CLI

Set the following environment variables or export them from your shell profile/RC file:

| Variable | Explanation | Example |
|---|---|---|
| `XBAT_BASE_URL` | Base URL of the xbat installation. | `https://demo.xbat.dev` |
| `XBAT_API_VERSION` | [API](../api.md) version (part of the URL). | `v1` |
| `XBAT_API_CLIENT_ID` | [API](../api.md) OAuth2 client ID for the CLI. | `CLI` |

The following environment variables are only required when the xbat is only exposed locally, or when starting a Slurm scripts through the CLI with `xbat start --job-script my_job_script.sh` (see above):

| Variable | Explanation |
|---|---|
| `XBAT_SSH_FORWARDING_TARGET` | SSH target for proxying xbat CLI through. |
| `XBAT_SSH_FORWARDING_PORT` | Local port being forwarded. (Otherwise, use remote port.) |

Authenticate interactively using `xbat login`.
The following commands are available (use `--help` for documentation of arguments):

| Command | Explanation |
|---|---|
| `login` | Update the xbat API access token. |
| `ls` | Output benchmark runs/jobs in a table. |
| `rm` | Delete benchmark runs. |
| `log` | Show the output and error of a job. |
| `pull` | Download measurements for a finished job. |
| `roofline` | Show the roofline model data of one or more finished jobs. |
| `start` | Start a benchmark run. |
| `stop` | Stop benchmark runs/jobs. |
| `export` | Create a backup of benchmark runs. |
| `ui` | Open the xbat web UI. |
| `plot` | Plotting commands. |
