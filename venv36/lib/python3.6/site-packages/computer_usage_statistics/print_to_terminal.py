#!/usr/bin/env python
    
with open('PATH_TO_REPOSITORY/histogram.txt', 'r') as myfile:
    data = myfile.read()

splitted_data = data.splitlines()

print "HOUR\tCOUNT"
for idx, data in enumerate(splitted_data):
    print str(idx) + "\t" + str(data)
