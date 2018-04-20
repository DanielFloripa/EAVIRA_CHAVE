from copy import deepcopy
import random
from math import sqrt
from numpy import std, mean
import numpy as np
import sys

from Virtual import VirtualMachine
from SLAHelper import *
from Controller import *
from DistributedInfrastructure import *
from Eucalyptus import *
from SLAHelper import *


class Demand(object):
    def __init__(self, sla):
        self.sla = sla
        self.algorithm = sla.g_algorithm()
        self.list_of_source_files = sla.g_list_of_source_files()
        self.logger = sla.g_logger()
        self.az_id = sla.g_az_id_list()
        self.number_of_azs = sla.g_number_of_azs()
        self.vmRam_default = sla.g_core_2_ram_default()
        # Tres dicionarios iportantes:
        self.all_vms_dict = dict()
        self.all_op_dict = dict()
        self.all_ha_dict = dict()

    def __repr__(self):
        return repr([self.sla, self.logger, self.algorithm, self.az_id, self.number_of_azs, self.vmRam_default,
                     self.all_vms_dict, self.all_op_dict, self.all_ha_dict])

    def get_demand_from_az(self, az_id):
        return self.all_vms_dict[az_id], self.all_op_dict[az_id], self.all_ha_dict[az_id]

    def create_vms_from_sources(self):
        # self._define_az_id(list_of_source_files)
        for i, source_file in enumerate(self.list_of_source_files):
            id = self.az_id[i]
            self.all_vms_dict[id], self.all_op_dict[id], self.all_ha_dict[id] = self._get_vms_from_source(source_file)

    def _get_ha_from_source(self, source_file):
        ha_source_file = source_file.split(".txt")[0] + "-ha.txt"
        ha_demand_dict = OrderedDict()
        with open(ha_source_file, "r") as ha_source:
            ha_demand_dict["this_az"] = ha_source.readline()  # apenas uma vez
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
                az_id = self._get_az_id(source_file)
                type = "VM"
                if state == "START":
                    if self.algorithm == "CHAVE":  # Will allocate later
                        host = "None"
                    elif self.algorithm == "EUCA":
                        host = str(operation[3])  # Default allocation from EUCA_files
                    else:
                        self.logger.info("We must decide which algorithm will be used!")
                        exit(-1)
                    ha = ha_dict[this_vm_id]
                    vcpu = int(operation[4])
                    vram = self.vmRam_default * vcpu
                    lifetime = 0
                    vm = VirtualMachine(this_vm_id, vcpu, vram, ha, type, host, az_id, timestamp, lifetime, self.logger)
                    vms_list.append(vm)
                    vm_de_allocate.append(vm)
                    operations_dict[op_id] = vm

                elif state == "STOP":
                    last_op_id = str(this_vm_id + '-START')
                    vm_to_stop = operations_dict[last_op_id]
                    lifetime = 0
                    try:
                        lifetime = timestamp - int(vm_to_stop.get_timestamp())
                    except:
                        self.logger.error("Problem on %s 'lifetime': %s %s %s \n %s" %
                                          (last_op_id, lifetime, timestamp, vm_to_stop.get_timestamp(), sys.exc_info()[0]))
                    if self.algorithm == "CHAVE":
                        host = "None"
                    else:
                        host = vm_to_stop.get_physical_host()

                    vcpu = vm_to_stop.get_vcpu()
                    ha = vm_to_stop.get_ha()
                    vram = vm_to_stop.get_vram()

                    vm = VirtualMachine(this_vm_id, vcpu, vram, ha, type, host, az_id, timestamp, lifetime, self.logger)

                    operations_dict[op_id] = vm
                    try:
                        vmindex = vm_de_allocate.index(vm_to_stop)
                        vm_de_allocate.pop(vmindex)
                    except:
                        self.logger.error("On pop VM from %s \n %s" % (op_id, sys.exc_info()[0]))
            if vm_de_allocate:  # Se tiver algo, entao sobrou alguma vm
                self.logger.error("On de-allocate:" + str(vm_de_allocate))
        return vms_list, operations_dict, ha_dict

    # TODO: criar para GVT
    def get_vms_from_gvt(self, source_file):
        pass

    def _get_az_id(self, source_file):
        for id in self.az_id:
            if source_file.rfind(id):
                return id
