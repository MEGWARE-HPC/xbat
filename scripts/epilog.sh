#!/bin/bash

[[ ! "$SLURM_JOB_CONSTRAINTS" =~ "xbat" ]] && exit 0

# xbatd must be installed
[ ! -f /etc/systemd/system/xbatd.service ] && exit 0

# allow current measurement interval to finish before stopping service
sleep 10

systemctl stop xbatd.service || true