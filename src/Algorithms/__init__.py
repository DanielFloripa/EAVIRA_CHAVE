#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
from collections import OrderedDict

from Architecture.Controller import *


class BaseAlgorithm:
    def __init__(self, api: GlobalController) -> None:
        self.api = api
        self.sla = api.sla
        self.logger = api.sla.g_logger()
        self.nit = api.sla.g_nit()
        self.trigger_to_migrate = api.sla.g_trigger_to_migrate()
        self.frag_percent = api.sla.g_frag_class()
        self.ff_mode = api.sla.g_ff()
        self.window_time = api.sla.g_window_time()
        self.last_ts_d = sorted(api.demand.last_ts_d.items(), key=self.sla.key_from_item(lambda k, v: (v, k)))
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
        self.az_load_change_d = dict()
        self.is_init_d = self.__init_dicts()

    def __repr__(self):
        return repr([self.logger, self.nit, self.trigger_to_migrate,
                     self.frag_percent, self.ff_mode, self.window_time, self.all_vms_dict,
                     self.all_op_dict, self.all_ha_dict, self.sla])

    #
    # Initial and basics
    #
    def __init_dicts(self):
        self.az_list = self.api.get_az_list()
        for az in self.az_list:
            self.az_load_change_d[az.az_id] = 0.0
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
        In this version, we run the infrastructures in in serial mode
        :return:
        """
        start = time.time()
        milestones = int(self.api.demand.max_timestamp / self.sla.g_milestones())
        while self.global_time <= self.api.demand.max_timestamp:
            for az in self.api.get_az_list():
                self.placement(az)
                values = (self.global_time, az.get_az_energy_consumption2(), "",)
                self.sla.metrics.set(az.az_id, 'energy_l', values)
                azload = az.get_az_load()
                values = (self.global_time, azload, str(az.print_hosts_distribution(level='MIN')),)
                self.sla.metrics.set(az.az_id, 'az_load_l', values)

            if self.global_time % milestones == 0:
                memory = self.sla.check_simulator_memory()
                elapsed = time.time() - start
                self.logger.critical("gt: {} , time:{} , it toke: {:.3f}s, {}".format(
                    self.global_time, time.strftime("%H:%M:%S"), elapsed, memory))
                self.sla.metrics.set('global', 'lap_time_l', (self.global_time, elapsed, "Status:{}".format(memory)))
                start = time.time()
            self.remove_finished_azs()
            # At the end, increment the clock:
            self.global_time += self.window_time

    def remove_finished_azs(self):
        """
        Note: This will remove the AZ that had its last operation
        :return: None
        """
        if self.global_time >= self.last_ts_d[0][1]:
            azid = self.last_ts_d[0][0]
            new_az_list = list(self.az_list)
            for az in new_az_list:
                if az.az_id == azid:
                    del self.last_ts_d[0]
                    self.az_list.remove(az)
                    self.logger.critical("{}\t has nothing else! Deleted at {}, remain {}".format(
                        azid, self.global_time, len(self.az_list)))

    def placement(self, az):
        az_id = az.az_id
        remaining_operations_for_this_az = dict(self.op_dict_temp_d[az_id])
        for op_id, vm in remaining_operations_for_this_az.items():
            if vm.timestamp <= self.global_time:
                self.has_operation_this_time[az_id] = True
                this_state = op_id.split(K_SEP)[1]
                if this_state == "START":
                    # Allocate:
                    del self.op_dict_temp_d[az_id][op_id]
                elif this_state == "STOP":
                    # Dealocate:
                    del self.op_dict_temp_d[az_id][op_id]
                else:
                    self.logger.error("{}\t OOOps, DIVERGENCE between {} and {} ".format(az_id, this_state, op_id))
                    continue
        # OUT!

    def set_rejection_for(self, procedure, code, info, lc_id, pool_id, az_id, vm_id):
        # Doc: `code` is 0, 1, 2, 3 or 5
        try:
            if procedure == "replication":
                # Após ocorrer a rejeição, remova o pool do dicionário
                del self.replication_pool_d[lc_id][pool_id]
            elif procedure == "placement":
                # Após ocorrer a rejeição, remova as vms start e stop do dicionário
                del self.op_dict_temp_d[az_id][vm_id + "_START"]
                del self.op_dict_temp_d[az_id][vm_id + "_STOP"]
                if pool_id in self.replicas_execution_d[lc_id].keys():
                    del self.replicas_execution_d[lc_id][pool_id]
                    code = 1
            elif procedure == "add_new_host":
                pass
            else:
                self.logger.error("{}\t Rejection procedure incorrect! in code {}".format(az_id, code))
                exit(10)
        except Exception as e:
            self.logger.exception(e)
            pass
        # Note: this_metric must match columns_d:
        this_metric = {'gvt': self.global_time,
                       'val_0': code,
                       'info': "pool:{}, {}".format(pool_id, info)}
        self.sla.metrics.set(az_id, 'reject_l', tuple(this_metric.values()))
        self.sla.metrics.update(az_id, "vm_history", "reject_code", code, "vm_id", vm_id)
        self.logger.warning("{}\t Problem to place {} az:{} at {}, metric: {}".format(
                pool_id, vm_id, az_id, self.global_time, this_metric.items()))
