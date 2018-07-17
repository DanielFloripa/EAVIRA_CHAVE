#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CHAVE-Sim: The simulator for research based in clouds architecture
    CHAVE: Consolidation with High Availability on virtualyzed environments
"""

import psutil
from copy import deepcopy
import random
from math import sqrt
from numpy import std, mean
import numpy as np
import logging
from collections import OrderedDict
from Users.globalData import *
from Users.MetricSQLite import *

# VMs:
CRITICAL = 'critical'
REPLICA = 'replica'
REGULAR = 'regular'
S_MIGRATING = 'migrating'
S_ALLOCATED = 'allocated'
S_DEALLOCATED = 'deallocated'
NODE = "NODE"
# Hosts
HOST_ON = True
HOST_OFF = False
# Files
K_SEP = '_'
F_SEP = '-'
# Consolidation
TIGHT = 'TIGHT'
MEDIUM = 'MEDIUM'
WIDE = 'WIDE'


class SLAHelper(object):
    """
    Class SLAHelper contains all parameters used along the simulation
    Also contains some Helpers methods
    """
    fragmentation_class_dict = {TIGHT: 1.0, MEDIUM: 1.5, WIDE: 2.0}

    @staticmethod
    def get_required_ha(replicas, av_azs):
        prod = 1.0
        if type(av_azs) is list:
            if replicas == 1:
                return av_azs[0]
            for i in range(0, replicas):
                prod = prod * float(1.0 - av_azs[i])
                # print av_azs[i], i, prod
            ha = 1.0 - prod
            return ha
        elif type(av_azs) is float:
            if replicas == 1:
                return av_azs
            ha = 1.0 - np.power((1.0 - float(av_azs)), replicas)
            return ha
        return False

    @staticmethod
    def truncate(tax):
        n = str(tax).count("9")
        quick_trunc = str(tax).split(".")[:n]  # np.round(tax, n)
        if quick_trunc == 1.0:
            truncating = quick_trunc
            while truncating == 1.0:
                n += 1
                truncating = str(tax)[:n]  # np.round(tax, n)
            return truncating
        return quick_trunc

    @staticmethod
    def get_ha_tax(downtime):
        m = 525600.0  # 365 * 24 * 60
        av = 1.0 - float(downtime) / float(m)
        return av

    @staticmethod
    def get_downtime(ha):
        m = 525600.0
        downtime = (1.0 - float(ha)) * float(m)
        return downtime

    # Valido apenas quando todas as AZs possuem a mesma taxa A
    def get_required_replicas(self, a, ha=None, downtime=None):
        if ha is None:
            ha = 0.99999
        if downtime is not None:
            ha = self.get_ha_tax(downtime)
        else:
            downtime = self.get_downtime(ha)

        logA = np.log10(1.0 - a)
        logHA = np.log10(1.0 - ha)
        r = float(float(logHA) / float(logA)) - 1.0
        replicas = np.ceil(r)
        #print("For {} mins of Downtime is required {}% and {} replicas (A:{} H:{})".format(downtime, (ha * 100), replicas, a, ha))
        return int(replicas)

    @staticmethod
    def key_from_item(func):
        return lambda item: func(*item)

    @staticmethod
    def print_dic(raw_dict):
        ret_str = ''
        if not isinstance(raw_dict, dict) and not isinstance(raw_dict, OrderedDict):
            raise TypeError("Problem on type for raw_dict, is: {}".format(type(raw_dict)))
        for k1, v1 in raw_dict.items():
            ret_str += '\n'+k1+': '
            if isinstance(v1, dict) or isinstance(v1, OrderedDict):
                for k2, v2 in v1.items():
                    ret_str += '\n\t' + k2 + ': '
                    if isinstance(v2, dict) or isinstance(v2, OrderedDict):
                        for k3, v3 in v2.items():
                            ret_str += '\n\t\t' + k3 + ': ' + str(v3)
                    else:
                        ret_str += str(v2)
            else:
                ret_str += str(v1)
            ret_str += '\n'
        return ret_str

    def p_list(self, raw_list, rec=0):
        s, tab = '', ''
        for i in range(rec):
            tab += '\t'
        if not isinstance(raw_list, list):
            raise TypeError("Input is not a list, but: ".format(type(raw_list)))
        for l in raw_list:
            if isinstance(l, list):
                rec += 1
                s += tab + self.p_list(l, rec) + '\n'
            else:
                s += tab + str(l) + '\n'
                rec = 0
        return s

    @staticmethod
    def is_required_ha(av_vm, av_az):
        if av_vm > av_az:
            return True
        return False

    @staticmethod
    def monte_carlo():
        """
        Monte Carlo de Erro-Não-Limitado
        https://en.wikipedia.org/wiki/Monte_Carlo_method
        uniformly distributed: np.random.rand() Create an array of the given shape and populate it with
            random samples from a uniform distribution over ``[0, 1)``.
        number of points = nops
        :return:
        """
        radius = 1
        dimmensions = 2
        r = np.random.rand(dimmensions)
        # Funcao que retorna +-21% de probabilidade
        # Equivale a 1/4 da área externa de um circulo dentro de um quadrado de lado = diametro
        if (r[0] ** 2) + (r[1] ** 2) >= radius:
            return True
        return False

    @staticmethod
    def my_std(data):
        u = mean(data)
        std = sqrt(1.0 / (len(data) - 1) * sum([(e - u) ** 2 for e in data]))
        return 1.96 * std / sqrt(len(data))

    @staticmethod
    def mean(data):
        return sum(data) / float(len(data))

    def __init__(self):
        # vars
        self.__sla_is_locked = False
        self.__has_overcommitting = False  # bool
        self.__consolidation = False  # bool
        self.__enable_emon = False  # bool
        self.__enable_replication = False  # bool
        self.__window_time = 1  # int
        self.__number_of_azs = 6  # int
        self.__number_of_milestones = 10  # int
        self.__lock_case = ""  # str
        self.__consolidation_alg = ""  # str()
        self.__ff = ""  # str()
        self.__algorithm = ""  # str()
        # vars from environment
        self.__source = ""
        self.__max_az_per_region = ""  # str()
        self.__date = ""  # str()
        self.__core_2_ram_default = ""  # str()
        self.__data_output = ""  # str()
        self.__log_output = ""  # str()
        self.__default_file_output = ""
        self.__trigger_to_migrate = ""  # str()
        self.__frag_class = ""  # str()
        self.__vcpu_per_core = ""  # str()
        self.__output_type = list()
        self.__out_sep = ""
        self.__az_selection = ""  # str()
        self.__trace_class = ""  # str()
        self.__energy_model_src = ""
        # Note: deprecated
        self.__avg_load_objective_file = ""
        # lists
        self.__ha_input = []
        self.__az_nodes = []
        self.__az_cores = []
        self.__az_conf = []
        self.__nit = []
        self.__list_of_source_files = []
        self.__az_id_list = []
        self.auto_az_id_parse = []
        # dicts
        self.__az_dict = dict()
        self.__avg_load_objective = dict()  # dict az: floats
        # objects
        self.logger = logging
        self.metrics = object  # Metrics(self.__az_id_list, self)
        self.__doc = ""

    def init_metrics(self):
        self.metrics = MetricSQLite(self.__az_id_list, sla=self)

    def debug_sla(self):
        self.logger.critical("\nDateTime:\t {}\nOrder Mode:\t {}\nMain Algo:\t {}\nConsol Alg:\t {}\nConsolida?:\t {}"
                             "\nOvercomm?:\t {}\nEnergyMon?:\t {}\nReplicate?:\t {}\nAZConf OK?:\t {}\nVM Locked?:\t {}"
                             "\nWindowTime:\t {}\nNumb AZs:\t {}\nMaxAZs/Reg:\t {}\nCore2Ram:\t {}\nTrigger:\t {}"
                             "\nResultType:\t {}\nFrag Class:\t {}\nAZ Select:\t {}\nTraceClass:\t {}\nAZ Nodes:\t {}"
                             "\nAZ Cores:\t {}\nN. Operat.:\t {}\nAZ Identif:\t {}\nTraceFoldr:\t {}\nDataOutput:\t {}\n"
                             "Log Output:\t {}\nSourcesF.:\t {}\nHAInput:\t {}\nAZ Dictionary:\t {}\nMetrics:\t {}\n"
                             "LoggerObj:\t {}\nSLA locked?:\t {}\n".format(  # self.p_list(self.__doc),
            self.__date, self.__ff, self.__algorithm, self.__consolidation_alg, self.__consolidation,
            self.__has_overcommitting, self.__enable_emon, self.__enable_replication, self.__az_conf, self.__lock_case,
            self.__window_time, self.__number_of_azs, self.__max_az_per_region,  self.__core_2_ram_default,
            self.__trigger_to_migrate, self.__output_type, self.__frag_class, self.__az_selection, self.__trace_class,
            self.__az_nodes, self.__az_cores, self.__nit, self.__az_id_list, self.__source,
            self.__data_output, self.__log_output, self.__list_of_source_files, self.__ha_input,
            self.print_dic(self.__az_dict), self.metrics.__doc__, self.logger, self.__sla_is_locked))

    def __repr__(self):
        return repr([self.__consolidation_alg, self.__ff, self.__algorithm, self.__source, self.__has_overcommitting,
                     self.__consolidation, self.__enable_emon, self.__enable_replication, self.__window_time, self.__lock_case,
                     self.__number_of_azs, self.__max_az_per_region, self.__date, self.__core_2_ram_default,
                     self.__data_output, self.__log_output, self.__trigger_to_migrate, self.__output_type,
                     self.__frag_class, self.__az_selection, self.__trace_class, self.__ha_input, self.__az_nodes,
                     self.__az_cores, self.__az_conf, self.__nit, self.__list_of_source_files, self.__az_id_list,
                     self.__az_dict, self.metrics, self.logger, self.__sla_is_locked])

    def obj_id(self):  # Return the unique hexadecimal footprint from each object
        return str(self).split(' ')[3].split('>')[0]

    def define_az_id(self, mode):
        if self.is_sla_lock():
            return False
        if len(self.__ha_input) != len(self.__az_nodes) != len(self.__az_cores) != len(self.__nit):
            self.logger.error("Len diff: ", len(self.__ha_input), len(self.__az_nodes), len(self.__az_cores),
                              len(self.__nit))

        for i, source in enumerate(self.__list_of_source_files):
            ns = str(source).rfind("/")
            ne = str(source).rfind(F_SEP)
            if mode == "FILE":
                id = str(source[ns + 1: ne])
            elif mode == "AUTO":
                id = "AZ" + str(i)
                self.auto_az_id_parse.append({"AUTO": id, "FILE": str(source[ns + 1: ne])})
            else:
                self.logger.error("Error in value: {}. Must be FILE or AUTO ".format(mode))
            self.__az_id_list.append(id)
            self.__az_dict[id] = {'source_files': source,
                                  'ha_source_files': self.__ha_input[i],
                                  'az_nodes': int(self.__az_nodes[i]),
                                  'az_cores': int(self.__az_cores[i]),
                                  'az_ram': (int(self.__core_2_ram_default) * int(self.__az_cores[i])),
                                  'az_nit': int(self.__nit[i])}
        return True

    def set_conf(self, raw_data, conf):
        if self.is_sla_lock():
            return False
        out = []
        i = 0
        while i < len(raw_data):
            if conf is 'az_conf':
                self.__az_nodes.append(int(raw_data[i]))  # node
                self.__az_cores.append(int(raw_data[i + 1]))  # core
                i = i + 2
                out = True
            if conf is 'nit':
                self.__nit.append(int(raw_data[i]))  # nit
                out.append(int(raw_data[i]))
                i = i + 1
        if type(raw_data) is str:
            out = int(raw_data)
        return out

    def set_test_mode(self):
        #self.log_output(str(eval(os.environ["CS_LOG_OUTPUT"])))
        #self.data_output(str(eval(os.environ["CS_DATA_OUTPUT"])))
        #self.default_file_output(str(eval("\"" + os.environ["CS_DEF_FILE"])))
        self.set_logger(print)
        self.max_az_per_region(int(os.environ["CS_MAX_AZ_REGION"]))
        self.source_folder(str(os.environ.get("CS_SOURCE_FOLDER")))
        self.core_2_ram_default(int(os.environ.get('CS_CORE2RAM')))
        self.output_type(str(os.environ["CS_OUTPUT_TYPE"]), str(os.environ["CS_OUTPUT_SEPARATOR"]))
        self.trace_class(str(os.environ["CS_TRACE_CLASS"]))
        self.enable_emon(eval(os.environ["CS_ENABLE_EMON"]))
        self.az_selection(str(os.environ["CS_AZ_SELECTION"]))
        self.trigger_to_migrate(int(os.environ.get('CS_TRIGGER_MIGRATE')))
        self.frag_class(str(os.environ.get('CS_FRAGMENTATION_CLASS')))
        self.vcpu_per_core(float(os.environ.get('CS_VCPUS_PER_CORE')))
        self.define_az_id(str(os.environ.get("CS_DEFINE_AZID")))
        self.energy_model_src(str(os.environ.get("CS_ENERGY_MODEL")))
        self.milestones(int(os.environ.get("CS_MILESTONES")))
        # self.doc(doc)
        """From now, we can't change this SLA parameters"""
        self.init_metrics()
        self.set_sla_lock(True)
        self.debug_sla()

    def is_sla_lock(self):
        if self.__sla_is_locked:
            res = "The SLA Object is locked, please, re-run the simulator with desired parameters"
            self.logger.error(res)
            return True
        return False

    def set_sla_lock(self, state):
        if type(state) is bool:
            self.__sla_is_locked = state
            self.logger.info("SLA sate is locked? R: {}".format(state))
            return True
        else:
            self.logger.info("State must be a bool type: True | False")
            return False

    # SETTERS:

    def consolidation_alg(self, consolidation_alg):
        if self.is_sla_lock():
            return False
        self.__consolidation_alg = consolidation_alg  # str()
        return True

    def ff(self, ff):
        if self.is_sla_lock():
            return False
        self.__ff = ff
        return True

    def doc(self, doc):
        if self.is_sla_lock():
            return False
        self.__doc = doc
        return True

    def algorithm(self, algorithm):
        if self.is_sla_lock():
            return False
        self.__algorithm = algorithm
        if algorithm == "TEST":
            self.set_test_mode()
        return True

    def source_folder(self, source):
        if self.is_sla_lock():
            return False
        self.__source = source
        return True

    def has_overcommitting(self, has_overcommitting):
        if self.is_sla_lock():
            return False
        self.__has_overcommitting = has_overcommitting
        return True

    def has_consolidation(self, consolidation):
        if self.is_sla_lock():
            return False
        self.__consolidation = consolidation
        return True

    def enable_emon(self, enable_emon):
        if self.is_sla_lock():
            return False
        self.__enable_emon = enable_emon
        return True

    def enable_replication(self, enable_replication):
        if self.is_sla_lock():
            return False
        self.__enable_replication = enable_replication
        return True

    def window_time(self, window_time):
        if self.is_sla_lock():
            return False
        self.__window_time = window_time
        return True

    def lock_case(self, lock_case):
        if self.is_sla_lock():
            return False
        self.__lock_case = lock_case
        return True

    def number_of_azs(self, number_of_azs):
        if self.is_sla_lock():
            return False
        self.__number_of_azs = number_of_azs
        return True

    def max_az_per_region(self, max_az_per_region):
        if self.is_sla_lock():
            return False
        self.__max_az_per_region = max_az_per_region
        return True

    def date(self, date):
        if self.is_sla_lock():
            return False
        self.__date = date
        return True

    def core_2_ram_default(self, core_2_ram_default):
        if self.is_sla_lock():
            return False
        if core_2_ram_default == 0 or core_2_ram_default == "" or core_2_ram_default is None:
            core_2_ram_default = 4
        self.__core_2_ram_default = core_2_ram_default
        return True

    def data_output(self, data_output):
        if self.is_sla_lock():
            return False
        self.__data_output = data_output
        return True

    def log_output(self, log_output):
        if self.is_sla_lock():
            return False
        self.__log_output = log_output
        return True

    def default_file_output(self, default_file_output):  # CS_DEF_FILE
        if self.is_sla_lock():
            return False
        self.__default_file_output = default_file_output
        return True

    def trigger_to_migrate(self, trigger_to_migrate):
        if self.is_sla_lock():
            return False
        self.__trigger_to_migrate = trigger_to_migrate
        return True

    def frag_class(self, frag_class):
        if self.is_sla_lock():
            return False
        self.__frag_class = frag_class
        return True

    def vcpu_per_core(self, vcpu_per_core):
        if self.is_sla_lock():
            return False
        self.__vcpu_per_core = vcpu_per_core
        return True

    def ha_input(self, ha_input):
        if self.is_sla_lock():
            return False
        self.__ha_input = ha_input
        return True

    def az_conf(self, az_conf):
        if self.is_sla_lock():
            return False
        self.__az_conf = az_conf
        return True

    def nit(self, nit):
        if self.is_sla_lock():
            return False
        self.__nit = nit
        return True

    def list_of_source_files(self, list_of_source_files):
        if self.is_sla_lock():
            return False
        self.__list_of_source_files = list_of_source_files
        return True

    def az_id_list(self, az_id_list):
        if self.is_sla_lock():
            return False
        self.__az_id_list = az_id_list
        return True

    def az_dict(self, az_dict):
        if self.is_sla_lock():
            return False
        self.__az_dict = az_dict
        return True

    def metrics_dict(self, metrics):
        if self.is_sla_lock():
            return False
        self.metrics = metrics
        return True

    def set_logger(self, logger):
        if self.is_sla_lock():
            return False
        self.logger = logger
        return True

    def output_type(self, output_type, out_sep):
        if self.is_sla_lock():
            return False
        self.__output_type = output_type.split(K_SEP)
        try:
            self.__out_sep = int(out_sep)
        except ValueError:
            self.__out_sep = eval(out_sep)
            pass
        except Exception as e:
            self.logger.critical(e)

        return True

    def az_selection(self, az_selection):
        if self.is_sla_lock():
            return False
        self.__az_selection = az_selection
        return True

    def trace_class(self, trace_class):
        if self.is_sla_lock():
            return False
        self.__trace_class = trace_class
        return True

    def energy_model_src(self, energy_model):
        if self.is_sla_lock():
            return False
        self.__energy_model_src = energy_model
        return True

    # Note: deprecated
    def avg_load_objective(self, avg_load_objective_file):
        if self.is_sla_lock():
            return False
        self.__avg_load_objective_file = avg_load_objective_file
        if self.g_algorithm() == "EUCA":
            return True
        else:
            with open(avg_load_objective_file, 'r') as file:
                for line in file:
                    item = line.split(sep=',')
                    self.logger.debug('LOAD: az:{}, avg:{}'.format(item[0], item[1]))
                    try:
                        self.__avg_load_objective[item[0]] = float(item[1])
                    except Exception as e:
                        self.logger.error("Error on read {}, is {} ({})".format(avg_load_objective_file, self.__avg_load_objective, e))
            return True

    def milestones(self, number_of_milestones):
        if self.is_sla_lock():
            return False
        self.__number_of_milestones = number_of_milestones
        return True

    ''' GETTERS '''

    def g_milestones(self):
        return self.__number_of_milestones

    # Note: deprecated
    def g_avg_load_objective(self, az_id=None):
        if az_id is not None:
            return self.__avg_load_objective[az_id]
        return self.__avg_load_objective

    def g_avg_load_objective_file(self):
        return self.__avg_load_objective_file

    def g_energy_model_src(self):
        return self.__energy_model_src

    def g_trace_class(self):
        return self.__trace_class

    def g_az_selection(self):
        return self.__az_selection

    def g_output_type(self):
        return self.__output_type, self.__out_sep

    def g_consolidation_alg(self):
        return self.__consolidation_alg

    def g_ff(self):
        return self.__ff

    def g_algorithm(self):
        return self.__algorithm

    def g_source_folder(self):
        return self.__source

    def g_has_overcommitting(self):
        return self.__has_overcommitting

    def g_has_consolidation(self):
        return self.__consolidation

    def g_enable_emon(self):
        return self.__enable_emon

    def g_enable_replication(self):
        return self.__enable_replication

    def g_window_time(self):
        return self.__window_time

    def g_lock_case(self):
        return self.__lock_case

    def g_number_of_azs(self):
        return self.__number_of_azs

    def g_max_az_per_region(self):
        return self.__max_az_per_region

    def g_date(self):
        return str(self.__date)

    def g_core_2_ram_default(self):
        return self.__core_2_ram_default

    def g_data_output(self):
        return self.__data_output

    def g_log_output(self):
        return self.__log_output

    def g_default_file_output(self):
        return self.__default_file_output

    def g_trigger_to_migrate(self):
        return self.__trigger_to_migrate

    def g_frag_class(self):
        return self.__frag_class

    def g_vcpu_per_core(self):
        return self.__vcpu_per_core

    def g_ha_input(self):
        return self.__ha_input

    def g_az_conf(self):
        return self.__az_conf

    def g_nit(self):
        return self.__nit

    def g_list_of_source_files(self):
        return self.__list_of_source_files

    def g_az_id_list(self):
        return self.__az_id_list

    def g_az_dict(self):
        return self.__az_dict

    def g_metrics_dict(self):
        return self.metrics.get_metrics()

    def g_logger(self):
        return self.logger

    '''    def xxx(self, xxx):
        if not self.set_sla_lock():
            return False
        self.__xxx = xxx'''

    def check_simulator_memory(self) -> str:
        ram = psutil.virtual_memory()[2]
        disk = psutil.disk_usage(self.g_data_output())[3]
        if ram > 99.0 and disk > 99.0:
            self.logger.critical("Memory is full, exiting!")
            exit(code=3)
        return "RAM: {}, Disc: {}".format(ram, disk)


"""
class Metrics(object):
    #Concentrates all metrics used in CHAVE simulator
    def __init__(self, az_id, sla):
        self.logger = sla.logger
        self.sla = sla
        self.__metrics_dict = OrderedDict()
        self.__az_id_list = az_id
        self.is_init = self.init_dict(is_print=False)

    def __repr__(self):
        return repr(["is_init:", self.is_init, 'az_id_list', self.__az_id_list, "az_id_list", self.__az_id_list])

    def get_metrics(self):
        return self.__metrics_dict

    def just_energy(self, az_id, energy, global_time):
        if self.sla.metrics.set_in_pos(az_id, 'energy_l', energy, global_time) and \
                self.sla.metrics.add(az_id, 'total_energy_f', energy):
            acum = self.sla.metrics.get(az_id, 'total_energy_f')
            if self.sla.metrics.set_in_pos(az_id, 'energy_acum_l', acum, global_time):
                # self.logger.debug("{}\t Energy at {}t is {}/{} Wh".format(az_id, global_time, energy, acum))
                return True
        else:
            self.logger.error("{}\t Metrics problem: en:{} gt:{}".format(az_id, energy, global_time))
            return False

    def set(self, az_id, key, value):
        if key in all_metrics_l[0: len_v]:
            self.__metrics_dict[az_id][key] = value
        elif key in all_metrics_l[len_v: len_m]:
            self.__metrics_dict[az_id][key].append(value)
        else:
            self.logger.error(resp('set', key, value))
            return False
        return True

    def set_in_pos(self, az_id, key, value, position):
        if key in all_metrics_l[0: len_v]:
            self.logger.error("This func is only for metric defined by lists type! You choose: k:{}".format(key))
        elif key in all_metrics_l[len_v: len_m]:
            if len(self.__metrics_dict[az_id][key]) > position:
                self.__metrics_dict[az_id][key][position] = value
            elif len(self.__metrics_dict[az_id][key]) == position:
                self.__metrics_dict[az_id][key].append(value)
            else:
                self.logger.error("{}->{}\tAre you trying put val:{} in the future?{}".format(az_id, key, value, position))
        else:
            self.logger.error(resp('set', key, value))
            return False
        return True

    def get(self, az_id, key):
        if key in all_metrics_l:
            return self.__metrics_dict[az_id][key]
        else:
            self.logger.error(resp('get', key))
            return False

    def add(self, az_id, key, value, n=-1):
        if key in all_metrics_l[0: len_v]:
            try:
                self.__metrics_dict[az_id][key] = self.__metrics_dict[az_id][key] + value
            except TypeError:
                pass
        elif key in all_metrics_l[len_v: len_m]:
            if n >= 0:
                self.__metrics_dict[az_id][key][n] += value
            else:
                self.logger.error("Use 'set' command or specify the 'n' in list position")
                return False
        else:
            self.logger.error(resp('add', key, value))
            return False
        return True

    def incr_1(self, az_id, key, n=-1):
        if key in all_metrics_l[0: len_v]:
            self.__metrics_dict[az_id][key] = self.__metrics_dict[az_id][key] + 1
        elif key in all_metrics_l[len_v: len_m]:
            if n >= 0:
                self.__metrics_dict[az_id][key][n] += 1
            else:
                self.logger.error("Use 'set' command or specify the 'n' in list position")
                return False
        else:
            self.logger.error(resp('increment', key))
            return False
        return True

    def sum(self, az_id, key, value=None):
        if key in all_metrics_l[0: len_v]:
            self.logger.error("This is only for list. Use 'get' command")
            ret = False
        elif key in all_metrics_l[len_v: len_m]:
            ret = sum(values for values in self.__metrics_dict[az_id][key])
        else:
            self.logger.error(resp('sum', key, value))
            return False
        return ret

    def rst(self, az_id, key, value=None):
        if key in all_metrics_l[0: len_v]:
            self.__metrics_dict[az_id][key] = 0
        elif key in all_metrics_l[len_v: len_m]:
            self.__metrics_dict[az_id][key] = []
        else:
            self.logger.error(resp('rst', key, value))
            return False
        return True

    def avg(self, az_id, key, value=None):
        if key in all_metrics_l[0: len_v]:
            self.logger.error("This is only for list. Use 'get' command")
            return False
        elif key in all_metrics_l[len_v: len_m]:
            sum_avg = 0
            for values in self.__metrics_dict[az_id][key]:
                if type(sum_avg) == list or type(values) == list:
                    self.logger.error("DIFFERENT TYPES sa{} v{} {} {} {}".format(
                        type(sum_avg), type(values), key, sum_avg, values))
                    # exit(1)
                    raise ConnectionAbortedError
                sum_avg += values
            len_avg = float(len(self.__metrics_dict[az_id][key]))
            if len_avg == 0:
                return False
            return sum_avg / len_avg
        else:
            self.logger.error(resp('avg', key, value))
            return False

    def init_dict(self, is_print=False):
        temp_az_list = list(self.__az_id_list)
        temp_az_list.append('global')
        for az_id in temp_az_list:
            self.__metrics_dict[az_id] = OrderedDict()
            for i, k in enumerate(all_metrics_l):
                if i < len_v:
                    self.__metrics_dict[az_id][k] = 0
                else:
                    self.__metrics_dict[az_id][k] = []
        self.__metrics_dict['global']['max_elapsed_internal_l'] = [0, 0]  # [global_time, elapsed]
        if is_print:
            for az_id, key in self.__metrics_dict.items():
                self.logger.debug('{}'.format(az_id))
                for k, value in key.items():
                    self.logger.debug('\t{}: {}'.format(k, value))
        # Done!
        return True

    def resume_global(self, elapsed, api=None):
        for i, key in enumerate(k_values):
            total = 0
            for az_id in self.sla.g_az_id_list():
                total += self.get(az_id, key)
            self.add('global', key, total)
            self.logger.debug("Global metric for {} is {}".format(key, total))

        # self.set('global', 'sla_violations_i', api.get_total_SLA_violations_from_cloud())
        # self.set('global', 'overcommit_i', api.get_list_overcom_amount_from_cloud())
        self.set('global', 'elapsed_time_i', elapsed)
"""
