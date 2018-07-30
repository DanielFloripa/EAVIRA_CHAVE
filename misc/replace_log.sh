 WORD="\[WARNING\ \|\ Infra\ \ \ \ \|\ migrate\ \ \ \ \ \ \ \ \ \ \ \ \ \ \]\ \-\-\>\ Are"

list=`ls *`
for file in ${list[@]}; do 
sed -i -e "/${WORD}.*/d" ${file}
done
