#!/usr/bin/env python

import os
import sys
import string
from random import randint

if __name__ == '__main__':
	NUM_VIS = 200
	NUM_NODES = [5]
	LINK_BW = [5, 10, 15] #Mbps
	
	config = []
	#medium (vcpu, ram, storage, bw max)
	# config.append([1, 4, 4])
	#large
	config.append([2, 8, 32])
	#xlarge
	# config.append([4, 15, 80])

	for ff in range(0, NUM_VIS):
		vpc = "virtual/vpc-m3/%d.xml.dat" %(ff)
		f = open(vpc, 'w')

		nnodes = NUM_NODES[randint(0, len(NUM_NODES) - 1)]

		out = "%d\n" %(nnodes)
		out_links = "%d\n" %(nnodes - 1)

		out = "%s%d %d %d %d %d\n" %(out, 0, 1, 1, 1, 1)

		for i in range(1, nnodes):
			node_config = randint(0, len(config) - 1)
			out = "%s%d %d %d %d %d\n" %(out, i, config[node_config][0], config[node_config][1], config[node_config][2], 0)
			link_config = randint(0, len(LINK_BW) - 1)
			out_links = "%s%d %d %d\n" %(out_links, 0, i, LINK_BW[link_config])

		f.write(out)
		f.write(out_links)
		f.close()
