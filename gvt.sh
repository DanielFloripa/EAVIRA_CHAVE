#!/bin/bash

SRC_LIST=(`ls -d input/small-eucalyptus-traces/* | grep trace.txt`)
for SRC in ${SRC_LIST[@]}; do
    if [ "$1" == "max_gvt" ]; then
	    RET=`python src/myGVT.py -source ${SRC} -max-gvt True`
	    export ${RET}
	else
	    python src/myGVT.py -source ${SRC}
	fi
done
