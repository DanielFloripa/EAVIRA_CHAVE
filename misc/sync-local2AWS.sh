#!/bin/bash
# Script para backup instalação acesso via SSH usando o rsync. Versão 0.2. Fonte: http://organelas.com/2009/08/07/

## Configurations ##
# Destino:  IP ou hostname da máquina de destino
DESTINO="ec2-34-230-18-64.compute-1.amazonaws.com"
PEM="../masterChave.pem"
# Usuário no destino
USR=ubuntu
## End of configurations!!! ##

if [ "$1" == "ssh" ]; then
    ssh -i ${PEM} ${USR}@${DESTINO}
    exit
elif [ "$1" == "sync" ]; then
    # Diretórios de destino
    PYPY="/pypy_portable"
    PROJ="/CHAVE-Sim"
    DIR=/home/ubuntu
    # Origem: arquivos de origem
    SRC="/home/daniel/Dropbox/UDESC/Mestrado/Pratico/simulations"
    FILES="/*"
    # Arquivo log
    LOG=${SRC}/.log/aws_backup`date +%Y-%m-%d`.log
    # Marcador para o watchdog.sh
    touch READY

    # Checar se a máquina de destino está ligada
    /bin/ping -c 1 -W 2 $DESTINO > /dev/null
    if [ "$?" -ne 0 ]; then
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
       if [ "$2" == "receive" ]; then
            echo "RECEIVING logs..."  >> $LOG
            scp -i $PEM $USR@$DESTINO:$DIR$PROJ/src/logs/* ./src/logs/
       elif [ "$2" == "send" ]; then
            echo "SENDING..."  >> $LOG
            rsync -ah --update --stats --progress --log-file=$LOG -rave "ssh -i $PEM" $SRC$PROJ$FILES $USR@$DESTINO:$DIR$PROJ
            #rsync -ah --update --stats --progress --log-file=$LOG -rave "ssh -i $PEM" $SRC$PYPY$FILES $USR@$DESTINO:$DIR$PYPY
       else
            echo -n "You must specify 'send' or 'receive'"
       fi
       HORA_FIM=`date +%s`
       TEMPO=`expr $HORA_FIM - $HORA_INI`
       echo -e "\nBackup finalizado com sucesso!" >> $LOG
       echo -e "Duração: $TEMPO s\n" >> $LOG
       echo -e "--- // ---\n" >> $LOG
       echo -e "\nBackup finalizado com sucesso!"
       echo -e "Duração: $TEMPO s\n"
       echo -e "Consulte o log da operação em $LOG.\n"
       exit
    fi
#Configs for new instance
elif [ "$1" == "install" ]; then
    cd ~
    sudo apt-get update && sudo apt-get upgrade -y
    sudo apt-get install git vim nano htop python python-numpy
    #    This project:
    git clone https://github.com/DanielFloripa/CHAVE-Sim.git
    #	Parallel project:
    (wget -O - pi.dk/3 || curl pi.dk/3/ || fetch -o - http://pi.dk/3) | bash
    sudo cp -rf ~/bin/* /usr/bin
    sudo cp -rf ~/share/* /usr/share/
    rm -rf ~/bin ~/share parallel**
    parallel --version
    parallel --citation
    # R-cran
	sudo apt-get install r-base r-base-dev libxml2-dev libcurl4-openssl-dev libssl-dev 
	wget https://download1.rstudio.org/rstudio-xenial-1.1.447-amd64.deb
	sudo chmod +x rstudio-xenial-1.1.447-amd64.deb
	sudo dpkg -i rstudio-xenial-1.1.447-amd64.deb
	rm -rf rstudio-xenial-1.1.447-amd64.deb
else
    echo -e "Some error in parameter, must be: \n\t $0 ssh |or| \n\t $0 sync +{send || receive} |or| \n\t $0 install USENAME"
fi