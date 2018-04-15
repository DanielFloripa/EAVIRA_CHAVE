#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from collections import OrderedDict
import random

from DistributedInfrastructure import AvailabilityZone
from Algorithms import ksp_yen, dijkstra

"""
Class: Controller
Description: Controller is the class that manages what operations are performed
Have two subclass: global and local
"""


class Controller(object):
    this_algorithm = None

    def __init__(self, regions, logger, **kwargs):
        self.main_parameters = self._get_kwargs(kwargs)
        #self.algorithm = algorithm
        self.regions = regions
        self.logger = logger
        self.metrics_dict = OrderedDict()

    def get_algorithm(self):
        #return self.algorithm
        return Controller.this_algorithm

    def _get_kwargs(self, kwargs):
        for key, value in kwargs:
            if key == "az_id":
                self.id = value
            if key == "az_id":
                self.id = value
            if key == "az_id":
                self.id = value
            if key == "az_id":
                self.id = value

    def metrics(self, command, key, value, n):  # metrics_dict{}
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
                                self.metrics_dict[k] = 0.0
                            elif x == 6:
                                self.metrics_dict[k] = []
                            elif x == 9:
                                self.metrics_dict[k] = [0 for i in range(n)]
            if command is 'set':
                if key in key_list[0:2]:
                    self.metrics_dict[key] = value
                    return True
                if key in key_list[2:8]:
                    self.metrics_dict[key].append(value)
                    return True

            if command is 'get':
                if key in key_list:
                    return self.metrics_dict[key]

            if command is 'add':
                if key in key_list[2:17]:
                    self.metrics_dict[key] = self.metrics_dict[key] + value
                    return self.metrics_dict[key]
                    # sum([v.get_vram() for v in self.virtual_machine_list])

            if command is 'resume':
                if key in key_list[2:17]:
                    return sum(values for values in self.metrics_dict[key])
                elif key in key_list[0:2]:
                    return self.metrics_dict[key]
        else:
            self.logger.error("Command (" + str(command) + ") not found!!")
        return None


#################################################
#######      CLASS GLOBAL CONTROLLER      #######
#################################################
class GlobalController(Controller):
    def __init__(self, regions_list, algorithm, demand, *kwargs):
        Controller.__init__(**kwargs)
        Controller.this_algorithm = algorithm
        self.regions_list = regions_list  # lista
        self.demand = demand  # Objeto

    def run_test_euca(self, dc, helper):
        helper.metrics("init", "ALL", "INIT", -1)
        requisitions_list = []
        this_cycle = window_time
        arrival_time = 0
        req_size = 0
        max_host_on = 0
        req_size_list = []
        op_dict_temp = operation_dict
        while (arrival_time < this_cycle) and (len(op_dict_temp.items()) > 0):
            for op_id, op_vm in op_dict_temp.items():
                arrival_time = op_vm.get_timestamp()
                vm = self._opdict_to_vmlist(op_vm.get_id())
                if arrival_time < this_cycle:  # TODO: or (req_size < window_size):
                    this_state = op_id.split('-')[2]
                    new_host_on, off = dc.each_cycle_get_hosts_on()
                    if new_host_on > max_host_on:
                        max_host_on = new_host_on
                        self.logger.info(
                            "New max host on: " + str(max_host_on) + str(off) + " at " + str(arrival_time) + " sec.")
                    if this_state == "START":
                        if dc.allocate_on_host(vm):
                            requisitions_list.append(vm)
                            req_size += 1
                    elif this_state == "STOP":
                        dc.deallocate_on_host(vm)
                    # Remova do dict temporario
                    del op_dict_temp[op_id]
                else:
                    # Enquanto não há requisições, incremente o relógio
                    while arrival_time >= this_cycle:
                        this_cycle += window_time
                    if req_size >= window_size:
                        self.logger.info("req_size" + str(req_size))
                    req_size_list.append(req_size)
                    req_size = 0
                    requisitions_list = []
                    break
        #        print "\t\tout: ", arrival_time, thiscycle, len(op_dict_temp.items())
        return dc, max_host_on

    def _opdict_to_vmlist(id, vm_list):
        for vm_temp in vm_list:
            if vm_temp.get_id() == id:
                return vm_temp
        return None

    def reallocate_infrastructure_mm(self):
        self.datacenter.reallocate_infrastructure_mm()

    def execute_elasticity(self, delete_requests, recfg_requests, repl_requests, offline):
        repl_requests_count = 0
        recfg_requests_count = 0
        delete_requests_count = 0

        new_delete_requests = []
        for delete in delete_requests:
            delete_requests_count += 1
            vi = self.datacenter.get_vi(delete['vi'])
            if vi != -1:
                new_vnode = vi.get_virtual_resource(delete['vnode'])
                if new_vnode != -1:
                    new_delete_requests.append(new_vnode)
        self.datacenter.answer_delete_requests(new_delete_requests)

        new_recfg_requests = []
        for recfg in recfg_requests:
            recfg_requests_count += 1
            vi = self.datacenter.get_vi(recfg['vi'])
            if vi != -1:
                new_vnode = vi.get_virtual_resource(recfg['vnode'])
                if new_vnode != -1:
                    recfg['vnode'] = new_vnode
                    new_recfg_requests.append(recfg)

        new_repl_requests = []
        for repl in repl_requests:
            repl_requests_count += 1
            vi = self.datacenter.get_vi(repl['vi'])
            if vi != -1:
                new_vnode = vi.get_virtual_resource(repl['vnode'])
                if new_vnode != -1:
                    new_repl_requests.append(new_vnode)

        # call MM, MBFD and Buyya solutions
        self.datacenter.answer_reconfiguration_requests_mbfd(new_recfg_requests)
        self.datacenter.answer_replication_requests_mbfd(new_repl_requests)

    def choose_config(self, virtual_folder):
        # Choose a random virtual file
        virtual_files = os.listdir(virtual_folder)
        return virtual_folder + virtual_files[random.randint(0, len(virtual_files) - 1)]

    def execute_mbfd(self, vi):
        return self.datacenter.mbfd(vi)

    def get_datacenter(self):
        return self.datacenter


#################################################
#######       CLASS LOCAL CONTROLLER      #######
#################################################
class LocalController(Controller):
    def __init__(self, azs, algorithm, migration, replication, requisitions, violations, hosts, vm_dict, *args):
        Controller.__init__(*args)
        self.availability_zones = azs
        self.algorithm = algorithm
        self.vm_dict = vm_dict
        # self. =

    def __repr__(self):
        return repr(self)

    def execute_chave(self, chave_object):
        chave_object.run()

    def
