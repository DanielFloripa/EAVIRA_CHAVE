#!/usr/bin/env python
# Call this script with "hour" as argument
# Use the file "bash_script" to call this script
import sys

hour = int(sys.argv[1])
    
with open('PATH_TO_REPOSITORY/histogram.txt', 'r') as myfile:
    data = myfile.read()

newdata = data.splitlines()

newdata[hour] = int(newdata[hour]) + 1

tmpstr = str(newdata)
tmpstr = tmpstr.replace("'","")
tmpstr = tmpstr.replace(" ","")
tmpstr = tmpstr.replace(",","\n")
tmpstr = tmpstr.replace("[","");
tmpstr = tmpstr.replace("]","");

with open('PATH_TO_REPOSITORY/histogram.txt', 'w') as myfile:
    myfile.write(tmpstr)

