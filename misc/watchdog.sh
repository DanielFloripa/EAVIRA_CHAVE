#!/bin/bash 

source chave.conf

#FOLDER_NAME=${PWD##*/}

COUNT=0

while [ true ]; do
    sleep 2
    if [ -e "READY" ]; then
        rm READY
        TS=`date ${DP}`
        echo "Executing at $TS:"
        bash execute_simulator.sh $TS
        let "COUNT++"
    fi
done