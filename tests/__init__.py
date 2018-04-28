
from collections import OrderedDict

import time
count = 0
start = time.time()
while count < 24531071:
    count = count + 1

elapsed = time.time() - start
print elapsed,count

# O resultado mostra um acrescimo de 2,23 segundos
# >> 2.23299884796 24531071


key_list = ['total_alloc', 'accepted_alloc', 'max_host_on',
            'energy_list', 'energy_avg', 'energy_t',
            'sla_break', 'alloc', 'total_alloc_list',
            'energy_ttl', 'dc_load']
command_list = ['set', 'add', 'summ', 'get'] # 'init'

class Metric:
    def __init__(self):
        self.__metrics_dict = OrderedDict()
        self.az_id_list = ['ds1', 'ds2', 'ds3', 'ds4']


    def __init_metrics_dict(self, is_print=False):
        for azid in self.az_id_list:
            self.__metrics_dict[azid] = OrderedDict()
            for key in key_list:
                self.__metrics_dict[azid][key] = []
        if is_print:
            for azid, key in self.__metrics_dict.viewitems():
                print '\n\n', azid,
                for k, value in key.viewitems():
                    print '\n\t', k, '\n\t\t', value


    def metrics(self, az_id, command, key, value=None, n=-1):
        str_error = ("Key (%s) not found for Command %s, with val %s!!" % (key, command, value))
        str_ok = ("{%s: %s} -> " % (key, value))
        l = len(key_list)
        m = 3
        if command is 'INIT':
            self.__init_metrics_dict()
            if key is "ALL":
                key1 = key_list[0:m]  # inteiros
                l1 = len(key1)
                key2 = key_list[m:l]  # listas vazias
                l2 = len(key2)
                key = [key1, key2]
                self.__logger.debug("Init Metrics Size: ", l1, l2)
                if value == "ZEROS":
                    for kk in key:
                        x = len(kk)
                        for k in kk:
                            if x == l1:
                                self.__metrics_dict[az_id][k] = 0
                            elif x == l2:
                                self.__metrics_dict[az_id][k] = []
                    return True
                else:
                    self.__logger.error("You must specify 'ZEROS'!!")
                    return False
            self.__logger.debug(str_ok, self.__metrics_dict[az_id].viewitems())

        elif command is 'set':
            if key in key_list[0:m]:
                self.__metrics_dict[az_id][key] = value
            elif key in key_list[m:l]:
                self.__metrics_dict[az_id][key].append(value)
            else:
                self.__logger.error(str_error)
                return False
            self.__logger.debug(str_ok, True)  #, self.__metrics_dict[az_id].viewitems()))
            return True

        elif command is 'get':
            if key in key_list:
                self.__logger.debug(str_ok, self.__metrics_dict[az_id][key])
                return self.__metrics_dict[az_id][key]
            else:
                self.__logger.error(str_error)
                return False

        elif command is 'add':
            if key in key_list[0:m]:
                self.__metrics_dict[az_id][key] += value
            elif key in key_list[m:l]:
                if n >= 0:
                    self.__metrics_dict[az_id][key][n] += value
                else:
                    self.__logger.error("Use 'set' command or specify 'n' position")
                    return False
            else:
                self.__logger.error(str_error)
                return False
            self.__logger.debug(str_ok, self.__metrics_dict[az_id][key])
            return self.__metrics_dict[az_id][key]

        elif command is 'summ':
            if key in key_list[0:m]:
                ret = self.__metrics_dict[az_id][key]
            elif key in key_list[m:l]:
                ret = sum(values for values in self.__metrics_dict[az_id][key])
            else:
                self.__logger.error(str_error)
                return False
            self.__logger.debug(str_ok, ret)
            return ret
        else:
            self.__logger.error("Command (" + str(command) + ") not found!!")
        return False


m = Metric()
m.metrics('ds1', 'INIT', 'ALL', 'ZEROS')

for i in range(10):
    for az in m.az_id_list:
        print "AZ:", az,
        for com in command_list:
            print '\n\tCommand', com
            for key in key_list:
                print '\t\t',
                m.metrics(az, com, key, i+1, 0)