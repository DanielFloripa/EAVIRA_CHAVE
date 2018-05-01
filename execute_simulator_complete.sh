#!/bin/bash

source chave.conf

CLEAR="false"

#killall dropbox

if "${CLEAR}" == "true"; then
    rm -rf ${CS_LOG_PATH}/*
    rm -rf ${CS_DATA_PATH}/*
fi
mkdir ${CS_LOG_PATH} 2> /dev/null
mkdir ${CS_DATA_PATH} 2> /dev/null

### ### ### ### ### ### ### ### ### ### ### ### ###
###  DATA FILE CONFIGURATIONS                   ###
### ### ### ### ### ### ### ### ### ### ### ### ###
# Sources:
SRC_LIST=(`ls -d ${CS_FDR_EUCALYPTUS}/* | grep trace.txt`)
SRC_LIST_HA=(`ls -d ${CS_FDR_EUCALYPTUS}/* | grep trace-ha.txt`)
AZ_CONF=( 13 24 7 12 7 8 12 8 31 32 31 32 ) # ('node core')
NIT=()
for SRC in ${SRC_LIST[@]}; do
    NIT+=( `wc -l < ${SRC}` )
    # python src/myGVT.py -source ${SRC}
done

### ### ### ### ### ### ### ### ### ### ### ### ###
###  OPTIONS CONFIGURATIONS                     ###
### ### ### ### ### ### ### ### ### ### ### ### ###
# Algorithm used for tests
TEST_LIST=( 'CHAVE' 'EUCA' 'MM' 'MBFD' )
# Placement or migration priority
PM_LIST=( 'PlacementFirst' 'MigrationFirst' )
# Hosts Organization : increasing or decreasing
FF_LIST=( 'FFD2I' 'FF3D')
# If test has overbooking strategy
WITH_OVERB=( 'False' 'True' ) # Shared, or Dedicated
# TODO: Selection AZs to place replicas
AZ_2_REGIONS=('HA' 'LoadBalance' 'BestEffort')
# WINDOW time/size: ('min' 'step' 'max')
WT=('1' '2' '20')
WS=('20' '20' '60')

cd src
_INIT=`date +%s`
echo -e "\tExecuting at" `date +${CS_DP}`

### ### ### ### ### ### ### ### ### ### ### ### ###
###  EXECUTING IN HOST WITH PARALLEL            ###
### ### ### ### ### ### ### ### ### ### ### ### ###
if [ ${CS_isAWS} == true ]; then
    parallel --bar python __init__.py -nit ${NIT[@]} -in ${SRC_LIST[@]} -az ${AZ_CONF[@]} -ha ${SRC_LIST_HA[@]} \
    -alg {1} -pm {2} -ff {3}  -wt {4} -ws {5} -ob {6} ::: \
        ${TEST_LIST[@]} ::: \
        ${PM_LIST[@]} ::: \
        ${FF_LIST[@]} ::: \
        $(seq ${WT[0]} ${WT[1]} ${WT[2]}) ::: \
        $(seq ${WS[0]} ${WS[1]} ${WS[2]}) ::: \
        ${WITH_OVERB[@]} ::: \

### ### ### ### ### ### ### ### ### ### ### ### ###
###  EXECUTING IN G5K                           ###
### ### ### ### ### ### ### ### ### ### ### ### ###
elif [ ${CS_isG5K} == true ]; then  # If in Grid 5000 we need use nested for #
    TEST=${TEST_LIST[0]} # test for 'CHAVE' algorithm
    for OB in ${WITH_OVERB[@]}; do
        for PM in "${PM_LIST[@]}"; do
            for FF in "${FF_LIST[@]}"; do
                for TIME in `seq ${WT[0]} ${WT[1]} ${WT[2]}`; do
                    for SIZE in `seq ${WS[0]} ${WS[1]} ${WS[2]}`; do
                        it=0
                        for SRC in "${SRC_LIST[@]}"; do
                            echo -e "Executing Test"`date +${CS_DP}`"_${TEST}_${PM}_${FF}_${TIME}_${SIZE}_${OB}"
                            python main.py\
                                    -nit ${NIT[$it]}\
                                    -algorithm $TEST\
                                    -pm $PM\
                                    -ff $FF\
                                    -input "$FDR_EUCALYPTUS/$SRC"\
                                    -az ${AZ_LIST[$it]}\
                                    -wt "$TIME"\
                                    -ws "$SIZE"\
                                    -overb $OB
                            let "it++"
                        done
                    done
                done
            done
        done
    done

    TEST=${TEST_LIST[1]} # EUCA
    PM="None"
    FF="None"
    for OB in ${WITH_OVERB[@]}; do
        for TIME in `seq ${WT[0]} ${WT[1]} ${WT[2]}`; do
            for SIZE in `seq ${WS[0]} ${WS[1]} ${WS[2]}`; do
                it=0
                for SRC in "${SRC_LIST[@]}"; do
                    echo -e "Executing Test"`date +${CS_DP}`"_${TEST}_${PM}_${FF}_${TIME}_${SIZE}_${OB}"
                    python main.py\
                            -nit ${NIT[$it]}\
                            -algorithm $TEST\
                            -pm $PM\
                            -ff $FF\
                            -input "$FDR_EUCALYPTUS/$SRC"\
                            -az ${AZ_LIST[$it]}\
                            -wt "$TIME"\
                            -ws "$SIZE"\
                            -overb $OB
                    let "it++"
                done
            done
        done
    done
fi

let "_END=`date +%s`-${_INIT}"
echo -e "\n\tThis simulation ended at" `date +${CS_DP}` " and took ${_END} seconds"

#dropbox start 2> /dev/null
