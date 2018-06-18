#!/bin/bash

source chave.conf

PARALLEL=parallel
command -v ${PARALLEL} >/dev/null 2>&1 || {
    export PARALLEL=~/bin/parallel
}

echo -e "${_GREEN}\tRunning globally since: ${CS_START} ${_NC}"

CLEAR=false

if ${CLEAR} == true; then
    rm -rf ${CS_LOG_PATH}/*
    rm -rf ${CS_DATA_PATH}/*
fi

mkdir -p ${CS_LOG_PATH} 2> /dev/null
mkdir -p ${CS_DATA_PATH} 2> /dev/null

AZ_CONF=( 13 24 7 12 7 8 12 8 31 32 32 32 ) # ('node core')
       #####################|
      ###AZ____node_core____|                  {CHAVE}
    #   ####################|
  # _   #DS1    13   24     |\_______
#  / \  #DS2    7    12     | > LC0  \__
# {   } #DS3    7    8      |/          \__/l__/l___/l_/l__M___
 # \_/  #===================K            >_GC___  ____  ___ __/
   #    #DS4    12   8      |\        __/  \/   \/    \/   V
     #  #DS5    31   32     | >_LC1__/
      ###DS6    32   32     |/
       #####################|
TEST_LIST=( 'CHAVE' 'EUCA' )  # 'MM' MBFD )
FF_LIST=( 'FFD2I') # 'FF3D')
CONSOLID_ALGO=( 'LOCK' 'MAX' ) #  'MIN' ) # 'ha' )
WITH_CONSOLID=( 'True' 'False' )
WITH_OVERCOMM=( 'False' ) # 'False' )
ENABLE_REPLIC=( 'True' 'False' )
LOCK_CASE=( 'RANDOM' 'True' 'False' )
WT=('1' '2' '2')  # Window time: ('min' 'step' 'max')

# TODO: implemetar um criador de AZs e regioes
# AZ_2_REGIONS=('HA' 'LB' 'BF')

# Sources:
SRC_LIST=(`ls -d ${CS_FDR_EUCALYPTUS}/* | grep trace.txt`)
SRC_LIST_PLUS=(`ls -d ${CS_FDR_EUCALYPTUS}/* | grep trace-plus.txt`)
if [[ ${#SRC_LIST_PLUS[@]} -lt ${#SRC_LIST[@]} ]]; then
    echo -e "${_WARN}Need to create some plus info! ${#SRC_LIST_PLUS[@]} < ${#SRC_LIST[@]} ${_NC}"
    bash gvt.sh 'trace_plus' #'create_trace' or 'trace_plus'
    SRC_LIST_PLUS=(`ls -d ${CS_FDR_EUCALYPTUS}/* | grep trace-plus.txt`)
fi

NIT=()
for SRC in ${SRC_LIST[@]}; do
    NIT+=( `wc -l < ${SRC}` )
done

cd src
pushd .
RUN_S=`date +%s`
# --tmpdir /media/debian/logs  -j16
if [ ${CS_isAWS} == true ]; then
    for TEST in ${TEST_LIST[@]}; do
        if [ "$TEST" == "EUCA" ]; then
            ${PARALLEL} --bar ${CS_PY} __init__.py -nit ${NIT[@]} -in ${SRC_LIST[@]} -az ${AZ_CONF[@]} -ha ${SRC_LIST_PLUS[@]} -alg "EUCA" -wt {1} ::: $(seq ${WT[0]} ${WT[1]} ${WT[2]}) :::
        else
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
SIM_RESULT="${_WARN}\n\tThis simulation ended at ${_NOW} and took ${_END} seconds. ${_NC}"
echo -e ${SIM_RESULT}
echo -e ${SIM_RESULT} >> "${CS_OUTPUT_PATH}/simulation_resume.txt"
popd

if [ "${USER}" == "ubuntu" ]; then
    scp -i /home/${USER}/Dropbox/chave2.pem ${CS_DATA_PATH} 10.0.0.16:/var/www/html/
    scp -i /home/${USER}/Dropbox/chave2.pem ${CS_LOG_PATH} 10.0.0.16:/var/www/html/
fi

#exit 1

PLOT=false
SYNC=false
# Todo: Automatizar processo
if [ ${PLOT} == true ]; then
	pushd .
	cd ${CS_PROJ_ROOT}/output/Plots/
	for elem in ${TEST_LIST[@]}; do
	        if [ "EUCA" == "${elem}" ]; then
        		./Optimized_All_graphsFunc_EUCA.r ${CS_START}
        	else
            	./Optimized_All_graphsFunc.r ${CS_START}
        	fi
    	done
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
    aws s3 sync ${OUTPUT} s3://${S3_BUCK} --acl public-read --exclude "*.Rhistory*",".Rproj" # --grants full=uri=http://acs.amazonaws.com/groups/global/AllUsers
fi

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
