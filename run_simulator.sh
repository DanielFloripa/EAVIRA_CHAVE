#!/bin/bash

source chave.conf

if [ "$1" == "install" ]; then
	install_chave
	exit
fi

echo -e "${CS_LOGO} ${_NC}"

CLEAR_ALL=false
PLOT=true
SYNC=true

if ${CLEAR_ALL} == true; then
    rm -rf "${CS_PROJ_ROOT}/output/"
fi

mkdir -p ${CS_LOG_PATH} 2> /dev/null
mkdir -p ${CS_DATA_PATH} 2> /dev/null

AZ_CONF=( 13 24 7 12 7 8 12 8 31 32 31 32 ) # ('node core')
    #________________
   #/ |AZ_|Node|Cores\          {CHAVE}
  #/  | 1 | 13 | 24  |\____
 #/   | 2 | 7  | 12  | >LC0\__ Source: ${CS_SOURCE_FOLDER}
#/ /\ | 3 | 7  | 8   |/       \__/l__/L___/l_/l__M___
#\ \/ |===|====|=====K         >_GC___  ____  ___ __/
 #\   | 4 | 12 | 8   |\     __/  \/   \/    \/   V
  #\  | 5 | 31 | 32  | >LC1/    Log: ${CS_LOG_LEVEL}
   #\_|_6_|_31_|_32__|/

TEST_LIST=(  'EUCA' 'CHAVE' ) # 'MM' MBFD )
FF_LIST=( 'FFD2I') # 'FF3D')
CONSOLID_ALGO=( 'LOCK'  'MAX' ) #  'MIN' ) # 'ha' )
WITH_CONSOLID=( 'False' 'True' )
WITH_OVERCOMM=( 'False' )
ENABLE_REPLIC=( 'False' 'True' )
LOCK_CASE=( 'RANDOM' 'False' 'True' 'None' )
WT=('1' '2' '2')  # Window time: ('min' 'step' 'max')

# TODO: implemetar um criador de AZs e regioes
# AZ_2_REGIONS=('HA' 'LB' 'BF')

# Sources:
SRC_LIST=(`ls -d ${CS_FDR_EUCALYPTUS}/* | grep trace.txt`)
SRC_LIST_PLUS=(`ls -d ${CS_FDR_EUCALYPTUS}/* | grep trace-plus.txt`)
if [[ ${#SRC_LIST_PLUS[@]} -lt ${#SRC_LIST[@]} ]]; then
    echo -e "${_RED}Genearting some plus info! ${#SRC_LIST_PLUS[@]} < ${#SRC_LIST[@]} ${_NC}"
    # Doc: two parameters: <'create_trace'> or <'trace_plus'>
    bash gvt.sh 'trace_plus'
    SRC_LIST_PLUS=(`ls -d ${CS_FDR_EUCALYPTUS}/* | grep trace-plus.txt`)
fi

NIT=()
for SRC in ${SRC_LIST[@]}; do
    NIT+=( `wc -l < ${SRC}` )
done

pushd . > /dev/null
cd src

RUN_S=`date +%s`
# --tmpdir /media/debian/logs  -j16
if [ ${CS_isAWS} == true ]; then
    ${PARALLEL} --bar ${CS_PY} __init__.py -nit ${NIT[@]} -in ${SRC_LIST[@]} -az ${AZ_CONF[@]} -ha ${SRC_LIST_PLUS[@]}  -alg {1} -ca {2} -ff {3}  -wt {4} -lock {5} -ovc {6} -cons {7} -repl {8}  ::: \
        ${TEST_LIST[@]} ::: \
        ${CONSOLID_ALGO[@]} ::: \
        ${FF_LIST[@]} ::: \
        $(seq ${WT[0]} ${WT[1]} ${WT[2]}) ::: \
        ${LOCK_CASE[@]} ::: \
        ${WITH_OVERCOMM[@]} ::: \
        ${WITH_CONSOLID[@]} ::: \
        ${ENABLE_REPLIC[@]} ::: \

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

let "_END=`date +%s`-${RUN_S}"
_NOW=`date +${CS_DP}`
SIM_RESULT="This simulation ended at ${_NOW} and took ${_END} seconds."
echo -e "${_RED}\n\t ${SIM_RESULT}  ${_NC}"
echo -e ${SIM_RESULT} >> "${CS_OUTPUT_PATH}/simulation_resume.txt"
popd > /dev/null

#if [ "${USER}" == "ubuntu" ]; then
#    scp -i /home/${USER}/Dropbox/chave2.pem ${CS_DATA_PATH} 10.0.0.16:/var/www/html/
#    scp -i /home/${USER}/Dropbox/chave2.pem ${CS_LOG_PATH} 10.0.0.16:/var/www/html/
#fi

# Todo: Automatizar processo
if [ ${PLOT} == true ]; then
	pushd .
	cd ${CS_PROJ_ROOT}/Plots/
	R -f database.R  ${CS_START}
	R -f databaseSpider.R ${CS_START}
	popd
fi
if [ ${SYNC} == true ]; then
    command -v aws >/dev/null 2>&1 || {
        echo >&2 "Is required 'awscli' but it's not installed...";
        echo "sucesso" | sudo -S pip install awscli
        pushd .
        cd ~
        unzip Dropbox/aws.zip
        popd
    }
    S3_BUCK="chave-output"
    OUTPUT="${CS_PROJ_ROOT}"/output/
    aws s3 sync ${OUTPUT} s3://${S3_BUCK} --acl public-read # --grants full=uri=http://acs.amazonaws.com/groups/global/AllUsers
fi


exit


#aws s3 mv ${OUTPUT} s3://${S3_BUCK}

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


    for TEST in ${TEST_LIST[@]}; do
        if [ "$TEST" == "EUCA" ]; then
		echo -e "Executing: $TEST"
             ${PARALLEL} --bar ${CS_PY} __init__.py -nit ${NIT[@]} -in ${SRC_LIST[@]} -az ${AZ_CONF[@]} -ha ${SRC_LIST_PLUS[@]} -alg "EUCA" -wt {1} ::: $(seq ${WT[0]} ${WT[1]} ${WT[2]}) :::
        else
		echo "Executing: "$TEST
            ${PARALLEL} --bar ${CS_PY} __init__.py -nit ${NIT[@]} -in ${SRC_LIST[@]} -az ${AZ_CONF[@]} -ha ${SRC_LIST_PLUS[@]} -alg ${TEST} -ca {1} -ff {2}  -wt {3} -lock {4} -ovc {5} -cons {6} -repl {7} ::: \
                ${CONSOLID_ALGO[@]} ::: \
                ${FF_LIST[@]} ::: \
                $(seq ${WT[0]} ${WT[1]} ${WT[2]}) ::: \
                ${LOCK_CASE[@]} ::: \
                ${WITH_OVERCOMM[@]} ::: \
                ${WITH_CONSOLID[@]} ::: \
                ${ENABLE_REPLIC[@]} :::
        fi
    done
