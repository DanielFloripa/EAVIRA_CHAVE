#!/usr/bin/python2

import sys
import subprocess
import commands

# print 'Number of arguments:', len(sys.argv), 'arguments.'
# print 'Argument List:', str(sys.argv)

def extract_columns ( directory, localfilename, fileoutput ):

	localfilename=directory+localfilename
	#print "\n\nextract_columns: "+localfilename
	for line in open(localfilename).xreadlines():
		column=line.split()
		# print column
		if column[1] == 'NA:':
			NAList=column[2]
			TAtotal=column[4]
			NDList=column[6]
			NMIGList=column[8]
			REPLList=column[10].split("/")
			RECFGList=column[12].split("/")
			DELList=column[14].split("/")
			# print (("%s \n%s %s %s %s %s %s") % \
			# 	(column,NAList,NDList,NMIGList,REPLList,RECFGList,DELList) )	
			# print (("%s %s %s %s %s %s") % \
			# 	(NAList,NDList,NMIGList,REPLList,RECFGList,DELList) )

		if column[1] == 'TA:':
			TAList=column[2]
			TAdev=column[4]
			OPList=column[6]
			OPdev=column[8]
			EngList=column[10]
			Engdev=column[12]
			SLAList=column[15]
			SLAdev=column[17]
			StealList=column[21]
			Stealdev=column[23]
			# print (("%s\n %s %s %s %s %s %s %s %s %s %s") % \
			#  	(column,TAList, TAdev, OPList, OPdev, EngList, Engdev, \
			#  	SLAList, SLAdev, StealList, Stealdev) )	
			# fileoutput.write (""+localfilename+","+EngList+","+Engdev+","+SLAList\
			#  	+","+SLAdev+","+StealList+","+Stealdev+"\n")
			print (("%s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s") % \
				(localfilename,NAList,NDList,NMIGList,REPLList,RECFGList,DELList, \
				TAList, TAdev, OPList, OPdev, EngList, Engdev, \
				SLAList, SLAdev, StealList, Stealdev))
			fileoutput.write (""+localfilename+","+NAList+","+TAtotal+","+NDList+","+NMIGList+","+REPLList[0]+","+REPLList[1]\
				+","+RECFGList[0]+","+RECFGList[1]+","+DELList[0]+","+DELList[1]+","+TAList+","+TAdev+","+OPList+","\
				+OPdev+","+EngList+","+Engdev+","+SLAList+","+SLAdev+","+StealList+","+Stealdev+"\n")
	return;

def main():

	if (len(sys.argv) < 2):
		print "python data.py <PATHDIRECTORY>"
		print "Ex.: python data.py ../resultados/NIT_0.1K/"
		return
		
	directory=str(sys.argv[1])
	#directory="../resultados/NIT_0.1K/"
	cmdline='/bin/ls -l '+directory+' | grep -v total > /tmp/datainput.dat'
	filelist = commands.getstatusoutput(cmdline)

	
	listofiles="/tmp/datainput.dat"
	filecont=0
	filename = []
	# print "###Filename(1) NA(2) ND(3) NMIG(4) REPL(5) RECFG(6) DEL(7) TAList(8) TAdev(9) \
	# OPList(10) OPdev(11) EngList(12) Engdev(13) SLAList(14) SLAdev(15) StealList(16) Stealdev(17)"	
	# print "Filename(1),EngList(12),Engdev(13),SLAList(14),SLAdev(15),StealList(16),Stealdev(17)"	

	NIT= directory.split("/")
	filenameOutput="/tmp/dataOutput"+NIT[2]+".csv"
	fileoutput=open(filenameOutput,"w")
	fileoutput.write("Filename,NA,TAtotal,ND,NMIG,REPL0,REPL1,RECFG0,RECFG1,DEL0,DEL1,TAList,TAdev,OPList,OPdev,EngList,Engdev,SLAList,SLAdev,StealList,Stealdev\n")
	# fileoutput.write("Filename(1),EngList(12),Engdev(13),SLAList(14),SLAdev(15),StealList(16),Stealdev(17)\n")

	for line in open(listofiles).xreadlines():
		fileresults=line.split()
		filename=fileresults[8]
		filecont=filecont+1
		print ("FILENAME: %s" %(filename))
		extract_columns(directory,filename,fileoutput)

 	fileoutput.close() 
	print ("The /tmp/dataOutput.csv file created.")
main()