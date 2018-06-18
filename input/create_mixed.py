import os
import random

if __name__ == '__main__':
	os.system('rm ./virtual/mixed/*')
	for i in range(100):
		r = random.random()
		if r <= 0.33:
			cdir = './virtual/ft/'
		elif r > 0.33 and r <= 0.66:
			cdir = './virtual/vpc/'
		else:
			cdir = './virtual/nlayers/'
		
		files = os.listdir(cdir)
		chosen_cfg = files[random.randint(0, len(files)-1)]

		cmd =  'cp %s %s' % (cdir+chosen_cfg, './virtual/mixed/'+str(i)+'.xml.dat')
		print(cmd)
		os.system(cmd)
