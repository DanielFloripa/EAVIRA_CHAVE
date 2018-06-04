#!/bin/bash

source chave.conf

SRC_LIST=(`ls -d ${CS_FDR_EUCALYPTUS}/* | grep trace.txt`)
ROOT_PROJ=`pwd`
GVT='src/Users/Source_Generator.py'


if [ "$1" == "get_trace" ]; then
    for SRC in ${SRC_LIST[@]}; do
        ${CS_PY} ${ROOT_PROJ}/${GVT} -service $1 -source ${SRC} -lock 'RandomMC'
    done
elif [ "$1" == "set_trace" ]; then
    for SRC in ${SRC_LIST[@]}; do
        ${CS_PY} ${ROOT_PROJ}/${GVT} -service $1 -source ${SRC} -lock 'RandomMC'
    done
else
    echo "USE: get_trace or set_trace"
fi