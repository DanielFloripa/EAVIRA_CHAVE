#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CHAVE-Sim: The simulator for research based in clouds architecture
    CHAVE: Consolidation with High Availability on virtualyzed environments
"""
from typing import Union
import random
from math import sqrt
import psutil
import numpy as np
import logging
import sqlite3
from collections import OrderedDict
from Users.globalData import *
import os
import time
from Users.SLAHelper import *


def resp(command, key, value=None):
    return "Key {} not found for command {} and val {}!!".format(key, command, value)

class MetricSQLite(object):
    """
    Class Metrics
    All metrics used in CHAVE simulator
    """
    def __init__(self, az_id, logger=None, sla=None):
        if sla is None:
            self.logger = logger
            self.sla = None
            self.db_path = "output/"
        elif logger is None:
            self.logger = sla.logger
            self.sla = sla
            self.db_path = sla.g_data_output()
            self.db_file_default = sla.g_default_file_output()
        else:
            print("ERROR, logger or SLA must be setted!!!")
            exit(1)
        self.__az_id_list = list(az_id)  # One copy
        self.__az_id_list.append('global')
        self.tables = []
        self.connection = dict()
        self.cursor = dict()
        self.is_init = self.init_db()

    def __repr__(self):
        return repr(["is_init:", self.is_init, 'az_id_list', self.__az_id_list, "az_id_list", self.__az_id_list])

    def set(self, az_id, key, value, column=None):
        # Se for uma tabela, e valor for int ou float
        if (isinstance(value, float) or isinstance(value, int)) and column is not None:
            len_value = 1
            self.cursor[az_id].execute(query_insert(len_value).format(key, column), [value])
            return True
        else:
            len_value = len(value)
        # Note: Uma lista de tabelas
        if isinstance(key, list) or isinstance(key, tuple):
            for i, k in enumerate(key):
                if k in all_metrics_l:
                    self.cursor[az_id].execute(query_insert(len_value).format(k, column), [value[i]])
        # Note: uma lista de colunas
        #elif isinstance(column, list) or isinstance(column, tuple):
            #for i, c in column:
                #self.cursor[az_id].execute(query_insert_one.format(key, c), [value[i]])
        # Note: Ou uma lista de valores (mais comum)
        elif isinstance(value, list) or isinstance(value, tuple):
            if key in all_metrics_l[0: len_l]:
                self.cursor[az_id].execute(query_insert(len_value).format(key, columns_l), value)
            elif key in all_metrics_l[len_l: len_l+len_d]:
                self.cursor[az_id].execute(query_insert(len_value).format(key, columns_d), value)
            elif key in k_info:
                self.cursor[az_id].execute(query_insert(len_value).format(key, column), value)
                pass
        else:
            self.logger.error("{} {} {}".format(type(value), type(column), type(key)))
            self.logger.error(resp('set', key, value))
            return False
        self.connection[az_id].commit()
        return True

    def update(self, az_id: str, key: str, column: str, value: any, pk_name: str, pk: int) -> bool:
        if key in all_metrics_l:
            try:
                self.cursor[az_id].execute(query_update.format(key, column, pk_name), (value, pk,))
            except Exception as e:
                self.logger.error("ERROR: {}".format(e))
                return False
        else:
            self.logger.error(resp('update', key, value))
            return False
        self.connection[az_id].commit()
        return True

    def get(self, az_id, key, column=None, gvt=None) -> Union[list, bool]:
        if key in all_metrics_l:
            if column is None:
                column = '*'
            if gvt is not None:
                query = query_select_one.format(column, key)
                self.cursor[az_id].execute(query, [gvt])
            else:
                query = query_select.format(column, key)
                self.logger.debug(query)
                self.cursor[az_id].execute(query)
        else:
            self.logger.error(resp('get', key))
            return False
        return [linha for linha in self.cursor[az_id].fetchall()]

    def add(self, az_id: str, key: str, column: str, value: any, gvt: int) -> bool:
        if key in all_metrics_l[0: len_m]:
            try:
                v = self.get(az_id, key, column=column, gvt=gvt)
                if isinstance(v, tuple) or isinstance(v, list):
                    new_value = v[0][0] + value
                else:
                    new_value = v + value
                self.cursor[az_id].execute(query_update.format(key, column), (new_value, gvt,))
            except Exception as e:
                self.logger.error("ERROR: {}".format(e))
                return False
        else:
            self.logger.error(resp('add', key, value))
            return False
        self.connection[az_id].commit()
        return True

    def incr_1(self, az_id, key, position):
        if key in all_metrics_l[0: len_m]:
            self.add(az_id, key, "gvt", 1, position)
        else:
            self.logger.error(resp('increment', key))
            return False
        return True

    def special(self, az_id, table, column, func):
        if az_id == 'all':
            ret = dict()
            for az in self.__az_id_list:
                v = self.special(az, table, column, func)
                if v is not None and not isinstance(v, bool):
                    ret[az] = v[0][0]
                else:
                    ret[az] = None
            return ret
        if table in all_metrics_l:
            if func in query_special_base.keys():
                try:
                    self.cursor[az_id].execute(query_special.format(query_special_base[func].format(column), table))
                except Exception as e:
                    self.logger.error("ERROR: {}".format(e))
                    return False
                else:
                    return self.cursor[az_id].fetchall()
                    # for linha in self.cursor[az_id].fetchall():
                    #     yield linha
            else:
                self.logger.error("ERROR: Function: {} not in {}".format(func, query_special_base.keys()))
        else:
            self.logger.error(resp('special', table+column, func))
            return False
        return

    def commit_db(self, az_id):
        self.connection[az_id].commit()

    def close_all_dbs(self):
        for az_id in self.__az_id_list:
            self.cursor[az_id].close()
            self.connection[az_id].commit()
            self.connection[az_id].close()

    def init_db(self):
        for az_id in self.__az_id_list:
            db_file = str(self.db_file_default) + "_" + az_id + ".db"
            try:
                os.mkdir(self.db_path)
            except Exception as e:
                self.logger.debug("Can't make dir: {}".format(e))
                pass
            self.logger.debug('Init database: {}'.format(db_file))
            self.connection[az_id] = sqlite3.connect(self.db_path + '/' + db_file)
            # print(self.db_path + '/' + db_file, self.db_file_default)
            for q in query_init:
                # Todo: colocar pra fora connection e commit para testar
                self.cursor[az_id] = self.connection[az_id].cursor()
                try:
                    self.cursor[az_id].execute(q)
                except sqlite3.OperationalError:
                    self.logger.fatal("Error on query {} for {}".format(q, db_file))
                    exit(1)
            self.connection[az_id].commit()

        with open('tables.txt', 'w') as outfile:
            for q in query_init:
                outfile.write(q+'\n')
        return True

    def debug_db(self):
        for az_id in self.__az_id_list:
            self.cursor[az_id].execute(query_list_tables)
            for table in self.cursor[az_id].fetchall():
                self.tables.append(table)
            self.logger.debug('AZ: {}\t Tabelas: {}'.format(az_id, self.tables))
            # obtendo o schema da tabela
            self.cursor[az_id].execute(query_show_schema)
            self.logger.debug('\tSchemas:')
            for schema in self.cursor[az_id].fetchall():
                self.logger.debug("\t\t{}".format(schema))

    def resume_global(self, elapsed):
        for i, key in enumerate(k_lists):
            total = 0
            for az_id in self.__az_id_list:
                total += self.get(az_id, key)
            self.add('global', key, total)
            self.logger.debug("Global metric for {} is {}".format(key, total))

        # self.set('global', 'sla_violations_i', api.get_total_SLA_violations_from_cloud())
        # self.set('global', 'overcommit_i', api.get_list_overcom_amount_from_cloud())
        self.set('global', 'elapsed_time_i', elapsed)
