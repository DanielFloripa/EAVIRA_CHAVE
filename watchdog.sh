#!/bin/bash 

#NFS_RAIZ=`pwd`
#FOLDER_NAME=${PWD##*/}


while [ true ]; do
    sleep 1
    if [ -e "READY" ]; then
        TS=`date +%s`
        echo "Executing at $TS: "
        bash execute_simulator.sh > log-$TS.log
        rm READY
    fi
done