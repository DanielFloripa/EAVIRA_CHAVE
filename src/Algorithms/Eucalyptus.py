#!/usr/bin/python
# -*- coding: utf-8 -*-

import threading
import time
import math
from Users.SLAHelper import *


class Eucalyptus(object):
    def __init__(self, api):
        self.api = api
        self.sla = api.sla
        self.logger = api.sla.g_logger()
        self.nit = api.sla.g_nit()
        self.trigger_to_migrate = api.sla.g_trigger_to_migrate()
        self.frag_percent = api.sla.g_frag_class()
        self.ff_mode = api.sla.g_ff()
        self.window_time = api.sla.g_window_time()
        self.last_number_of_migrations = 0
        self.demand = None
        self.localcontroller_list = []
        self.region_list = None
        self.all_vms_dict = dict()
        self.all_op_dict = dict()
        self.all_ha_dict = dict()
        self.az_list = []
        self.global_hour = 0
        self.global_time = 0
        self.global_energy = 0
        self.exceptions = False
        self.has_operation_this_time = dict()
        self.replicas_execution_d = dict()
        """d['lc_id']['pool_id'] = obj"""
        self.replication_pool_d = dict()
        """d['lc_id']['lcid_azid_vmid'] = {'critical':[AZc, VMc], 'replicas':[[AZr1,VMr1],[...], [AZrn,VMrn]]}"""
        self.req_size_d = dict()
        self.energy_global_d = dict()
        self.max_host_on_d = dict()
        self.vms_in_execution_d = dict()
        self.op_dict_temp_d = dict()  # az.op_dict
        self.is_init_d = self.__init_dicts()

    def __repr__(self):
        return repr([self.logger, self.nit, self.trigger_to_migrate,
                     self.frag_percent, self.ff_mode, self.window_time, self.all_vms_dict,
                     self.all_op_dict, self.all_ha_dict, self.sla])

    #############################################
    ### Initial and basics
    #############################################
    def __init_dicts(self):
        self.az_list = self.api.get_az_list()
        for az in self.az_list:
            self.req_size_d[az.az_id] = 0
            self.energy_global_d[az.az_id] = 0.0
            self.max_host_on_d[az.az_id] = 0
            self.vms_in_execution_d[az.az_id] = dict()
            self.op_dict_temp_d[az.az_id] = dict(az.op_dict)
            self.has_operation_this_time[az.az_id] = False

        for lc_id, lc_obj in self.api.get_localcontroller_d().items():
            self.localcontroller_list.append(lc_obj)
            self.replicas_execution_d[lc_id] = dict()
            self.replication_pool_d[lc_id] = dict()
        return True

    def run(self):
        """
        Interface for all algorithms, the name must be agnostic for all them
        In this version, we use Threads for running infrastructures in parallel
        :return: Void
        """
        # for az in self.api.get_az_list():
        #    az.create_infra(first_time=True, host_state=HOST_ON)

        start = time.time()
        while self.global_time <= self.api.demand.max_timestamp:
            for az in self.api.get_az_list():
                self.placement(az)

                values = (self.global_time, az.get_az_energy_consumption2(), "",)
                self.sla.metrics.set(az.az_id, 'energy_l', values)

                azl1, azl2 = az.get_az_load()
                values = (self.global_time, azl2, str(azl1),)
                self.sla.metrics.set(az.az_id, 'az_load_l', values)

            if self.global_time % 10000 == 0:
                memory = self.sla.check_simulator_memory()
                elapsed = time.time() - start
                self.logger.critical("gt: {} , time:{} , it toke: {:.3f}s, {}".format(
                    self.global_time, time.strftime("%H:%M:%S"), elapsed, memory))
                self.sla.metrics.set('global', 'lap_time_l', (self.global_time, elapsed, "Status:{}".format(memory)))
                start = time.time()
            self.global_time += self.window_time

    def placement(self, az):
        az_id = az.az_id
        remaining_operations_for_this_az = dict(self.op_dict_temp_d[az_id])
        for op_id, vm in remaining_operations_for_this_az.items():
            if vm.timestamp <= self.global_time:
                self.has_operation_this_time[az_id] = True
                this_state = op_id.split(K_SEP)[1]
                if this_state == "START":
                    ''' Let's PLACE!'''
                    if az.allocate_on_host(vm, vm.host_id):
                        self.vms_in_execution_d[az_id][vm.vm_id] = vm
                    else:
                        del self.op_dict_temp_d[az_id][vm.vm_id + "_START"]
                        del self.op_dict_temp_d[az_id][vm.vm_id + "_STOP"]
                        # Note: Must match columns_d:
                        this_metric = {'gvt': self.global_time,
                                       'val_0': 0,
                                       'info': "{}, host:{}. {}".format(
                                           vm.vm_id, vm.host_id, az.print_hosts_distribution(level='Min'))}
                        self.sla.metrics.set(az_id, 'reject_l', tuple(this_metric.values()))
                        self.logger.error("{}\tReject {} {} at gt:{}".format(az_id, vm.vm_id, vm.host_id, self.global_time))
                        break
                    del self.op_dict_temp_d[az_id][vm.vm_id + "_START"]
                elif this_state == "STOP":
                    exec_vm = None
                    try:
                        exec_vm = self.vms_in_execution_d[az_id].pop(vm.vm_id)
                    except IndexError:
                        self.logger.error("{}\t Problem INDEX on pop vm {}".format(az_id, vm.vm_id))
                    except KeyError:
                        self.logger.error("{}\t Problem KEY on pop vm {} {}".format(az_id, vm.vm_id, exec_vm))
                    else:
                        if exec_vm is not None:
                            if az.deallocate_on_host(exec_vm, ts=vm.timestamp):
                                del self.op_dict_temp_d[az_id][op_id]
                            else:
                                self.logger.error("{}\t Problem for deallocate {}".format(az_id, exec_vm.vm_id))
                        else:
                            self.logger.error("{}\t Problem for deallocate: VM is None. Original {}".format(az_id, vm))
                else:
                    self.logger.error("{}\t OOOps, DIVERGENCE between {} and {} ".format(az_id, this_state, op_id))
                    continue
        # OUT!









