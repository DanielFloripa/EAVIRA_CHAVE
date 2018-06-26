#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CHAVE-Sim: The simulator for research based in clouds architecture
    CHAVE: Consolidation with High Availability on virtualyzed environments
"""

import sys
from Architecture.Resources.Virtual import *
from Users.SLAHelper import *


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
        self.all_vms_dict = dict()  # Dicionaario de listas
        self.all_operations_dicts = dict()  # Dicionario de dicionarios
        self.all_ha_dicts = dict()  # Dicionario de dicionarios
        self.max_timestamp = 0
        self.last_ts_d = dict()
        self.ha_only_dict = dict()

    def __repr__(self):
        return repr([self.sla, self.logger, self.algorithm,
                     self.az_id, self.number_of_azs, self.vmRam_default,
                     self.all_vms_dict, self.all_operations_dicts, self.all_ha_dicts])

    def obj_id(self):  # Return the unique hexadecimal footprint from each object
        return str(self).split(' ')[3].split('>')[0]

    def last_timestamps_d_ordered(self):
        return sorted(self.last_ts_d.items(), key=self.sla.key_from_item(lambda k, v: (v, k)))

    def get_demand_from_az(self, az_id):
        return self.all_vms_dict[az_id], \
               self.all_operations_dicts[az_id], \
               self.all_ha_dicts[az_id]

    def create_vms_from_sources(self):
        for i, source_file in enumerate(self.list_of_source_files):
            azid = self.az_id[i]
            self.all_vms_dict[azid], \
            self.all_operations_dicts[azid], \
            self.all_ha_dicts[azid] = self._get_vms_from_source(source_file)

    def __get_availab_from_source(self, source_file):
        locked_case = self.sla.g_lock_case()
        is_enabled_repl = self.sla.g_enable_replication()
        if locked_case == 'True':
            lock = True
        elif locked_case == 'False':
            lock = False
        else:
            lock = ""
        av_source_file = source_file.split(".txt")[0] + "-plus.txt"
        av_demand_dict, lock_dict = dict(), dict()
        with open(av_source_file, "r") as source:
            av_demand_dict['this_az'] = float(source.readline())
            for demand in source:
                demand = demand.split()
                #  ha_ts = demand[0]  # <- not used!
                vm_id = demand[1]

                if is_enabled_repl:
                    av_demand_dict[vm_id] = float(demand[2])
                else:
                    av_demand_dict[vm_id] = av_demand_dict['this_az']

                if locked_case == 'RANDOM':
                    lock = eval(demand[3])
                lock_dict[vm_id] = lock
        return av_demand_dict, lock_dict

    def _get_vms_from_source(self, source_file):
        """
        :param source_file: one source file, refer to all demand from one AZ
        :return:    operations_dict --> a ordered dictionary with all operations (create/destroy)
                    vms_list --> a list with all VMs objects to instance
        """
        availab_dict, lock_dict = self.__get_availab_from_source(source_file)
        operations_dict = OrderedDict()
        vms_list = []
        for_testing_vm_list = []
        line = 0
        av_az = availab_dict['this_az']
        az_id = self._get_this_az_id(source_file)
        with open(source_file, 'r') as source:
            for operation in source:
                line = line + 1
                operation = operation.split()
                state = str(operation[0])
                timestamp = int(operation[1])
                this_vm_id = str(operation[2])
                op_id = str(this_vm_id + K_SEP + state)
                av_vm = availab_dict[this_vm_id]
                lock = lock_dict[this_vm_id]
                if self.sla.is_required_ha(av_vm, av_az):
                    vtype = CRITICAL
                else:
                    vtype = REGULAR

                if state == "START":
                    if self.algorithm == "CHAVE":
                        host = "None"
                    else:
                        host = str(operation[3])  # Use the default allocation from EUCA_files

                    vcpu = int(operation[4])
                    vram = self.vmRam_default * vcpu
                    lifetime = 0
                    vm = VirtualMachine(this_vm_id, vcpu, vram, av_vm, vtype, host, az_id,
                                        timestamp, lifetime, lock, self.logger)
                    vms_list.append(vm)
                    for_testing_vm_list.append(vm)
                    operations_dict[op_id] = vm
                    if vtype is CRITICAL:
                        self.ha_only_dict[this_vm_id] = vm

                elif state == "STOP":
                    last_op_id = str(this_vm_id + '_START')
                    vm_to_stop = operations_dict[last_op_id]
                    lifetime2 = 0
                    try:
                        lifetime2 = timestamp - int(vm_to_stop.timestamp)
                        vm_to_stop.lifetime = lifetime2
                    except Exception as e:
                        self.logger.exception(type(e))
                        self.logger.error("Problem on {} 'lifetime': {} {} {} \n {}".format(
                            last_op_id, lifetime2, timestamp, vm_to_stop.timestamp, sys.exc_info()[0]))
                    host = vm_to_stop.get_host_id()
                    vcpu = vm_to_stop.get_vcpu()
                    vram = vm_to_stop.get_vram()

                    vm = VirtualMachine(this_vm_id, vcpu, vram, av_vm, vtype, host, az_id,
                                        timestamp, lifetime2, lock, self.logger)

                    operations_dict[op_id] = vm
                    try:
                        vmindex = for_testing_vm_list.index(vm_to_stop)
                        for_testing_vm_list.pop(vmindex)
                    except Exception as e:
                        self.logger.exception(type(e))
                        self.logger.error("On pop VM from {} \n {}".format(op_id, sys.exc_info()[0]))
            # Note: Se tiver algo, entao sobrou alguma vm
            if for_testing_vm_list:
                self.logger.error("At the end of demand, we already have VMs: {}".format(for_testing_vm_list))
                exit(1)
                # Note: Get the last timestamp from loop and record the biggest
            self.last_ts_d[az_id] = timestamp
            if self.max_timestamp < timestamp:
                self.max_timestamp = timestamp
                # self.logger.debug("New Max Timestamp: {} found in {}".format(self.max_timestamp, az_id))
        return vms_list, operations_dict, availab_dict

    # TODO: criar para GVT
    def get_vms_from_gvt(self, source_file):
        pass

    def _get_this_az_id(self, source_file):
        for id in self.az_id:
            if source_file.rfind(id) > 0:
                return id

        for p in self.sla.auto_az_id_parse:
            if source_file.rfind(p['FILE']) > 0:
                return p['AUTO']
        self.logger.error("Not found AZ_ID from source_file {}".format(source_file))
        exit(0)

    def define_host_for_vm(self):
        pass
