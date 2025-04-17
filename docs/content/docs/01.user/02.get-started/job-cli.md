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
