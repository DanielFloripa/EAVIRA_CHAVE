#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CHAVE-Sim: The simulator for research based in clouds architecture
    CHAVE: Consolidation with High Availability on virtualyzed environments
"""

# Just some global vars
k_lists = ['max_host_on_i',
           'energy_l',
           'az_load_l',
           'lap_time_l',
           'reject_l'
           ]
columns_l = ('gvt', 'val_0', 'info')
len_l = len(k_lists)

k_dicts = ['consol_d',  # OK!
           'replic_d',  # OK!
           'time_steps_d'
           ]
columns_d = ('gvt', 'energy_0', 'energy_f', 'val_0', 'val_f', 'hosts_0', 'hosts_f', 'info')
len_d = len(k_dicts)

k_info = ["basic_info", "vm_history"]
columns_basic_info = ("max_gvt", "nodes", "cores", "noperations", "availabiliy", "trace_dir", "frag_class", "az_select", "trace_class", "ai")  # pk: ai
columns_vm_hist = ("vm_id", "gvt_start", "gvt_end",  "host_place", "vcpu", "vtype", "req_avail", "lock_migr", "lifetime", "migrations", "reject_code")  # pk: vm_id


all_metrics_l = k_lists + k_dicts + k_info
len_m = len(all_metrics_l)

query_pragma = [
    "PRAGMA main.page_size=4096;",
    "PRAGMA main.cache_size=10000;",
    "PRAGMA main.locking_mode=EXCLUSIVE;",
    "PRAGMA main.synchronous=OFF;",
    "PRAGMA main.journal_mode=OFF;",
    "PRAGMA main.locking_mode=EXCLUSIVE;",
    "PRAGMA main.temp_store=MEMORY;",
    "CREATE TABLE {} ({} INTEGER NOT NULL, {} INTEGER NOT NULL, {} INTEGER NOT NULL, {} INTEGER NOT NULL, {} DOUBLE NOT NULL, {} TEXT DEFAULT '', {} TEXT DEFAULT '', {} TEXT DEFAULT '', {} TEXT DEFAULT '', {} INTEGER PRIMARY KEY AUTOINCREMENT);".format(k_info[0], *columns_basic_info),
    "CREATE TABLE {} ({} TEXT NOT NULL PRIMARY KEY, {} INTEGER NOT NULL, {} INTEGER NOT NULL,  {} TEXT, {} INTEGER, {} TEXT DEFAULT 'regular', {} DOUBLE NOT NULL, {} BOOLEAN DEFAULT False, {} INTEGER, {} INTEGER, {} INTEGER DEFAULT -1);".format(k_info[1], *columns_vm_hist)
]

query_create_default = "CREATE TABLE {} (gvt INTEGER NOT NULL, "
query_insert_default = "INSERT INTO {} {} VALUES (".format({}, {})
query_insert_one = "INSERT INTO {} ({}) VALUES (?);".format({}, {})
query_update = "UPDATE {} SET {} = ? WHERE {} = ?;".format({}, {}, {})
query_select = "SELECT {} FROM {};".format({}, {})
query_select_one = "SELECT {} FROM {} WHERE gvt = ?;".format({}, {})
query_delete = "DELETE FROM {} WHERE gvt = ?;".format({})
# DEBUG: listando as tabelas do bd:
query_list_tables = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
query_show_schema = "SELECT sql FROM sqlite_master WHERE type='table';"
# Special functions
query_special_base = {'SUM': 'sum({})', 'AVG': 'avg({})', 'MIN': 'min({})', 'MAX': 'max({})', 'COUNT': 'count(*)'}
query_special = "SELECT {} FROM {};".format({}, {})


def query_insert(len_tuple):
    str1 = '?, '
    it = ''
    for i in range(len_tuple - 1):
        it += str1
    ret = "{}{}?);".format(query_insert_default, it)
    return ret


def query_create(tup):
    len_tuple = len(tup)
    it = ''
    for i in range(len_tuple - 2):
        it += '{} REAL DEFAULT 0, '.format(tup[i+1])
    ret = "{}{}{} TEXT DEFAULT '', ai INTEGER PRIMARY KEY AUTOINCREMENT);".format(query_create_default, it, format(tup[i+2]))
    return ret


query_init = query_pragma + \
             [query_create(columns_l).format(key) for key in k_lists] + \
             [query_create(columns_d).format(key) for key in k_dicts]

"""
import numpy as np
def get_ha_tax(downtime):
    m = 525600.0  # 365 * 24 * 60
    av = 1.0 - float(downtime) / float(m)
    return av


def get_downtime(ha):
    m = 525600.0
    downtime = (1.0 - float(ha)) * float(m)
    return downtime


# Valido apenas quando todas as AZs possuem a mesma taxa A
def get_required_replicas(a, ha=None, downtime=None):
    if ha is None:
        ha = 0.99999
    if downtime is not None:
        ha = get_ha_tax(downtime)
    else:
        downtime = get_downtime(ha)

    logA = np.log10(1.0 - a)
    logHA = np.log10(1.0 - ha)
    r = float(float(logHA) / float(logA)) - 1.0
    replicas = np.ceil(r)
    #print("For {} mins of Downtime is required {}% and {} replicas (A:{} H:{})\n la:{} lha:{} r:{}".format(downtime, (ha * 100), replicas, a, ha,logA, logHA, r))
    return int(replicas)

get_required_replicas(0.999, 0,9999995)  # 999999999  x=1-(1-0.999)**3
"""