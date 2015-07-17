#!/bin/bash

DISKSPACE=`df -H /dev/root | sed '1d' | awk '{print $5}' | cut -d'%' -f1`
ALERT=80
logger "${DISKSPACE}% used.  Limit is ${ALERT}%"
if [ ${DISKSPACE} -ge ${ALERT} ]; then
    logger "Disk utilization over limit.  Deleting 10 oldest files from /var/cache/avconv"
    find /var/cache/avconv -type f | tail -n -1 | xargs rm
    exit
  else
    logger "Disk itilization under limit.  No deletions necessary."

fi
