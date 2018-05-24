#!/usr/bin/env python 

import pandas as pd
import json
files=['18.05.24_13.01.49_CHAVE_PlacementFirst_FFD2I_1_20_False_False.json',
	   '18.05.24_13.01.49_CHAVE_PlacementFirst_FFD2I_1_20_False_True.json',
	   '18.05.24_13.01.49_CHAVE_PlacementFirst_FFD2I_1_20_True_False.json',
	   '18.05.24_13.01.49_CHAVE_PlacementFirst_FFD2I_1_20_True_True.json']

key = ['consolidation_l', 'replication_l', 'overcommitting_l']
for f in files:
	print f
	with open(f) as train_file:
		dict_train = json.load(train_file)

	train = pd.DataFrame.from_dict(dict_train, orient='index')

	for k in key:
		print k
		train[k].to_csv(k+str('.csv'))
		for i in range(len(train[k])):  # azs 0-7
			print train[k][i]
			with open(k + "_"+train[k].keys()[i]+f+'.txt', "w") as fp:
				for j in range(len(train[k][i])):  # ops
					for kd, vd in train[k][i][j].items():  # internal_keys
						line = "{} \t {}\n".format(kd, vd)
						fp.write(line)
					fp.write("\n")

