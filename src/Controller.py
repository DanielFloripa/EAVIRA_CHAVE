#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import timeit
import sys
import subprocess
import re
import time
import random

from DistributedInfrastructure import AvailabilityZone
from Algorithms import ksp_yen, dijkstra

"""
Class: Controller
Description: Controller is the class that manages
			what operations are performed
			Have two subclass: global and local
"""


class Controller(object):
    def __init__(self, algorithm, regions, azs, *args):
        self.main_parameters = args
        self.algorithm = algorithm
        self.regions = regions
        self.availability_zones = azs

    def get_algorithm(self):
        return self.algorithm

    def get_main_parameters(self):
        return self.main_parameters


#################################################
#######      CLASS GLOBAL CONTROLLER      #######
#################################################
class GlobalController(Controller):
    def __init__(self, datacenter, main_parameters, algorithm, *args):
        super(GlobalController, self).__init__(main_parameters, algorithm)
        self.datacenter = datacenter

    def run_test_euca(dc, helper):
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
                vm = opdict_to_vmlist(op_vm.get_id())
                if arrival_time < this_cycle:  # TODO: or (req_size < window_size):
                    this_state = op_id.split('-')[2]
                    new_host_on, off = dc.each_cycle_get_hosts_on()
                    if new_host_on > max_host_on:
                        max_host_on = new_host_on
                        logger.info(
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
                        logger.info("req_size" + str(req_size))
                    req_size_list.append(req_size)
                    req_size = 0
                    requisitions_list = []
                    break
        #        print "\t\tout: ", arrival_time, thiscycle, len(op_dict_temp.items())
        return dc, max_host_on

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
    def __init__(self, allocation, migration, replication, requisitions, violations, hosts, vm_dict):
        self.allocation = allocation
        self.migration = migration
        self.replication = replication
        self.violations = violations
        self.requisitions = requisitions
        self.hosts = hosts
        self.vm_dict = vm_dict
        # self. =

    def execute_chave(self, chave_object):
        chave_object.run()
