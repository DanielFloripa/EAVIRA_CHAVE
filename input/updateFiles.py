#!/usr/bin/env python

import os
import sys
import string
from random import randint

def update_physical():
	for fname in os.listdir('physical/'):
		f = open('physical/'+fname)
		out = ""
		for line in f:
			s = line
			l = line.split()
			
			if len(l) == 5:
				s = "%s %s %s %s %s\n" % (l[0], 24, 256, 1024, l[4])
			elif len(l) == 3:
				s = "%s %s %s\n" % (l[0], l[1], 1000)
			out = "%s%s" % (out, s)
		f.close()
		f = open('physical/'+fname, 'w')
		f.write(out)
		f.close()

if __name__ == '__main__':
	for folder in os.listdir('virtual/'):
		for fname in os.listdir('virtual/'+folder):
			f = open('virtual/'+folder+'/'+fname)
			out = ""
			for line in f:
				s = line
				l = line.split()
				
				if len(l) == 5:
					cpu = randint(1, 4)
					ram = [1,2,4,8,16,32][randint(0,5)]
					storage = [8,16,32,64,128][randint(0,4)]
					s = "%s %s %s %s %s\n" % (l[0], cpu, ram, storage, l[4])
				elif len(l) == 3:
					bw = randint(1, 10)
					s = "%s %s %s\n" % (l[0], l[1], bw)
				out = "%s%s" % (out, s)
			f.close()
			f = open('virtual/'+folder+'/'+fname, 'w')
			f.write(out)
			f.close()
