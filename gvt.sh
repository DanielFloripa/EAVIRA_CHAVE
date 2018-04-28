#!/bin/bash

SRC_LIST=(`ls -d input/eucalyptus-traces/* | grep trace.txt`)
for SRC in ${SRC_LIST[@]}; do
    if [ "$1" == "max_gvt" ]; then
	    RET=`python myGVT.py -source ${SRC} -max-gvt True`
	    export ${RET}
	else
	    python myGVT.py -source ${SRC}
	fi
done
