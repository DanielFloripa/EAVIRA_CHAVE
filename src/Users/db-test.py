import sqlite3
# import random number generator
from numpy.random import uniform
import time
import os
import logging
logging.basicConfig(level=logging.DEBUG, format='(%(levelname)s %(funcName)s) --> %(message)s')
from Users.MetricSQLite import *

random_numbers = uniform(low=10.0, high=25.0, size=100)

start1 = time.time()
az_id_l = ['az1', 'az2', 'az3']
metric = MetricSQLite(az_id_l, logger=logging)

with open('tables.txt', 'w') as outfile:
    for q in query_init:
        outfile.write(q)


obj = len(random_numbers) / 10
for i, number in enumerate(random_numbers):
    metric.set('az1', 'total_energy_f', (i, number, 'asd'))
    if i % obj == 0:
        metric.commit_db('az1')
metric.commit_db('az1')
final1 = time.time() - start1

logging.debug(metric.set('az3', 'max_host_on_i', (10, 100.9, 'asd10')))
logging.debug(metric.set('az2', 'max_host_on_i', (9, 900.9, 'asd9')))
logging.debug(metric.set('az2', 'max_host_on_i', (11, 111.9, 'asd11')))
logging.debug(metric.set('az2', 'elapsed_time_i', (88, 888.8, 'asd6')))
metric.commit_db('az3')
metric.commit_db('az2')
x = metric.get('az3', 'max_host_on_i', column='val_0')
for e in x:
    logging.debug("R1:{}".format(e))

y = metric.get('az2', 'elapsed_time_i')
for e in y:
    logging.debug("R2:{}".format(e))

z = metric.get('az1', 'total_energy_f', gvt=10)
for e in z:
    logging.debug("R3:{}".format(e))

k = metric.get('az1', 'total_energy_f', column='val_0', gvt=10)
for e in k:
    logging.debug("R4:{}".format(e))

logging.debug(metric.add('az2', 'elapsed_time_i', 'val_0', 112, 88))
y = metric.get('az2', 'elapsed_time_i')
for e in y:
    logging.debug("R5:{}".format(e))

logging.debug(metric.update('az2', 'elapsed_time_i', 'val_0', 112, 88))
y = metric.get('az2', 'elapsed_time_i')
for e in y:
    logging.debug("R6:{}".format(e))


metric.cursor['az1'].close()
metric.connection['az1'].commit()
metric.connection['az1'].close()


start2 = time.time()
with open('original.txt', 'w') as outfile:
    for number in random_numbers:
        outfile.write("{}\n".format(number))
final2 = time.time() - start2


logging.debug("db:{}, file:{}".format(final1, final2))

