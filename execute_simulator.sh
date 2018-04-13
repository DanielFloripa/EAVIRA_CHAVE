#!/bin/bash

source chave.conf

#if [ $@ -ge 1 ]; then
#    TS=$1
#else
#    echo "no parametter"
#    TS=`date +${DP}`
#fi

mkdir ${CS_LOGPATH} 2> /dev/null
mkdir ${CS_DATAPATH} 2> /dev/null

TEST_LIST=( 'CHAVE' 'EUCA')
PM_LIST=( 'PlacementFirst' ) # 'MigrationFirst' )
FF_LIST=( 'FFD2I') # 'FF3D')
WITH_OVERB=( 'False' ) # 'True' ) Shared, or Dedicated

# Sources:
SRC_LIST=(`ls -d ${CS_FDR_EUCALYPTUS}/* | grep trace.txt`)
AZ_LIST=( '13:24' '7:12' '7:8' '12:8' '31:32' '31:32' ) # ('node:core')
NIT=()
for SRC in ${SRC_LIST[@]}; do
    NIT+=(`wc -l < $SRC`)
    python src/myGVT.py -source ${SRC}
done
SRC_HA_LIST=(`ls -d ${CS_FDR_EUCALYPTUS}/* | grep trace-ha.txt`)
#echo ${NIT[@]}



# WINDOW time/size='min step max'
WT=('2000' '2000' '2001')
WS=('20' '20' '21')
AV=0.9995

cd src
echo "executing at " `date +$DP`

if [ ${CS_isAWS} == true ]; then
    parallel --bar 'python main.py -alg {1} -pm {2} -ff {3} -nit {4} -in {5} -az {6} -av {10} -wt {7} -ws {8} -ovb {9}' ::: \
        ${TEST_LIST[@]} ::: \
        ${PM_LIST[@]} ::: \
        ${FF_LIST[@]} ::: \
        ${NIT[@]} :::+ \
        ${SRC_LIST[@]} :::+ \
        ${AZ_LIST[@]} ::: \
        $(seq ${WT[0]} ${WT[1]} ${WT[2]}) ::: \
        $(seq ${WS[0]} ${WS[1]} ${WS[2]}) ::: \
        ${WITH_OVERB[@]} ::: \
        ${AV}

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
                                    -availab $AV\
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
                            -availab $AV\
                            -wt "$TIME"\
                            -ws "$SIZE"\
                            -overb $OB
                    let "it++"
                done
            done
        done
    done
fi

