# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

### Added

-   dedicated API CSV and JSON file endpoints for graph measurements (#9)
-   extended API CSV endpoint to export multiple metrics at once (#20)
-   syntax highlighting support for CSV language in editor (#8)

### Changed

-   always overwrite valkey.conf on installation
-   use chrt instead of nice by default for xbatd for more reliable scheduling
-   temporarily downgrade LIKWID to v5.3.0 due to errors on some architectures with v5.4.1
-   improved layout of docs on smaller screens
-   default back to npm instead of bun for frontend and docs
-   first variant of job configuration can now be deleted (#49)

### Fixed

-   link to edit page and changelog on GitHub
-   node info and benchmarks not being registered correctly
-   misaligned links to Slurm documentation in job script editor (#7)
-   incorrect CSV headers on graph export
-   different capitalization of username leading to creation of multiple accounts (#21)
-   theme and fonts issues in editor (#13, #14)
-   anonymization of benchmarks exports (#30)
-   issue with JobOverviewTable loading (#28)
-   overview table distortion by long names (#41)

## v1.0.0 - 2025-04-17

_If you are migrating from a prior release modification of `xbatd.conf` is required to include settings for the REST API and QuestDB - see `conf/xbatd.conf` and adjust accordingly!_

_questdb.conf was updated significantly - it is recommended to use the new version and transfer credentials from your current one!_

### Added

-   MIT license
-   ability to submit jobs via Slurm CLI with `--constraint=xbat` parameter.
-   [xbat.dev](xbat.dev) website featuring user, admin and developer documentation
-   public demo [demo.xbat.dev](https://demo.xbat.dev) and [microcard mirror](https://microcard.xbat.dev)
-   read-only demo mode
-   authentication for xbatd ILP over HTTP
-   purge of deleted jobs from QuestDB (admin only - see documentation)
-   job state to job selection dropdown
-   export and import of benchmark data for backup (manager and admin only)
-   configurable worker size and port for frontend/backend
-   option to use alternative xbat system user account
-   configurable SSL certificate directory and auto-detection of certificates
-   overview of variables to job selection dropdown
-   hover-based job details to benchmark overview
-   support for AMD GPUs
-   dedicated error page

### Changed

-   only capture jobs that possess the "xbat" feature flag
-   backend and xbatctld to use gRPC instead of a REST API for communication
-   optimize the loading mode of icons
-   graph UI and expanded configuration options
-   improved handling of large job IDs in overview table
-   increased timeout for import/export calls and adjusted maximum upload file size
-   valkey cache no longer persists across service restarts
-   updated LIKWID and other dependencies
-   reduced worker count and max memory consumption for Questdb
-   max clock speed for GPUs is no longer captured
-   improved setup process

### Fixed

-   wiki highlighting incorrect menu entry when navigating via a link
-   deletion of benchmarks not accounting for job outputs
-   Slurm dates reported as 1970-01-01 when date is not yet set
-   sidebar of configuration disappearing on small screens
-   GPU detection for hardware overview
-   LDAP login
-   jobs stuck in running state
-   incorrect removal of job variables when multiple values are present
-   missing device numbers in trace name on device level
-   graph hover position
-   energy consumption incorrectly labled as "power" in sidebar info
-   missing download button on job script
-   multiple concurrent purges
-   uninstall of xbat
-   job variables configuration
-   high CPU usage of xbatctld and mongodb

## v0.17.0 - 2024-10-22

_This release requires modifying `xbat.conf` to include settings for PgBouncer and LDAP - see `conf/xbat.conf` and adjust accordingly!_

### Added

-   extended number of metrics for monitoring
-   improved loading times for graphs (especially for long running jobs)
-   added PgBouncer between QuestDB and backend
-   configurable user identifier for LDAP (cn/uid)
-   ability to pause automatic refresh of data
-   benchmark and variant names are now editable

### Changed

-   use dedicated xbat user
-   move database data and logs to `/var/lib/xbat` and `/var/log/xbat` - _requires copying and chowning mongodb/questdb/valkey/ no new location!_
-   removing a variant from a configuration now requires explicit confirmation
-   revised editing of variant name

### Fixed

-   broken compare and roofline features
-   LDAP authentication
-   automatic refresh not stopping when job has finished
-   jobs without any output incorrectly indicating that output is not available
-   power consumption disappearing on automatic refresh
-   dates being one month off in frontend
-   FLOPS peak values not scaled correctly

## v0.16.0 - 2024-09-27

### Added

-   wiki with guides and explanations
-   automatic refresh for graphs and output when job is pending or running
-   access to questdb GUI via frontend
-   adjustable redirect uris for swagger (only by admin)
-   indicator to graphs in case there is no data or data does not match filters
-   variables used for job to result page
-   forward slurm submission errors to user as failure reason
-   overhauled job variable configuration
    -   ability to define variables in configurations (before only on submission of benchmark)
    -   support for parameter studies -> generate permutations when specifying multiple values for a variable
    -   improved interface
-   access to LIKWID for all users

### Changed

-   use different editor for configurations and outputs
    -   improved performance
    -   better styling and syntax highlighting
    -   fixes several issues with the old editor
-   integrate job settings as sbatch directives into editor including form validation
-   jobcripts no longer separated into preparation, execution and postprocessing
    -   all stages are now combined
    -   optional manual insert of #XBAT-START# and #XBAT-STOP# emulates behaviour of execution stage
-   configuration settings are now collapsable
-   remove pagination for graph statistics
-   separate job-related info in result page
-   process jobs immediately instead of waiting for all jobs of a benchmark to finish
-   improved behaviour for pending and running jobs
-   deciles are no longer affected by "hide inactive" setting
-   deploying questdb separetely now requires --questdb-address parameter on installation for proper nginx configuration
-   automatically disable hardware performance monitoring when monitoring is disabled
-   xbatd now collects node information regardless of whether monitoring is enabled or not

### Fixed

-   access to swagger via frontend
-   graphs not switching colors correctly on theme change
-   comparison dialog not closing on outside click
-   cpu topology dialog not closing on "close" button click
-   jobscripts that are not (yet) available in the frontend returning 404
-   details of internal error being displayed to user
-   job output using shell syntax highlighting
-   continuous loading of graphs when viewing jobs that failed during submission
-   graph hover not disappearing when cursor moves to legend
-   benchmarks states not being updated correctly

## v0.15.0 - 2024-07-31

### Added

-   extensive customisation options on graph image export
-   sum to graph statistics
-   graph trace customisation (not persistent yet)
    -   color palettes
    -   job id prefix renaming
    -   trace renaming with color picker
-   export and styling options to roofline model
-   inactive traces completely hideable from graph and statistics via settings menu
-   deciles for core and thread level
-   roofline jobs plottable by peak, average or median
-   cache for graph related API calls
-   detection for suspended QuestDB WAL - will be resumed automatically
-   location of job output to frontend

### Changed

-   migrate SPA to Nuxt SSR (including partial rewrite, optimisations and partial typescript support)
-   hide benchmark scaling factor on thread and core level
-   UX of graph interface
-   sorting of jobs to ascending on job selection form
-   improved performance of graph hover
-   graph hover may be truncated on large number of traces
-   increased nginx compression to reduce data transfer and improve loading times
-   sorting of tables and job selection
-   allowed characters for job name
-   metrics to be sorted alphabetically
-   graph styling
-   job related data to be stored in separate directories within $HOME/.xbat
-   store job output separately from job and load it only on demand
-   optimise bundle size

### Fixed

-   duplicate space in trace name on device/socket level or below
-   roofline dialog close button not working
-   margins resetting in graph export on window resize
-   error when submitting multiple benchmarks simoultenously as a new user
-   slurm error when job name contains whitespaces
-   undefined gpu metrics in quick search
-   graph loading indicator occasionally not disappearing
-   prevent graph hover from clipping outside of viewport
-   graph scaling sometimes being too conservative - use max value instead of median for scaling
-   scaling of peak values for level < node
-   unit for FLOPS and UOPS
-   "hide inactive" setting not working on initial graph load
-   job renaming on roofline graph

## v0.14.0 - 2024-04-10

### Added

-   improved documentation and setup instructions
-   ability to cancel benchmarks
-   queued benchmarks showing job states
-   failed benchmarks showing reason for failure
-   track last user login
-   display variant name and iteration in job selection and graph statistics
-   allow for roofline comparison across benchmarks
-   variant name of job to sidebar
-   ability to display peak flops and bandwidths in graphs

### Changed

-   rename tool to xbat
-   FLOPS and UOPS use automatic scaling like most other metrics
-   result page factors in status of benchmark
-   removed box and lasso select from graphs
-   use UTC for all timestamps
-   use lazy loading for roofline model and power usage
-   automatically select first metric when changing group on graph if there is only a single metric present
-   display branch misprediction ratio as percentage and descriptions for branching metrics
-   'hide inactive' setting now applies to all metric levels
-   only completed and cancelled jobs are selectable in roofline and compare selection

### Fixed

-   podman-compose issues when deploying with database
-   occasional timeout of measurement API calls
-   inconsistent behaviour of table checkboxes in benchmark overview
-   benchmark status on partial job failure
-   trace names showing html-linebreaks
-   improper csv header
-   wrapping of CSV to multiple lines
-   duplicate api calls in comparison
-   incorrect graph background color on initial page load in dark mode
-   incorrect scaling of graph when collapsing/expanding sidebar
-   clipping of graph controls on smaller screens in column arrangement
-   long configuration names overlapping with actions in configuration page
-   graph statistics containing empty entries when activating min/max/avg traces
-   reset metric level to job if current selection is invalid
-   grouping of statistic traces in graph legend
-   statistics still being visible when changing back node/job level
-   misaligned topology due to line-wrap
-   removing of variants

## v0.13.1 - 2024-02-19

### Added

-   support for LDAP authentication
-   display capture interval and iterations at benchmark results
-   x-axis title can be toggled off
-   hint when jobs could not be accounted for in comparison
-   ability to hide inactive threads/cores
-   additional filters for thread/core-level
-   cpu/gpu/fpga power consumption

### Changed

-   graph default level to "job"
-   default graphs are now sensitive to available measurements
-   allow for comparison of all jobs in roofline regardless of node
    -   use reference node across all jobs
    -   display hint when jobs are run on different nodes
-   graph statistics respects thread/core hide option
-   graph settings and filters are now applied automatically (with timeout)

### Fixed

-   graph hover containing html linebreak
-   CPU max speed formatting
-   x-axis labels overlapping with title
-   inconsistent sorting of jobs in comparison dialog
-   available metrics for comparison when job has no measurements
-   loading time of export dialog
-   incorrect grouping of statistics on thread/core level
-   thread/core traces not visible by default
-   inaccurate calculation of averages caused by inactive cores
-   duplicate requests for metrics
-   aggregation of system power on job level

## v0.13.0 - 2024-01-24

### Added

-   improve interfacing with slurm
    -   provide available partitions in configuration
-   make swagger UI available to all users
-   display project ID and application runtime in frontend
-   compare feature
-   quick search for graph metrics
-   extended statistics for graphs
-   graph export as JSON, CSV and PNG/SVG
-   ability to filter for thread/core range

### Changed

-   improve FLOPS metrics descriptions
-   rework authentication system (authlib instead of oauthlib)
-   upgrade LIKWID for SPR/Zen4 support and bugfixes
-   allow users of type manager to delete benchmarks of other users
-   improve loading times of graphs

### Fixed

-   duplicate peak flop label in roofline model
-   graph hover adjusted for markers
-   graphs stuck in loading animation when no data is present
-   users seeing benchmarks of other users (which are not shared)
-   shared benchmarks missing from overview
-   misaligned graph legends

## v0.12.0 - 2023-11-02

### Added

-   third-party licenses
-   provide separate packages for el8 and el9
-   microbenchmarking for peakflops and cache/memory-bandwidth
-   customizable roofline modelling
-   logging with customizable levels for collectd
-   copy to clipboard in editor
-   dark mode
-   provide changelog via frontend

### Changed

-   use nvml instead of dcgm for nvidia gpu monitoring
-   collectd can now communicate with mongodb
    -   job configuration retrieved directly from database instead of temporary file created by prolog
    -   collected system information now written to database instead of user home
-   remove envparser
-   replace rapidjson with nlohmann/json
-   graph rangeslider can now be toggled off
-   revise user management
    -   benchmarks and configurations are no longer bound to a project
    -   users only have access to their data
    -   projects can be used to share access to benchmarks and configurations with other users
-   improve styling of graphs
-   convert CHANGELOG to markdown
-   multiple UI improvements
-   replace config.json for frontend with .env provided by vite
-   upgrade LIKWID for Zen4 and SapphireRapids support

### Fixed

-   misaligned line numbers in editor
-   saving of new configurations
-   unit of infiniband bandwidth, memory data volume and vectorization ratio
-   duplicate label for scalar operations
-   incorrect capturing of metrics for clock, energy, power and CPI

## v0.11.2 - 2023-08-08

-   fix loading of measurements when jobs of a benchmark are executed on different nodes

## v0.11.1 - 2023-07-27

-   fix handling of missing job time
-   improve build process
-   fix whitelist access and user roles
-   fix scroll-up button prevent actions at bottom of page
-   various UI fixes
-   fix metric aggregation
-   fix handling of missing timestamps in jobscript

## v0.11.0 - 2023-07-06

-   add Xilinx FPGA power monitoring
-   remove ability to individually turn off measurements -> always gather everything if possible
-   auto-generate job name if none given
-   update npm dependencies and migrate to vue3/vuetify3
-   migrate from webpack to vite
-   add download of raw json to graph
-   add descriptions to metric groups and metrics
-   fix and improve statistics
-   add graph loading indicator
-   fix collection of socket-based metrics when SMT is enabled
-   cb-questdb no longer runs as root

## v0.10.0 - 2023-06-09

-   rework metric system
    -   add questdb as timeseries database
    -   daemon collects values at lowest possible level and processes them
    -   daemon write measurements directly to questdb via Influx Line Protocol
    -   add level-based metric aggregation
    -   combine single metrics to sensible views
-   add statistics for graphs
-   fix multi-node jobs
-   deprecate export feature
-   minor fixes

## v0.9.4 - 2023-04-24

-   set webgateway app name separately (fixes issues with pipe pool naming scheme)

## v0.9.3 - 2023-04-20

-   improve security of pipe
-   enable all nvidia gpu metrics
-   refactor webgateway directory
-   enable ningx gzip and expand types
-   adapt configuration for ConfigParser
-   rework logging mechanism and add logging to file
-   fix walltime regex
-   rework configuration interface
-   remove limit on iterations
-   add snackbar to relevant UI actions
-   rework benchmark result interface

## v0.9.2 - 2023-02-15

-   update installation instructions

## v0.9.1 - 2023-02-02

-   disallow project deletion if none is selected
-   measurement data no longer includes preparation and postprocessing phase
-   remove old files from /run/cb on startup
-   remove communication files after executing commands on host
-   improve handling of invalid tokens
-   reenabled and improved ethernet and infinband metrics
-   fixed detection of job end when slurm queue is empty
-   adding a new variant now sets the new one as active instead of jumping back to the first (#60)
-   fix default naming of new variantes
-   fix disappearing arrows of variant tabs with certain window-sizes (#62)
-   add runtime information for variant selection (#65)
-   add feature to download jobscript and slurm output via frontend
-   fix duplicate processing of results when using multiple variants
-   account for all job states on multi-variant jobs
-   fix display of system information
-   fix incorrect width of graphs in comparison-dialog (#44)
-   fix inability to select benchmark for comparison (#64)
-   removed internal jobscript display from frontend
-   added logout page
-   potential fix for login-issues by avoiding conflicts when executing commands on host
-   improved logging and refactoring

## v0.9.0 - 2023-01-18

-   add options to configure network bind of frontend and collectd
-   set correct file permissions during install
-   use prolog and epilog for handling preparations and orchestration of measurements
-   collectd now writes results to home-directory of user
-   fix graph options when running multiple iterations of a benchmark
-   improve form validation
-   fix duplicate labels for SP/DP metrics
-   fix incorrect return code for commands executed via docker-host-pipe
-   check job state after job ends to improve displayed benchmark status
-   all job-related data is now stored in users home-directory
-   execute sbatch as submitting user instead of providing uid/gid due to env issues

## v0.8.4 - 2022-12-08

-   improve installation
    -   executor option is now correctly resolved
    -   automatically create path for configurations, logs and database
    -   default likwid location is now the same as with collectd
    -   remove duplicate directory creation
-   add shutdown of collectd rest-server when cancellation is signaled
-   increase number of file descriptors for collectd.service to prevent likwid from running into this limit on systems with high core-count due to direct msr usage
-   deployment without local database-container is now possible (--no-db during installation)
-   fix login error when no whitelist is set up
-   docker-host-pipe handling is now part of cb.service instead of cronjob
-   improve collectd behaviour between jobs
-   revert collectd to run with nice -20 instead of RT priority 99
-   fix multi-node job submission
-   job scripts can now request a number of nodes instead of specifying them by name

## v0.8.3 - 2022-11-23

-   change mongod.conf location
-   make uid and gid of mongodb user configurable
-   expand likwid metrics
    -   fix missing branch predicition
    -   enable operational intensity
    -   add cycle activities
-   docker-host-pipe is now part of the cb.service and no longer requires a cronjob
-   cb.service now respects container-executor selection

## v0.8.2 - 2022-11-11

-   implement authentication via PAM

## v0.8.1 - 2022-11-03

-   enter now submits login form
-   fix issue regarding credential check
-   fix crash of collectd during initialisation
-   fix controlds handling of incoming collectd data
-   account for gid and home directory in addition to uid when submitting jobs
-   implement blocking of users

## v0.8.0 - 2022-10-12

-   add user authentication via freeIPA
-   add local user authentication for admin
-   add user and rights management
-   rework project management and selection
-   add option to execute commands locally on host instead of via ssh
-   add request size io metrics
-   integrate collectd (formerly cbUtilities cbDaemon) into this repository
-   rework collectd to directly communicate with controld
-   update collectd rpm
-   bump likwid to v5.2.2
-   multiple frontend-related fixes
-   improve setup process
-   improve logging
-   several bugfixes

## v0.7.2 - 2022-08-02

-   drastically improve handling of large outputs

## v0.7.1 - 2022-07-27

-   fix incorrect access to new configurations after first save
-   refactor docker-compose file
-   disable logging for database in docker-compose
-   remove unused repo

## v0.7.0 - 2022-07-22

-   complete restructure of project
-   improved python module usage
-   implement controld which replaces all gitlab CI functions for CB
-   test install and removal of cb.service in pipeline
-   fix deletion of benchmarks

## v0.6.2 - 2022-06-24

-   fix issues when using cancel on configurations

## v0.6.1 - 2022-06-14

-   reimplement plot comparison feature
-   reimplement export feature (pdf export not included)
-   add functionality to assign configurations to different project (only in development project)
-   fix autoscaling and x-axes of graphs
-   add form validation
-   ship fonts (Source Sans Pro, Source Code Pro)
-   various fixes to code editor

## v0.6.0 - 2022-05-25

-   transition frontend to vuetify
-   improve features and styling of frontend
-   rework jobscript configuration
-   implement mechanism for multiple versions within one configuration
-   add editor with syntax highlighting
-   remove jube dependency
-   implement job setup and submission as python script
-   change data structure of bencharmk_runs and permutations collections
-   add systeminfo to permutations -> systeminfo collection is no longer required
-   inline scripts called in jobscript
-   the jobscript is now the only file transmitted to cluster before job submission
-   adapt gitlab-related settings for new gitlab domain
-   permutations are now stored in database before job submission and updated after collection
-   remove permutations being passed as artifacts between stages as database is now responsible for providing permutation information
-   bugfixes related to graphs
-   provide configured jobscript directly to user in frontend
-   make CB internal jobscript available in development project
-   display database \_id of configurations to be used outside of the CB interface
-   pass benchmark id between stages to solve unavailablility of id when the benchmark is created in the deployment stage and not beforehand
-   huge refactoring
-   disable export and comparison feature (not yet reimplemented in vuetify)

## v0.5.0 - 2022-05-02

-   remove automatic install of cbUtilities
-   improve logging when processing results
-   improve error handling on invalid json
-   add compatiblity to view benchmarks run before v.0.4.4
-   remove unused starter parameters
-   cleanup jobscript and jube
-   add configuration file
-   provide configuration file via API
-   frameworks settings now rely on configuration file and gitlab variables instead of hardcoded values
-   fix jobscript preview
-   move mongodb to docker container

## v0.4.4 - 2022-03-18

-   move system info collection to cbDaemon
-   refactoring and cleanup
-   use jobscript preview from configuration for benchmark results
-   rework workpackage processing
-   switch from xmltodict to pands_read_xml for xml parsing
-   make frontend configurable via config.json

## v0.4.3 - 2022-02-18

-   add https via nginx with docker-compose

## v0.4.2 - 2022-01-24

-   update iostat metric mapping
-   add plot export feature

## v0.4.1 - 2022-01-05

-   change cbUtilities version referencing
-   fix legend creation for decile graphs (#12)
-   fix issues with measurement configurations
-   development-project can now access all projects configurations
-   change jobscript inputs to text-areas
-   several styling fixes
-   search-select no longer breaks when selecting an already selected entry
-   likwids cpu topology is now available in the benchmark results
-   installed gpus are now displayed in the hardware info section of a benchmark
-   improve calculation likwid metric calculation (NaN values are no longer considered for decile calculation)

## v0.4.0 - 2021-10-28

-   add Nvidia GPU monitoring via DCGM (#4)

## v0.3.0 - 2021-09-22

-   add project management

## v0.2.5 - 2021-09-21

-   improve error handling when processing results
-   disable cache when building frontend docker container

## v0.2.4 - 2021-09-15

-   use benchmark-continuous user for all ssh-related operations

## v0.2.3 - 2021-08-30

-   handle missing benchmark information

## v0.2.2 - 2021-08-16

-   add funtionality to delete benchmarks via frontend
-   improvements to benchmark overview

## v0.2.1 - 2021-08-10

-   automatic install of cbUtilities package
-   job script preview
-   fixes and improvements to pipeline

## v0.2.0 - 2021-07-19

-   port prototype to new benchmark center
-   split CI pipeline into separate jobs
-   deploy frontend via docker container
-   improve pipeline stability and error handling
-   use shared storage instead of home directory
-   refactor
