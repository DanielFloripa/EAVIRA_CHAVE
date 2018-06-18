#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CHAVE-Sim: The simulator for research based in clouds architecture
    CHAVE: Consolidation with High Availability on virtualyzed environments
"""
from shelve import DbfilenameShelf, Shelf
import shelve
from copy import deepcopy
import random
from math import sqrt
from numpy import std, mean
import numpy as np
import logging
from collections import OrderedDict

from src.Users.globalData import *


def resp(command, key, value=None):
    return "Key {} not found for command {} and val {}!!".format(key, command, value)


cache_file = '/tmp/__metrics_dict'


class MetricsDB(object):
    def __init__(self, az_id, sla):
        self.sla = sla
        self.logger = sla.logger
        self.__az_id_list = az_id
        self.is_init = self.init_dict(is_print=False)

    def set(self, az_id, key, value=None):
        __metrics_dict = shelve.open(cache_file, writeback=True)
        if key in all_metrics_l[0: len_v]:
            __metrics_dict[az_id][key] = value
        elif key in all_metrics_l[len_v: len_m]:
            m_list = __metrics_dict[az_id][key]
            m_list.append(value)
            __metrics_dict[az_id][key] = m_list
        else:
            self.logger.error(resp('set', key, value))
            __metrics_dict.close()
            return False
        __metrics_dict.close()
        return True

    def get(self, az_id, key):
        __metrics_dict = shelve.open(cache_file, writeback=True)
        if key in all_metrics_l:
            m_list = __metrics_dict[az_id][key]  # Shelf
            __metrics_dict.close()
            return m_list
        else:
            self.logger.error(resp('get', key))
            __metrics_dict.close()
            return False

    def add(self, az_id, key, value, position=-1):
        __metrics_dict = shelve.open(cache_file, writeback=True)
        if key in all_metrics_l[0: len_v]:
            __metrics_dict[az_id][key] = self.get(az_id, key) + value
        elif key in all_metrics_l[len_v: len_m]:
            if position >= 0:
                v = __metrics_dict[az_id][key][position]
                v += value
                __metrics_dict[az_id][key][position] = v
            else:
                self.logger.error("Use 'set' command or specify the 'n' in list position")
                return False
        else:
            self.logger.error(resp('add', key, value))
            return False
        __metrics_dict.close()
        return True

    def increment_one(self, az_id, key, n=-1):
        ret = True
        __metrics_dict = shelve.open(cache_file, writeback=True)
        if key in all_metrics_l[0: len_v]:
            __metrics_dict[az_id][key] = __metrics_dict[az_id][key] + 1
        elif key in all_metrics_l[len_v: len_m]:
            if n >= 0:
                __metrics_dict[az_id][key][n] += 1
            else:
                self.logger.error("Use 'set' command or specify the 'n' in list position")
                ret = False
        else:
            self.logger.error(resp('increment', key))
            ret = False
        __metrics_dict.close()
        return ret

    def sum(self, az_id, key, value=None):
        ret = True
        __metrics_dict = shelve.open(cache_file, writeback=True)
        if key in all_metrics_l[0: len_v]:
            self.logger.error("This is only for list. Use 'get' command instead!")
            ret = False
        elif key in all_metrics_l[len_v: len_m]:
            ret = sum(values for values in __metrics_dict[az_id][key])
        else:
            self.logger.error(resp('sum', key, value))
            ret = False
        __metrics_dict.close()
        return ret

    def avg(self, az_id, key):
        ret = 0
        __metrics_dict = shelve.open(cache_file, writeback=True)
        if key in all_metrics_l[0: len_v]:
            self.logger.error("This is only for list. Use 'get' command instead!")
            ret = 0
        elif key in all_metrics_l[len_v: len_m]:
            sum_avg = 0
            for values in __metrics_dict[az_id][key]:
                if isinstance(sum_avg, list) or isinstance(values, list):
                    self.logger.error("ERROR on key:{} DIFFERENT TYPES sumavg{}-> {}, val{}-> {}".format(
                        key, type(sum_avg), sum_avg, type(values), values))
                    # exit(1)
                    raise TypeError
                sum_avg += values
            len_avg = float(len(__metrics_dict[az_id][key]))
            if len_avg == 0:
                ret = 0
            ret = sum_avg / len_avg
        else:
            self.logger.error(resp('avg', key))
            __metrics_dict.close()
            return ret

    def init_dict(self, is_print=False):
        __metrics_dict = shelve.open(cache_file, writeback=True)
        temp_az_list = list(self.__az_id_list)
        temp_az_list.append('global')
        for az_id in temp_az_list:
            __metrics_dict[az_id] = OrderedDict()
            for i, k in enumerate(all_metrics_l):
                if i < len_v:
                    __metrics_dict[az_id][k] = 0
                else:
                    __metrics_dict[az_id][k] = []
        # self.logger.info("Metrics Initialized! %s" % __metrics_dict.items())
        if is_print:
            for az_id, key in __metrics_dict.items():
                print('\n\n', az_id, )
                for k, value in key.viewitems():
                    print('\n\t', k, '\n\t\t', value)
        # Done!
        __metrics_dict.close()
        return True
