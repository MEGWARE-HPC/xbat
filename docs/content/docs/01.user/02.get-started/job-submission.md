---
title: UI Submission
description: How to run a benchmark via UI
---

::Headline

## Starting a Benchmark

::

To start a benchmark, visit the `BENCHMARKS` tab and click the `START BENCHMARK` button.

Choose a name for your benchmark and select the configuration you want to use. By default, all your benchmarks are accessible only to you, but you may select a project to share the benchmark with. This means all users within this project will be able to see the benchmark and its results. See [Projects](/docs/user/projects) for more information.

<img src="/img/benchmark_submission.png" alt="Benchmark Submission Dialog" class="img img-40" >
</img>

::Banner
You can overwrite the job variables settings for the current configuration during submission. These changes will not persist and only apply to the current benchmark. See [here](https://localhost:3000/docs/user/get-started/job-configuration#variables) for more details on job variables.
::

::Headline

## Benchmark Overview

::

After the submission of your benchmark, it will appear in the table. This table tracks all your benchmarks as well as those that are shared with you through the project system. You can see the status of your benchmark, the configuration used and the time of submission.

You may perform the following actions on your benchmark after selecting at least on entry in the table:

-   **Share**: Modify the projects that have access to the benchmark.
-   **Revoke Shared Access**: Revoke access to a shared benchmark for all projects.
-   **Cancel**: Cancel the benchmark and all associated jobs in Slurm (only for active benchmarks).
-   **Delete**: Delete the benchmark and all associated data.

You can access the results of your benchmark by clicking on it in the table (see [Benchmark Results](#)).

Use the **_COMPARE_** button to compare the results of multiple benchmarks. See [Comparing Benchmarks](#) for more information.

<img src="/img/benchmark_overview.png" alt="Benchmark Overview" class="img img-70">
</img>
