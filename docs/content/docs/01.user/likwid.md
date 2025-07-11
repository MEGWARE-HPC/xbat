---
title: Accessing LIKWID
description: Use LIKWID in your jobscript
---

::Headline

## What is LIKWID

::

[LIKWID](https://github.com/RRZE-HPC/likwid){:target="_blank"} (Like I Knew What I’m Doing) is a performance monitoring and benchmarking suite for Linux systems, designed to help users analyze and optimize the performance of their applications. It provides tools for hardware performance monitoring, CPU topology detection, and pinning threads to specific cores, making it easier to understand and improve the efficiency of software on multi-core processors.

::Headline

## Using LIKWID

::

xbat heavily utilises LIKWID for performance monitoring and is therefore able to provide you access to the LIKWID tools aswell. To gain access to these tools, add the following line to your jobscript:

::Codeblock

```bash
export PATH="/usr/local/share/xbatd/bin/:$PATH"
```
::

Afterwards you can call the LIKWID tools directly.

::Codeblock

```bash
likwid-pin -c 0,2,4-6  ./myApp parameters
```

::

-   **[likwid-pin](https://github.com/RRZE-HPC/likwid/wiki/Likwid-Pin){:target="_blank"}**: Pin threads to cores without changes to the code (pthreads and OpenMP)
-   **[likwid-features](https://github.com/RRZE-HPC/likwid/wiki/likwid-features){:target="_blank"}**: Show and modify cpu features like hardware prefetchers
-   **[likwid-mpirun](https://github.com/RRZE-HPC/likwid/wiki/Likwid-Mpirun){:target="_blank"}**: Wrapper for MPI and Hybrid MPI/OpenMP applications
-   **[likwid-memsweeper](https://github.com/RRZE-HPC/likwid/wiki/Likwid-Memsweeper){:target="_blank"}**: Sweep memory of NUMA domains and evict cachelines from the last level cache
-   **[likwid-setFrequencies](https://github.com/RRZE-HPC/likwid/wiki/likwid-setFrequencies){:target="_blank"}**: Modify CPU and Uncore frequencies

::Banner{type="warning"}
Do not use _likwid-perfctr_, _likwid-bench_ or _likwid-perfscope_ in your jobs as it will interfere with the monitoring system of xbat and cause measurements to fail.
::
