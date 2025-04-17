#!/bin/bash

[[ ! "$SLURM_JOB_CONSTRAINTS" =~ "xbat" ]] && exit 0

# xbatd must be installed
[ ! -f /etc/systemd/system/xbatd.service ] && exit 0

# stop collectd in case it was not correctly shut down from last run
systemctl stop xbatd.service || true

RUN_PATH="/run/xbatd"

mkdir -m 0700 -p $RUN_PATH

# write jobId to file since collectd must know what job it is monitoring
echo "$SLURM_JOBID" > "$RUN_PATH/job"

BENCHMKARK_STATUS_FILE_PATH="/run/xbatd/benchmarkInProgress"

[ -e "$BENCHMKARK_STATUS_FILE_PATH" ] && rm "$BENCHMKARK_STATUS_FILE_PATH"

# start measurements
systemctl start xbatd.service || true

# TODO improve concept
# wait for collectd to detect wether microbenchmarking is necessary
sleep 5

counter=0
# if microbenchmarking is necessary, wait for it to finish (maximum of 300 seconds)
if [ -e "$BENCHMKARK_STATUS_FILE_PATH" ];then
    until [ ! -e "$BENCHMKARK_STATUS_FILE_PATH" ] || [ $counter -gt 59 ]; do
        counter=$((counter+1))
        sleep 5
    done
fi

exit 0