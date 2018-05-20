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

# Sources:
SRC_LIST=(`ls -d ${CS_FDR_EUCALYPTUS}/* | grep trace.txt`)
SRC_LIST_HA=(`ls -d ${CS_FDR_EUCALYPTUS}/* | grep trace-ha.txt`)
AZ_CONF=( 13 24 7 12 7 8 12 8 31 32 31 32 ) # ('node core')

####################|
#AZ____node_core____|                  {CHAVE}
####################|
#DS1    13   24     |\_______
#DS2    7    12     | > LC0  \__
#DS3    7    8      |/          \__/l__/l___/l_/l__M___
#===================K            >_GC___  ____  ___ __/
#DS4    12   8      |\        __/  \/   \/    \/   V
#DS5    31   32     | >_LC1__/
#DS6    31   32     |/
####################|

TEST_LIST=('CHAVE' ) # 'EUCA' 'MM' MBFD )
PM_LIST=( 'PlacementFirst' ) # 'MigrationFirst' )
FF_LIST=( 'FFD2I') # 'FF3D')
WITH_CONSOLIDATION=( 'True' 'False')
WITH_OVERCOM=( 'True' 'False' ) # Overcommitting
# TODO: para implemetar um criador de AZs e regioes
# AZ_2_REGIONS=('HA' 'LoadBalance' 'BestEffort')

NIT=()
for SRC in ${SRC_LIST[@]}; do
    NIT+=( `wc -l < ${SRC}` )
    # python src/myGVT.py -source ${SRC}
done
# WINDOW time/size: ('min' 'step' 'max')
WT=('1' '2' '2')
WS=('20' '20' '21')

cd src
pushd .
_INIT=`date +%s`
echo -e "\tExecuting at" `date +${CS_DP}`

if [ ${CS_isAWS} == true ]; then
    parallel --bar ${CS_PY} __init__.py -nit ${NIT[@]} -in ${SRC_LIST[@]} -az ${AZ_CONF[@]} -ha ${SRC_LIST_HA[@]} \
    -alg {1} -pm {2} -ff {3}  -wt {4} -ws {5} -ovc {6} -cons {7} ::: \
        ${TEST_LIST[@]} ::: \
        ${PM_LIST[@]} ::: \
        ${FF_LIST[@]} ::: \
        $(seq ${WT[0]} ${WT[1]} ${WT[2]}) ::: \
        $(seq ${WS[0]} ${WS[1]} ${WS[2]}) ::: \
        ${WITH_OVERCOM[@]} ::: \
        ${WITH_CONSOLIDATION[@]} ::: \

elif [ ${CS_isG5K} == true ]; then  # If in Grid 5000 we need use nested for #
    TEST=${TEST_LIST[0]} # test for 'CHAVE' algorithm
    for OC in ${WITH_OVERCOM[@]}; do
        for PM in "${PM_LIST[@]}"; do
            for FF in "${FF_LIST[@]}"; do
                for TIME in `seq ${WT[0]} ${WT[1]} ${WT[2]}`; do
                    for SIZE in `seq ${WS[0]} ${WS[1]} ${WS[2]}`; do
                        it=0
                        for SRC in "${SRC_LIST[@]}"; do
                            echo -e "Executing Test"`date +${CS_DP}`"_${TEST}_${PM}_${FF}_${TIME}_${SIZE}_${OC}"
                            ${CS_PY} main.py\
                                    -nit ${NIT[$it]}\
                                    -algorithm $TEST\
                                    -pm $PM\
                                    -ff $FF\
                                    -input "$FDR_EUCALYPTUS/$SRC"\
                                    -az ${AZ_LIST[$it]}\
                                    -wt "$TIME"\
                                    -ws "$SIZE"\
                                    -ovc $OC
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
    for OC in ${WITH_OVERCOM[@]}; do
        for TIME in `seq ${WT[0]} ${WT[1]} ${WT[2]}`; do
            for SIZE in `seq ${WS[0]} ${WS[1]} ${WS[2]}`; do
                it=0
                for SRC in "${SRC_LIST[@]}"; do
                    echo -e "Executing Test"`date +${CS_DP}`"_${TEST}_${PM}_${FF}_${TIME}_${SIZE}_${OC}"
                    ${CS_PY} main.py\
                            -nit ${NIT[$it]}\
                            -algorithm $TEST\
                            -pm $PM\
                            -ff $FF\
                            -input "$FDR_EUCALYPTUS/$SRC"\
                            -az ${AZ_LIST[$it]}\
                            -wt "$TIME"\
                            -ws "$SIZE"\
                            -ovc $OC
                    let "it++"
                done
            done
        done
    done
fi

let "_END=`date +%s`-${_INIT}"
echo -e "\n\tThis simulation ended at" `date +${CS_DP}` " and took ${_END} seconds"

popd

#if [ "${USER}" == "debian" ]; then
#    ls -s ${CS_LOG_OUTPUT} logs/
#fi
#    LOG_FDR="/media/debian/logs/"
#    if [ -e ${LOG_FDR} ]; then
#        echo "sucesso" | sudo -S rsync -ah --update --progress logs/* ${LOG_FDR}
#        rm -rf logs/*
#    else
#        udisksctl mount --block-device=/dev/vde
#        sleep 5
#        echo "sucesso" | sudo -S rsync -ah --update --progress logs/* ${LOG_FDR}
#        rm -rf logs/*
#    fi
#fi
