#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CHAVE-Sim: The simulator for research based in clouds architecture
    CHAVE: Consolidation with High Availability on virtualyzed environments
"""

# Just some global vars
k_values = ['max_host_on_i',
            'sla_violations_i',
            'elapsed_time_i'
            ]
columns_v = ('gvt', 'val_0', 'info')
columns_v_dict = {columns_v[0]: 0, columns_v[1]: 0, columns_v[2]: ''}
len_v = len(k_values)

k_lists = ['energy_l',
           'az_load_l',
           'lap_time_l',  # OK!
           'overc_l',
           'reject_l'
           ]
columns_l = ('gvt', 'val_0', 'info')
columns_l_dict = {columns_l[0]: 0, columns_l[1]: 0, columns_l[2]: ''}
len_l = len(k_lists)

k_dicts = ['migra_d',
           'consol_d',  # OK!
           'replic_d',  # OK!
           ]
columns_d = ('gvt', 'energy_0', 'energy_f', 'val_0', 'val_f', 'info')
columns_d_dict = {columns_d[0]: 0, columns_d[1]: 0, columns_d[2]: 0, columns_d[3]: 0, columns_d[4]: 0, columns_d[5]: ''}
len_d = len(k_dicts)

all_metrics_l = k_values + k_lists + k_dicts
columns_m_dict = dict(columns_v_dict); columns_m_dict.update(columns_l_dict); columns_m_dict.update(columns_d_dict)
len_m = len(all_metrics_l)


def query_insert(len_tuple):
    str1 = '?, '
    it = ''
    for i in range(len_tuple - 1):
        it += str1
    ret = query_insert_default + it + '?);'
    return ret


def resp(command, key, value=None):
    return "Key {} not found for command {} and val {}!!".format(key, command, value)


query_create_default = "CREATE TABLE {} (gvt INTEGER NOT NULL, "  # UNIQUE
def query_create(tup):
    len_tuple = len(tup)
    it = ''
    for i in range(len_tuple - 2):
        it += '{} REAL DEFAULT 0.0, '.format(tup[i+1])
    ret = query_create_default + it + '{} TEXT DEFAULT "", ai INTEGER PRIMARY KEY AUTOINCREMENT);'.format(format(tup[i+2]))
    return ret


query_pragma = [
    "PRAGMA main.page_size=4096;",
    "PRAGMA main.cache_size=10000;",
    "PRAGMA main.locking_mode=EXCLUSIVE;",
    "PRAGMA main.synchronous=OFF;",
    "PRAGMA main.journal_mode=OFF;",
    "PRAGMA main.locking_mode=EXCLUSIVE;",
    "PRAGMA main.temp_store=MEMORY;"]

query_init = query_pragma + \
             [query_create(columns_v).format(key) for key in k_values] + \
             [query_create(columns_l).format(key) for key in k_lists] + \
             [query_create(columns_d).format(key) for key in k_dicts]


query_insert_default = "INSERT INTO {} {} VALUES ("
query_insert_old = "INSERT INTO {} ({}) VALUES (?, ?, ?);"
query_insert_one = "INSERT INTO {} ({}) VALUES (?);"
query_update = "UPDATE {} SET {} = ? WHERE gvt = ?;"
query_select = "SELECT {} FROM {};"
query_select_one = "SELECT {} FROM {} WHERE gvt = ?;"
query_delete = "DELETE FROM {} WHERE gvt = ?;"
# DEBUG: listando as tabelas do bd:
query_list_tables = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
query_show_schema = "SELECT sql FROM sqlite_master WHERE type='table';"
# Special functions
query_special_base = {'SUM': 'sum({})', 'AVG': 'avg({})', 'MIN': 'min({})', 'MAX': 'max({})', 'COUNT': 'count(*)'}
query_special = "SELECT {} FROM {};"

"""
with sqlite3.connect("metrics2.db") as conn:
    conn.text_factory = str
    cur = conn.cursor()
    c = cur.execute("SELECT * from az_id WHERE name=?;", ["AZ2"])
    results = cur.fetchall()
    print(results[0][0])  
"""


