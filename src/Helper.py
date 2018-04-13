from copy import deepcopy
import random
from math import sqrt
from numpy import std, mean, sqrt
import numpy as np
from collections import OrderedDict
from Virtual import VirtualMachine


class Helper(object):
    def __init__(self, dc, logger, algorithm):
        self.dc = dc
        self.algorithm = algorithm
        self.logger = logger

    def _get_ha_from_source(self, source_file):
        ha_source_file = source_file.split(".txt")[0] + "-ha.txt"
        ha_demand_dict = OrderedDict()
        with open(ha_source_file, "r") as ha_source:
            az_availability = ha_source.read()
            ha_demand_dict["az"] = az_availability  # apenas uma vez
            for demand in ha_source:
                demand = demand.split()
                #  ha_ts = demand[0]  # <- not used!
                ha_id = demand[1]
                ha_tax = demand[2]
                ha_demand_dict[ha_id] = ha_tax
            ha_source.close()
        return ha_demand_dict

    def get_vms_from_source(self, source_file):
        ha_dict = self._get_ha_from_source(source_file)
        operations_dict = OrderedDict()
        vms_list = []
        vm_allocate = []
        line = 0
        with open(source_file, 'r') as source:
            for operation in source:
                line = line + 1
                operation = operation.split()
                state = str(operation[0])
                timestamp = int(operation[1])
                vm_id = str(operation[2])
                op_id = str(vm_id + '-' + state)
                type = "VM"
                if state == "START":
                    if self.algorithm == "CHAVE":  # alocaremos depois
                        host = "None"
                    if self.algorithm == "EUCA":
                        host = str(operation[3])  # alocação padrão
                    ha = ha_dict[vm_id]
                    vcpu = int(operation[4])
                    vram = self.vmRam_default * vcpu
                    lifetime = 0
                    # print (vm_id, vcpu, vram, ha, availability, type, host, dcid, timestamp, lifetime)
                    vm = VirtualMachine(vm_id, vcpu, vram, ha, type, host, self.dcid, timestamp, lifetime, self.logger)
                    vms_list.append(vm)
                    vm_allocate.append(vm)
                    operations_dict[op_id] = vm

                elif state == "STOP":
                    last_op_id = str(vm_id + '-START')
                    try:
                        lifetime = timestamp - int(operations_dict[last_op_id].get_timestamp())
                    finally:
                        self.logger.error("on LIFETIME" + str(lifetime))
                        lifetime = -1
                    if self.algorithm == "CHAVE":
                        host = None
                    else:
                        host = operations_dict[last_op_id].get_physical_host()  # alocação padrão

                    vcpu = operations_dict[last_op_id].get_vcpu()
                    ha = operations_dict[last_op_id].get_ha()
                    vram = operations_dict[last_op_id].get_vram()

                    vm = VirtualMachine(vm_id, vcpu, vram, ha, type, host, timestamp, lifetime, self.logger)
                    vm_to_pop = operations_dict[last_op_id]
                    # vms_list.append(vm)
                    operations_dict[op_id] = vm
                    # print "vm", line,":", vm.get_parameters(),
                    try:
                        vmindex = vm_allocate.index(vm_to_pop)
                        vm_allocate.pop(vmindex)
                    finally:
                        self.logger.error("On pop VM from " + str(op_id))
            if vm_allocate != []:
                self.logger.error("On deallocate:" + str(vm_allocate))
        return vms_list, operations_dict

    '''def ha_on_demand(self, av, max):
        if self.monte_carlo():
            return np.random.uniform(av, max)
        return av

    def monte_carlo(self):
        radius = 1
        x = np.random.rand(1)
        y = np.random.rand(1)
        # Funcao que retorna 21% de probabilidade
        if x ** 2 + y ** 2 >= radius:
            return True
        return False'''

    def metrics(command, key, value, n=None):  # metrics_dict{}
        command_list = ['get', 'set', 'add', 'init', 'resume']
        key_list = ['total_alloc', 'accepted_alloc',
                    'acc_list', 'acc_means', 'energy_list', 'energy_means', 'nop_list', 'nop_means',
                    'sla_break', 'sla_break_steal', 'alloc', 'total_alloc_list', 'dealloc', 'realloc', 'energy_rlc',
                    'energy_ttl', 'dc_vm_load', 'dc_load']
        if command in command_list:
            if command is 'init':
                if key is "ALL":
                    key1 = key_list[0:2]
                    key2 = key_list[2:8]
                    key3 = key_list[8:17]
                    key = [key1, key2, key3]
                if value == "INIT":
                    for kk in key:
                        x = len(kk)
                        for k in kk:
                            if x == 2:
                                metrics_dict[k] = 0.0
                            elif x == 6:
                                metrics_dict[k] = []
                            elif x == 9:
                                metrics_dict[k] = [0 for i in range(nit)]
            if command is 'set':
                if key in key_list[0:2]:
                    metrics_dict[key] = value
                    return True
                if key in key_list[2:8]:
                    metrics_dict[key].append(value)
                    return True

            if command is 'get':
                if key in key_list:
                    return metrics_dict[key]

            if command is 'add':
                if key in key_list[2:17]:
                    metrics_dict[key] = metrics_dict[key] + value
                    return metrics_dict[key]
                    # sum([v.get_vram() for v in self.virtual_machine_list])

            if command is 'resume':
                if key in key_list[2:17]:
                    return sum(values for values in metrics_dict[key])
                elif key in key_list[0:2]:
                    return metrics_dict[key]
        else:
            logger.error("Command (" + str(command) + ") not found!!")
        return None
    
    def opdict_to_vmlist(id):
        for vm_temp in vm_list:
            if vm_temp.get_id() == id:
                return vm_temp
        return None


    '''def my_std(data):
        u = mean(data)
        std = sqrt(1.0 / (len(data) - 1) * sum([(e - u) ** 2 for e in data]))
        return 1.96 * std / sqrt(len(data))

    def mean(data):
        return sum(data) / float(len(data))'''
