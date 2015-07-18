#!/bin/bash

TARGET=/var/cache/avconv/
while : ; do
	DISKSPACE=`df -H /dev/root | sed '1d' | awk '{print $5}' | cut -d'%' -f1`
	ALERT=70
	logger "${DISKSPACE}% used.  Limit is ${ALERT}%"
	if [ ${DISKSPACE} -ge ${ALERT} ]; then
	    	logger "Disk utilization over limit.  Deleting 1 oldest files from $TARGET"
	    	ls -A1 $TARGET  | head -1 | xargs -I '{}' -- sh -c "logger Deleting: $TARGET/'{}' && rm $TARGET/'{}'"
	  else
	    	logger "Disk utilization under limit.  No deletions necessary."
		exit	
	fi
done
logger "Done cleanup"
