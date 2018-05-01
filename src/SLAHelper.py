from copy import deepcopy
import random
from math import sqrt
from numpy import std, mean
import numpy as np
import logging
from collections import OrderedDict

k_values = ['total_alloc_i', 'accepted_alloc_i', 'max_host_on_i', 'total_energy_f']
k_lists = ['energy_l', 'energy_avg_l', 'energy_hour_l', 'sla_break_l', 'alloc_l', 'total_alloc_l', 'dc_load_l']
key_list = k_values + k_lists
command_list = ['set', 'add', 'sum', 'get', 'avg', 'init']


class SLAHelper(object):
    def __init__(self):
        # vars
        self.__pm = ""  # str()
        self.__ff = ""  # str()
        self.__algorithm = ""  # str()
        self.__has_overbooking = False  # bool
        self.__window_time = 0  # int
        self.__window_size = 0  # int
        self.__number_of_azs = 0  # int
        # vars from environment
        self.__max_az_per_region = ""  # str()
        self.__date = ""  # str()
        self.__core_2_ram_default = ""  # str()
        self.__data_output = ""  # str()
        self.__log_output = ""  # str()
        self.__trigger_to_migrate = ""  # str()
        self.__frag_percentual = ""  # str()
        self.__output_type = ""
        # lists
        self.__ha_input = []
        self.__az_nodes = []
        self.__az_cores = []
        self.__az_conf = []
        self.__nit = []
        self.__list_of_source_files = []
        self.__az_id_list = []
        # dicts
        self.__az_dict = dict()
        self.__metrics_dict = OrderedDict()
        # objects
        self.__logger = logging
        self.__is_locked = False

    def __repr__(self):
        return repr([self.__nit, self.__trigger_to_migrate, self.__frag_percentual, self.__has_overbooking,
                     self.__pm, self.__ff, self.__date, self.__window_size, self.__window_time,
                     self.__algorithm, self.__max_az_per_region])

    def obj_id(self):  # Return the unique hexadecimal footprint from each object
        return str(self).split(' ')[3].split('>')[0]

    def is_sla_lock(self):
        if self.__is_locked:
            res = "The SLA Object is locked, please, re-run the simulator with desired parameters"
            self.__logger.error(res)
            return True
        return False

    def set_sla_lock(self, state):
        if type(state) is bool:
            self.__is_locked = state
            str = "SLA sate is locked? R: %s" % (state)
            ret = True
        else:
            str = "State must be a bool type: True | False"
            ret = False
        self.__logger.info(str)
        return ret

    def define_az_id(self, mode):
        if self.is_sla_lock():
            return False
        if len(self.__ha_input) != len(self.__az_nodes) != len(self.__az_cores) != len(self.__nit):
            self.__logger.error("Len diff: ", len(self.__ha_input), len(self.__az_nodes), len(self.__az_cores), len(self.__nit))

        for i, source in enumerate(self.__list_of_source_files):
            if mode == "file":
                ns = str(source).rfind("/")
                ne = str(source).rfind("-")
                id = str(source[ns + 1: ne])
            elif mode == "auto":
                id = "AZ"+str(i)
            self.__az_id_list.append(id)
            self.__az_dict[id] = {'source_files': source,
                                'ha_source_files': self.__ha_input[i],
                                'az_nodes': int(self.__az_nodes[i]),
                                'az_cores': int(self.__az_cores[i]),
                                'az_ram': (int(self.__az_cores[i]) * int(self.__core_2_ram_default)),
                                'az_nit': int(self.__nit[i])}
        return True

    def set_conf(self, raw_data, flag):
        if self.is_sla_lock():
            return False
        # node:core
        out = []
        i = 0
        while i < len(raw_data):
            if flag is 'az_conf':
                self.__az_nodes.append(int(raw_data[i]))  # node
                self.__az_cores.append(int(raw_data[i + 1]))  # core
                i = i + 2
            if flag is 'nit':
                self.__nit.append(int(raw_data[i]))  # nit
                out.append(int(raw_data[i]))
                i = i + 1
        if type(raw_data) is str:
            out = int(raw_data)
        return out

    def init_metrics(self, is_print=False):
        m = len(k_values)
        for az_id in self.__az_id_list:
            self.__metrics_dict[az_id] = OrderedDict()
            for i, k in enumerate(key_list):
                if i < m:
                    self.__metrics_dict[az_id][k] = 0
                else:
                    self.__metrics_dict[az_id][k] = []

        self.__logger.info("Metrics Initialized! %s" % self.__metrics_dict.viewitems())
        if is_print:
            for azid, key in self.__metrics_dict.viewitems():
                print('\n\n', azid,)
                for k, value in key.viewitems():
                    print('\n\t', k, '\n\t\t', value)

    def metrics(self, az_id, command, key, value=None, n=-1):
        str_error = ("Key (%s) not found for Command %s, with val %s!!" % (key, command, value))
        str_ok = ("{0}: {1} -> ".format(key, value))
        l = len(key_list)
        m = len(k_values)
        #if command not in command_list or key not in key_list:
        #    self.__logger.error("Parameter not found: %s %s %s" % (az_id, command, key))
        #    return False
        #
        if command is 'set':
            if key in key_list[0:m]:
                self.__metrics_dict[az_id][key] = value
            elif key in key_list[m:l]:
                self.__metrics_dict[az_id][key].append(value)
            else:
                self.__logger.error(str_error)
                return False
            self.__logger.debug(str_ok)  #, self.__metrics_dict[az_id].viewitems()))
            return True
        #
        elif command is 'get':
            if key in key_list:
                self.__logger.debug(str_ok)
                return self.__metrics_dict[az_id][key]
            else:
                self.__logger.error(str_error)
                return False
        #
        elif command is 'add':
            if key in key_list[0:m]:
                self.__metrics_dict[az_id][key] = self.__metrics_dict[az_id][key] + value
            elif key in key_list[m:l]:
                if n >= 0:
                    self.__metrics_dict[az_id][key][n] += value
                else:
                    self.__logger.error("Use 'set' command or specify the 'n' in list position")
                    return False
            else:
                self.__logger.error(str_error)
                return False
            self.__logger.debug(str_ok)
            return self.__metrics_dict[az_id][key]
        #
        elif command is 'sum':
            if key in key_list[0:m]:
                self.__logger.error("This is only for list. Use 'get' command")
                ret = False
            elif key in key_list[m:l]:
                ret = sum(values for values in self.__metrics_dict[az_id][key])
            else:
                self.__logger.error(str_error)
                return False
            self.__logger.debug(str_ok)
            return ret
        #
        elif command is 'avg':
            if key in key_list[0:m]:
                self.__logger.error("This is only for list. Use 'get' command")
                return False
            elif key in key_list[m:l]:
                sum_avg = 0
                for values in self.__metrics_dict[az_id][key]:
                    if type(sum_avg) == list or type(values) == list:
                        self.__logger.error("DIFFERENT TYPES sa%s v%s %s %s %s" % (type(sum_avg), type(values), key, sum_avg, values))
                        exit(1)
                    sum_avg += values
                #sum_avg = float(sum(values) for values in self.__metrics_dict[az_id][key])
                len_avg = float(len(self.__metrics_dict[az_id][key]))
                if len_avg == 0:
                    #self.__logger.error("LEN_AVG is Zero")
                    return False
                self.__logger.debug(str_ok)
                return sum_avg / len_avg
            else:
                self.__logger.error(str_error)
                return False
        #
        elif command is 'init':
            self.init_metrics(is_print=False)
        else:
            self.__logger.error("Command (" + str(command) + ") not found!!")
        return False

    def pm(self, pm):
        if self.is_sla_lock():
            return False
        self.__pm = pm  # str()
        return True

    def ff(self, ff):
        if self.is_sla_lock():
            return False
        self.__ff = ff
        return True

    def algorithm(self, algorithm):
        if self.is_sla_lock():
            return False
        self.__algorithm = algorithm
        return True

    def has_overbooking(self, has_overbooking):
        if self.is_sla_lock():
            return False
        self.__has_overbooking = has_overbooking
        return True

    def window_time(self, window_time):
        if self.is_sla_lock():
            return False
        self.__window_time = window_time
        return True

    def window_size(self, window_size):
        if self.is_sla_lock():
            return False
        self.__window_size = window_size
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
        if core_2_ram_default == 0:
            core_2_ram_default = 2
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

    def trigger_to_migrate(self, trigger_to_migrate):
        if self.is_sla_lock():
            return False
        self.__trigger_to_migrate = trigger_to_migrate
        return True

    def frag_percentual(self, frag_percentual):
        if self.is_sla_lock():
            return False
        self.__frag_percentual = frag_percentual
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

    def metrics_dict(self, metrics_dict):
        if self.is_sla_lock():
            return False
        self.__metrics_dict = metrics_dict
        return True

    def logger(self, logger):
        if self.is_sla_lock():
            return False
        self.__logger = logger
        return True

    def output_type(self, output_type):
        if self.is_sla_lock():
            return False
        self.__output_type = output_type
        return True

    ''' GETTERS '''
    def g_output_type(self):
        return self.__output_type

    def g_pm(self):
        return self.__pm

    def g_ff(self):
        return self.__ff

    def g_algorithm(self):
        return self.__algorithm

    def g_has_overbooking(self):
        return self.__has_overbooking

    def g_window_time(self):
        return self.__window_time

    def g_window_size(self):
        return self.__window_size

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

    def g_trigger_to_migrate(self):
        return self.__trigger_to_migrate

    def g_frag_percentual(self):
        return self.__frag_percentual

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
        return self.__metrics_dict

    def g_logger(self):
        return self.__logger

    '''    def xxx(self, xxx):
        if not self.set_sla_lock():
            return False
        self.__xxx = xxx'''

    def monte_carlo(self):
        radius = 1
        x = np.random.rand(1)
        y = np.random.rand(1)
        # Funcao que retorna 21% de probabilidade
        if x ** 2 + y ** 2 >= radius:
            return True
        return False

    def my_std(self, data):
        u = mean(data)
        std = sqrt(1.0 / (len(data) - 1) * sum([(e - u) ** 2 for e in data]))
        return 1.96 * std / sqrt(len(data))

    def mean(self, data):
        return sum(data) / float(len(data))

