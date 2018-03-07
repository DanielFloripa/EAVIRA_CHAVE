#!/bin/bash

NFS_RAIZ=`pwd`  #'/home/daniel/Dropbox/UDESC/Mestrado/Pratico/simulations'
NFS_DIR=$NFS_RAIZ'/CHAVE-Sim'
PYPY="../../pypy_portable/bin/pypy"
FDR_EUCALYPTUS=$NFS_RAIZ"/database/eucalyptus-traces"
mkdir $NFS_RAIZ/results/ 2> /dev/null

TEST_LIST=( 'CHAVE' 'EUCA') # 'google' )
PM_LIST=( 'PlacementFirst' ) # 'MigrationFirst' )
FF_LIST=( 'FFD2I') # 'FF3D')
SRC_LIST=(`ls -d ${FDR_EUCALYPTUS}/* | grep DS`) #('DS1-trace.txt' 'DS2-trace.txt' 'DS3-trace.txt' 'DS4-trace.txt' 'DS5-trace.txt' 'DS6-trace.txt')
AZ_LIST=( '13:24' '7:12' '7:8' '12:8' '31:32' '31:32' ) # ('node:core')
#AZ_LIST=( '7 12' )
WITH_OVERB=( 'False' ) # 'True' ) Shared, or Dedicated

AV=0.9995 # azs: ${#SRC_LIST[@]}")
# WINDOW time/size='min step max'
WT=('2000' '2000' '2001')
WS=('20' '20' '21')

cd src
#rm slav-CHAVE.log slav-EUCA.log
#HEADER="id\tws\twt\tsv\tenergy cons\toverb"
#echo -e $HEADER >> slav-CHAVE.log
#echo -e $HEADER >> slav-EUCA.log

parallel --bar 'python main.py -nit {1} -alg {2} -pm {3} -ff {4} -in {5} -az {6} -av {10} -out `date +%s`"_{2}_{3}_{4}_{7}_{8}_{9}.log" -wt {7} -ws {8} -ovb {9}' ::: \
    2000 ::: \
    ${TEST_LIST[@]} ::: \
    ${PM_LIST[@]} ::: \
    ${FF_LIST[@]} ::: \
    ${SRC_LIST[@]} :::+ \
    ${AZ_LIST[@]} ::: \
    $(seq ${WT[0]} ${WT[1]} ${WT[2]}) ::: \
    $(seq ${WS[0]} ${WS[1]} ${WS[2]}) ::: \
    ${WITH_OVERB[@]} ::: \
    0.9995


exit

${AZ_LIST[$it]}

TEST=${TEST_LIST[0]} ## CHAVE
for OB in ${WITH_OVERB[@]}; do
    for PM in "${PM_LIST[@]}"; do
        for FF in "${FF_LIST[@]}"; do
            for TIME in `seq ${WT[0]} ${WT[1]} ${WT[2]}`; do
                for SIZE in `seq ${WS[0]} ${WS[1]} ${WS[2]}`; do
                    it=0
                    for SRC in "${SRC_LIST[@]}"; do
                        NIT=$(wc -l < $FDR_EUCALYPTUS/$SRC)
                        STR=`date +%s`"_${TEST}_${NIT}_${PM}_${FF}_${SRC}_${TIME}_${SIZE}_${OB}"
                        OUTPUT="output_${STR}.log"
                        echo "executing: python" $STR
                        python main.py\
                                -nit $NIT\
                                -algorithm $TEST\
                                -pm $PM\
                                -ff $FF\
                                -input "$FDR_EUCALYPTUS/$SRC"\
                                -az ${AZ_LIST[$it]}\
                                -availab $AV\
                                -output "$OUTPUT"\
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

TEST=${TEST_LIST[1]} ## EUCA
PM="None"
FF="None"
for OB in ${WITH_OVERB[@]}; do
    for TIME in `seq ${WT[0]} ${WT[1]} ${WT[2]}`; do
        for SIZE in `seq ${WS[0]} ${WS[1]} ${WS[2]}`; do
            it=0
            for SRC in "${SRC_LIST[@]}"; do
                NIT=$(wc -l < $FDR_EUCALYPTUS/$SRC)
                STR=`date +%s`"_${TEST}_${NIT}_${PM}_${FF}_${SRC}_${TIME}_${SIZE}_${OB}"
                OUTPUT="output_${STR}.log"
                echo "executing: python" $STR
                python main.py\
                        -nit $NIT\
                        -algorithm $TEST\
                        -pm $PM\
                        -ff $FF\
                        -input "$FDR_EUCALYPTUS/$SRC"\
                        -az ${AZ_LIST[$it]}\
                        -availab $AV\
                        -output "$OUTPUT"\
                        -wt "$TIME"\
                        -ws "$SIZE"\
                        -overb $OB
                let "it++"
            done
        done
    done
done
