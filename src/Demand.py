from copy import deepcopy
import random
from math import sqrt
from numpy import std, mean, sqrt
import numpy as np

from Virtual import VirtualMachine
from collections import OrderedDict


class Demand(object):
    def __init__(self, algorithm, logger):
        self.metrics_dict = OrderedDict
        self.algorithm = algorithm
        self.logger = logger
        self.azs_id = []
        self.number_of_azs = -1
        self.vmRam_default = 4
        self.all_vms_dict = dict()
        self.all_op_dict = dict()
        self.all_ha_dict = dict()

    def get_all_sources(self, list_of_source_files):
        self._define_az_id(list_of_source_files)
        for i, source_file in enumerate(list_of_source_files):
            self.all_vms_dict[self.az_id[i]],\
            self.all_op_dict[self.az_id[i]],\
            self.all_ha_dict[self.az_id[i]] = self._get_vms_from_source(source_file)

    def _define_az_id(self, list_of_souce_files):
        azs_id = []
        for source in list_of_souce_files:
            ns = str(source).rfind("/")
            ne = str(source).rfind("-")
            azs_id.append(str(source[ns + 1:ne]))
        if len(list_of_souce_files) > 1:
            self.azs_id = azs_id
            self.number_of_azs = len(list_of_souce_files)
        else:
            return azs_id

    def define_regions(self, source_list, max_az_per_region):
        if max_az_per_region < 2:
            self.logger.error("Low value config max-ax-per-region, must be > 2")
        n = len(source_list)
        regions_list = []
        for i in range(0, n):
            kv = {"name": 'region_'+str(i),
                  "azs_max": 'max_az_per_region'}
            regions_list.append(kv)
        return regions_list

    def _get_ha_from_source(self, source_file):
        ha_source_file = source_file.split(".txt")[0] + "-ha.txt"
        ha_demand_dict = OrderedDict()
        with open(ha_source_file, "r") as ha_source:
            az_availability = ha_source.read()
            ha_demand_dict["this_az"] = az_availability  # apenas uma vez
            for demand in ha_source:
                demand = demand.split()
                #  ha_ts = demand[0]  # <- not used!
                vm_id = demand[1]
                ha_tax = demand[2]
                ha_demand_dict[vm_id] = ha_tax
            ha_source.close()
        return ha_demand_dict

    def _get_vms_from_source(self, source_file):
        '''
        :param source_file: one source file, refer to all demand from one AZ
        :return:    operations_dict --> a ordered dictionary with all operations (create/destroy)
                    vms_list --> a list with all VMs objects to instance
        '''
        ha_dict = self._get_ha_from_source(source_file)
        operations_dict = OrderedDict()
        vms_list = []
        vm_de_allocate = []
        line = 0
        with open(source_file, 'r') as source:
            for operation in source:
                line = line + 1
                operation = operation.split()
                state = str(operation[0])
                timestamp = int(operation[1])
                this_vm_id = str(operation[2])
                op_id = str(this_vm_id + '-' + state)
                # Todo: ver se funciona mesmo!!
                dc_id = self._define_az_id(source_file)
                type = "VM"
                if state == "START":
                    if self.algorithm == "CHAVE":  # Will allocate later
                        host = "None"
                    elif self.algorithm == "EUCA":
                        host = str(operation[3])  # Default allocation from EUCA_files
                    else:
                        self.logger.info("We must decide which algorithm will be used!")
                        host = "None"
                    ha = ha_dict[this_vm_id]
                    vcpu = int(operation[4])
                    vram = self.vmRam_default * vcpu
                    lifetime = 0
                    vm = VirtualMachine(this_vm_id, vcpu, vram, ha, type, host, dc_id, timestamp, lifetime, self.logger)
                    vms_list.append(vm)
                    vm_de_allocate.append(vm)
                    operations_dict[op_id] = vm

                elif state == "STOP":
                    last_op_id = str(this_vm_id + '-START')
                    vm_to_stop = operations_dict[last_op_id]
                    try:
                        lifetime = timestamp - int(vm_to_stop.get_timestamp())
                    finally:
                        self.logger.error("Problem to calculate 'lifetime': " + str(lifetime))
                        lifetime = -1
                    if self.algorithm == "CHAVE":
                        host = "None"
                    else:
                        host = vm_to_stop.get_physical_host()

                    vcpu = vm_to_stop.get_vcpu()
                    ha = vm_to_stop.get_ha()
                    vram = vm_to_stop.get_vram()

                    vm = VirtualMachine(this_vm_id, vcpu, vram, ha, type, host, dc_id, timestamp, lifetime, self.logger)

                    operations_dict[op_id] = vm
                    try:
                        vmindex = vm_de_allocate.index(vm_to_stop)
                        vm_de_allocate.pop(vmindex)
                    finally:
                        self.logger.error("On pop VM from " + str(op_id))
            if vm_de_allocate:  # Se tiver algo, entao sobrou alguma vm
                self.logger.error("On de-allocate:" + str(vm_de_allocate))
        return vms_list, operations_dict, ha_dict

    # TODO: criar para GVT
    def get_vms_from_gvt(self, source_file):
        pass

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
        return False

    def my_std(data):
        u = mean(data)
        std = sqrt(1.0 / (len(data) - 1) * sum([(e - u) ** 2 for e in data]))
        return 1.96 * std / sqrt(len(data))

    def mean(data):
        return sum(data) / float(len(data))'''
