import sqlite3
# import random number generator
from numpy.random import uniform
import time
import os

query_select = "SELECT * FROM {};"
query_insert = "INSERT INTO {} ({}) VALUES (?);"

# Just some global vars
k_values = ['max_host_on_i', 'total_energy_f', 'sla_violations_i', 'elapsed_time_i',
            'allocate_i', 'deallocate_i', 'reject_i', 'accept_i', 'migration_i', 'consolidation_i',
            'replication_i', 'overcommit_i', 'placement_i', 'elapsed_time_i', 'max_elapsed_internal_l', 'energy_mon_total', 'MaxValues']

k_lists = ['energy_l', 'energy_acum_l', 'az_load_l', 'hosts_load_l', 'accept_l', 'reject_l', 'lap_time_d']

k_dicts = ['migration_d', 'consolidation_d', 'replication_d', 'overcommit_d', 'placement_d']

all_metrics_l = k_values + k_lists + k_dicts
len_m = len(all_metrics_l)
len_v = len(k_values)
query_list = [
    "PRAGMA main.page_size=4096;",
    "PRAGMA main.cache_size=10000;",
    "PRAGMA main.locking_mode=EXCLUSIVE;",
    "PRAGMA main.synchronous=OFF;",
    "PRAGMA main.journal_mode=OFF;",
    "PRAGMA main.locking_mode=EXCLUSIVE;",
    "PRAGMA main.temp_store=FILE;",
    "CREATE TABLE MaxValues (max_host_on_i INTEGER DEFAULT 0, total_energy_f REAL DEFAULT 0, " +
    "sla_violations_i INTEGER DEFAULT 0, elapsed_time_i INTEGER DEFAULT 0, allocate_i INTEGER DEFAULT 0, " +
    "deallocate_i INTEGER DEFAULT 0, reject_i INTEGER DEFAULT 0, accept_i INTEGER DEFAULT 0," +
    "migration_i INTEGER DEFAULT 0, consolidation_i INTEGER DEFAULT 0, replication_i INTEGER DEFAULT 0, " +
    "overcommit_i INTEGER DEFAULT 0, placement_i INTEGER DEFAULT 0, max_elapsed_internal_l INTEGER DEFAULT 0);",
    "CREATE TABLE energy_l (gvt INTEGER NOT NULL UNIQUE, az_id INTEGER NOT NULL, PRIMARY KEY(gvt));",
    "CREATE TABLE Pressure (reading float not null);"
]


def set(az_id, key, value):
    if key in all_metrics_l[0: len_v]:
        keydb = 'MaxValues'
        cursor[az_id].execute(query_insert.format(keydb, key), [value])
    #elif key in all_metrics_l[len_v: len_m]:
    #    cursor[az_id].execute(query_insert.format(key), value)
    else:
        print("error resp get  key")
        return False
    return True


def get(az_id, key):
    if key in all_metrics_l:
        cursor[az_id] = connection.cursor()
        cursor[az_id].execute(query_select.format(key))
        for linha in cursor[az_id].fetchall():
            yield linha
    else:
        print("error resp get  key")
        return False


random_numbers = uniform(low=10.0, high=25.0, size=1000)
dbfile = "original.db"
try:
    os.remove(dbfile)
except FileNotFoundError:
    pass

start0 = time.time()
connection = sqlite3.connect(dbfile)

cursor = dict()

for q in query_list:
    #print(q)
    cursor['az1'] = connection.cursor()
    cursor['az1'].execute(q)
    cursor['az1'].close()

connection.commit()
final0 = time.time() - start0

query = "INSERT INTO Pressure values (?);"

start1 = time.time()
cursor['az1'] = connection.cursor()
obj = len(random_numbers) / 10
for i, number in enumerate(random_numbers):
    cursor['az1'].execute(query, [number])
    if i % obj == 0:
        connection.commit()

set('az1', ['max_host_on_i', 'sla_violations_i'], [336598, 98])
x = get('az1', 'MaxValues')
for e in x:
    print("::", e)

cursor['az1'].close()
# save changes to file for next exercise
connection.commit()
connection.close()
final1 = time.time() - start1

start2 = time.time()
with open('original.txt', 'w') as outfile:
    for number in random_numbers:
        # need to add linebreak \n
        outfile.write("{}\n".format(number))
final2 = time.time() - start2


print("Init:{}, db:{}, file:{}".format(final0, final1, final2))
