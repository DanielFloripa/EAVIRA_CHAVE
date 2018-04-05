#!/bin/bash
#
# Script para backup via SSH usando o rsync. Versão 0.2. Fonte: http://organelas.com/2009/08/07/
#
## Configurations ##
# Destino:  IP ou hostname da máquina de destino
DESTINO="ec2-34-230-18-64.compute-1.amazonaws.com"
#ec2-52-207-221-202.compute-1.amazonaws.com"
PEM="../masterChave.pem"
#
# Usuário no destino
USR=ubuntu
#
# Diretório de destino
PYPY="/pypy_portable"
PROJ="/CHAVE-Sim"
DIR=/home/ubuntu
#
# Origem: arquivos de origem
SRC="/home/daniel/Dropbox/UDESC/Mestrado/Pratico/simulations"
FILES="/*"
#
# Arquivo log
LOG=$SRC/.log/aws_backup`date +%Y-%m-%d`.log
#
## End of configurations!!! ##

if [ "$1" == "ssh" ]; then
    ssh -i $PEM $USR@$DESTINO
    exit
fi

touch READY

# Checar se a máquina de destino está ligada
/bin/ping -c 1 -W 2 $DESTINO > /dev/null
if [ "$?" -ne 0 ];
then
   echo -e `date +%c` >> $LOG
   echo -e "\n$DESTINO desligado." >> $LOG
   echo -e "Backup não realizado\n" >> $LOG
   echo -e "--- // ---\n" >> $LOG
   echo -e "\n$DESTINO indisponivel."
   echo -e "Backup não realizado.\n"
else
   HORA_INI=`date +%s`
   echo -e `date +%c` >> $LOG
   echo -e "\n$DESTINO ligado!" >> $LOG
   echo -e "Iniciando o backup...\n" >> $LOG
   if [ "$1" == "receive" ]; then
        echo "RECEIVING logs..."  >> $LOG
        scp -i $PEM $USR@$DESTINO:$DIR$PROJ/src/logs/* ./src/logs/
   else
        echo "SENDING..."  >> $LOG
        rsync -ah --update --stats --progress --log-file=$LOG -rave "ssh -i $PEM" $SRC$PROJ$FILES $USR@$DESTINO:$DIR$PROJ
        #rsync -ah --update --stats --progress --log-file=$LOG -rave "ssh -i $PEM" $SRC$PYPY$FILES $USR@$DESTINO:$DIR$PYPY
   fi
   HORA_FIM=`date +%s`
   TEMPO=`expr $HORA_FIM - $HORA_INI`
   echo -e "\nBackup finalizado com sucesso!" >> $LOG
   echo -e "Duração: $TEMPO s\n" >> $LOG
   echo -e "--- // ---\n" >> $LOG
   echo -e "\nBackup finalizado com sucesso!"
   echo -e "Duração: $TEMPO s\n"
   echo -e "Consulte o log da operação em $LOG.\n"
fi

exit

## TODO ##
#       - Incluir em cron job!
#       - Definir como lidar com o arquivo.log (deletar, arquivar, deixar...)
#       - Incluir wakeonlan para ligar o computador se estiver desligado
#       - Desligar máquina de destino após o término do backup
#       - Criar alça para quando a transferência falhar (e.g.,falta de espaço)

Configs in AWS instance

sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install htop python python-numpy

(wget -O - pi.dk/3 || curl pi.dk/3/ || fetch -o - http://pi.dk/3) | bash
sudo mv /home/ubuntu/bin/* /usr/bin
parallel --version
parallel --citation
