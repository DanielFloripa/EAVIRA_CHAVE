#!/usr/bin/python
# -*- coding: utf-8 -*-

from random import randint
import math
from copy import deepcopy
from threading import Thread, RLock, current_thread, currentThread
from collections import OrderedDict
import time
from DistInfra import *


class Chave(object):
      # type: int

    def __init__(self, api):
        self.api = api
        self.sla = api.sla
        self.logger = api.sla.g_logger()
        self.nit = api.sla.g_nit()
        self.trigger_to_migrate = api.sla.g_trigger_to_migrate()
        self.frag_percentual = api.sla.g_frag_percentual()
        self.pm_mode = api.sla.g_pm()
        self.ff_mode = api.sla.g_ff()
        self.window_time = api.sla.g_window_time()
        self.window_size = api.sla.g_window_size()
        self.has_overbooking = api.sla.g_has_overbooking()
        self.last_number_of_migrations = 0
        # self.operation_dict = sla.g_op_dict()
        self.dbg = []  # "overb", "migr", "probl", "ok"]
        self.demand = None
        self.localcontroller_list = []
        self.region_list = None
        self.all_vms_dict = dict()
        self.all_op_dict = dict()
        self.all_ha_dict = dict()
        self.thread_dict = dict()
        self.replicas_dict = OrderedDict()
        self.az_list = []
        self.global_hour = -1
        self.global_time = -1
        self.buffer_replicas_dict = OrderedDict()
        self.executing_replicas_dict = OrderedDict()

    def __repr__(self):
        return repr([self.logger, self.nit, self.trigger_to_migrate,
                     self.frag_percentual, self.pm_mode, self.ff_mode,
                     self.window_size, self.window_time, self.has_overbooking,
                     self.all_vms_dict, self.all_op_dict, self.all_ha_dict, self.sla])

    def gvt(self, max):
        self.logger.info("Init GVT in %s to %s" %
                         (self.global_time, self.api.demand.max_timestamp))
        while self.global_time < self.api.demand.max_timestamp + 1:
            self.global_time += self.window_time
            if self.global_time % 60 == 0:
                time.sleep(0.001)
            if self.global_time % 3600 == 0:
                self.global_hour += 1
                self.logger.debug("GVT s:%s, h:%s" % (self.global_time, self.global_hour))
                time.sleep(0.01)
        self.logger.info("End of GVT!")


    def run(self):
        '''
        Interface for all algorithms, the name must be agnostic for all them
        :return: Void
        '''
        self.thread_dict['gvt'] = Thread(name="T_gvt", target=self.gvt, args=[0])
        # Creating Thread list
        for az in self.api.get_az_list():
            self.thread_dict[str(az.az_id)] = Thread(
                name="Tz_" + str(az.az_id),
                target=self.az_consolidation,
                args=[az])
        for lc_id, lc_obj in self.api.get_localcontroller_d().viewitems():
            self.thread_dict[str(lc_id)] = Thread(
                name="Tr_" + str(lc_id),
                target=self.region_replication,
                args=[lc_obj])
        # Release Threads
        for t_id, t_obj in self.thread_dict.viewitems():
            self.logger.debug("Executing thread for: %s" % (t_obj.getName()))
            t_obj.start()
            #t_obj.join(0.1)
            # Join Threads? NO!

    def az_consolidation(self, az):
        requisitions_queue = []
        req_size, req_size2, energy = 0, 0, 0.0
        max_host_on = 0
        vms_in_execution = OrderedDict()
        op_dict_temp = az.op_dict
        FORCE_PLACE = False
        arrival_time = 0
        # Enquanto houverem operações:
        while len(op_dict_temp.items()) > 0:
            for op_id, vm in op_dict_temp.items():
                # MIGRATE FIRST
                #            if pm == "MigrationFirst" and (chave.is_time_to_migrate(this_cycle) or dc.has_fragmentation()):
                #                dc = chave.migrate(dc)
                #                print "migrating at:", this_cycle, "with:", chave.get_last_number_of_migrations(), "migrations"
                if (self.global_time % 3600) == 0:
                    self.resume_energy_hour(az)

                new_host_on, off = az.each_cycle_get_hosts_on()
                if new_host_on > max_host_on:
                    max_host_on = new_host_on
                    self.sla.metrics(az.az_id, 'set', 'max_host_on_i', max_host_on)
                    self.logger.info("New max host on: {0} at {1} sec".format(max_host_on, arrival_time))

                arrival_time = vm.timestamp
                if arrival_time <= self.global_time:
                    this_state = op_id.split('_')[1]
                    if this_state == "START":
                        requisitions_queue.append(vm)
                        req_size += 1

                        # Let's PLACE
                        if (self.is_time_to_place(self.global_time) or
                            self.window_size_is_full(req_size)) or \
                            FORCE_PLACE is True:
                            if self.place(requisitions_queue, az):
                                vms_in_execution[vm.vm_id] = vm
                                # TODO: We measure energy consumption on each placement
                                # May be on each cycle?
                                energy = az.get_az_energy_consumption()
                                self.sla.metrics(az.az_id, 'set', 'energy_l', energy)
                                self.sla.metrics(az.az_id, 'set', 'energy_hour_l', energy)
                                requisitions_queue = []
                                req_size = 0
                                FORCE_PLACE = False
                            else:
                                self.logger.error("Problem on place queue: {0}".format(requisitions_queue))
                            del op_dict_temp[op_id]

                    elif this_state == "STOP" and vm not in requisitions_queue:  # não adicionado na ultima janela
                        try:
                            exec_vm = vms_in_execution.pop(vm.vm_id)
                        except IndexError or KeyError:
                            self.logger.error("Problem on pop vm {0}".format(vm.vm_id))
                            exit(1)
                        energy = az.get_az_energy_consumption()
                        self.sla.metrics(az.az_id, 'set', 'energy_l', energy)
                        self.sla.metrics(az.az_id, 'set', 'energy_hour_l', energy)
                        az.deallocate_on_host(exec_vm)
                        del op_dict_temp[op_id]
                    else:
                        self.logger.error("OOOps, DIVERGENCE between {0} and {1} ".format(this_state, op_id))
                        FORCE_PLACE = True
                        break
                else:  # While there are not requisition, wait for the Thread_GVT
                    #self.logger.debug("Waiting GVT at %s" % (self.global_time))
                    requisitions_queue = []
                    req_size = 0
                    break
            # PLACEMENT FIRST
            #        if pm == "PlacementFirst" and (chave.is_time_to_migrate(this_cycle) or dc.has_fragmentation()):
            #            dc = chave.migrate(dc)
            ##            last_host_list = dc.get_host_list()
            ##            empty_host_list = dc.create_infrastructure()
            ##            new_host_list = chave.migrate(last_host_list, empty_host_list)
            ##            dc.set_host_list(new_host_list)
            #            print "migrating at:", this_cycle, "with:", chave.get_last_number_of_migrations(), "migrations"
            ##with self.reentrant_lock:
                ##self.logger.info("Last arrival:" + str(arrival_time) + ", lastCicle:" + str(
                #    self.global_time) + ", len(op_dict):" + str(len(op_dict_temp.items())))
        time.sleep(5)

    def region_replication(self, lc_obj):
        if len(lc_obj.get_oredered_replicas_dict()) > 0:
            self.buffer_replicas_dict[lc_obj.get_id()] = lc_obj.get_oredered_replicas_dict()


    def resume_energy_hour(self, az):
        mean_last_hour = self.sla.metrics(az.az_id, 'avg', 'energy_hour_l')
        if mean_last_hour is False:
            return False
        self.logger.info("Media da ultima HORA: {0} at {1}h or {2}".format(
            mean_last_hour, self.global_hour, self.global_time))
        self.sla.metrics(az.az_id, 'set', 'energy_avg_l', mean_last_hour)
        self.sla.metrics(az.az_id, 'set', 'energy_hour_l', 0)
        self.sla.metrics(az.az_id, 'add', 'total_energy_f', mean_last_hour)
        return True

    def set_demand(self, demand):
        self.demand = demand
        self.all_vms_dict = demand.all_vms_dict
        self.all_op_dict = demand.all_op_dict()
        self.all_ha_dict = demand.all_ha_dict()

    def set_localcontroller(self, localcontroller):
        self.localcontroller_list = localcontroller
        for lc in localcontroller:
            print (lc.lc_id, lc.az_list)

    def _opdict_to_vmlist(self, id, this_vm_list):
        for vm_temp in this_vm_list:
            if vm_temp.get_id() == id:
                return vm_temp
        return None

    def order_ff_mode(self, host_list):
        if self.ff_mode == "FFD2I":  # crescente
            host_list.sort(key=lambda e: e.cpu)
        elif self.ff_mode == "FF3D":  # decrescente
            host_list.sort(key=lambda e: e.cpu, reverse=True)
        return host_list  # se nenhuma configuração

    def best_host(self, vm, az):

        for host in az.host_list:
            if host.cpu >= vm.get_vcpu() and host.ram >= vm.get_vram():
                self.logger.info("Best host for %s (vcpu:%s) is %s (cpu:%s). ovbCount:%s, tax:%s hasOvb? %s." %
                                      (vm.get_id(), vm.get_vcpu(), host.get_id(), host.cpu, host.overb_count,
                                       host.actual_overb, host.has_overbooking))
                return host, True
            else:
                if self.has_overbooking and host.can_overbooking(vm):
                    self.logger.info("Overb for %s (vcpu:%s), is %s (cpu:%s). Overb cnt:%s, actual:%s, has:%s." %
                                          (vm.get_id(), vm.get_vcpu(), host.get_id(), host.cpu,
                                          host.overb_count, host.actual_overb, host.has_overbooking))
                    host.do_overbooking(vm)
                    return host, True
        self.logger.error("PROBLEM: not found best host in len:%s for place %s. Try a new host" %
                         (len(az.host_list), vm.get_id()))
        if self.api.create_new_host(az.az_id):
            for host in az.host_list:
                if host.cpu >= vm.get_vcpu() and host.ram >= vm.get_vram():
                    self.logger.info("After new host, for %s (vcpu:%s) is %s (cpu:%s). ovbCount:%s, tax:%s hasOvb? %s." %
                                  (vm.get_id(), vm.get_vcpu(), host.get_id(), host.cpu, host.overb_count,
                                   host.actual_overb, host.has_overbooking))
                return host, True
            #self.best_host(vm, host_list)
        return None, False

    def place(self, vm_list, az):
        vm_list.sort(key=lambda e: e.get_vcpu(), reverse=True)  # decrescente
        #host_ff_mode = az.get_host_list()  # TODO: ver se e necessario: self.order_ff_mode(az.host_list)
        for vm in vm_list:
            bhost, is_ok = self.best_host(vm, az)
            if is_ok is True:
                vm.set_host_id(bhost.host_id)
                self.logger.debug("Allocating %s in %s" % (vm.vm_id, vm.host_id))
                if bhost.allocate(vm):
                    return True  # host_ff_mode.append(bhost)
                else:
                    self.logger.error("Problem on allocate at placement")
                    return False
        return True

    def migrate(self, az):
        vm_list_to_migrate = []

        new_az = AvailabilityZone(az.get_azNodes(), az.get_azCores(), az.get_availability(),
                                  az.get_id(), az.get_azRam(), az.algorithm,
                                  az.has_overbooking)
        # Criando a lista com todas as mvs em execução:
        for eachHost in az.get_host_list():
            for vm in eachHost.get_virtual_resources():
                # TODO porque 'migrate?' Marcacao Transitoria
                vm.set_physical_host("migrate")
                vm_list_to_migrate.append(vm)

        # Aplicando o ordenação decrescente:
        vm_list_to_migrate.sort(key=lambda e: e.get_vcpu(), reverse=True)

        for vm in vm_list_to_migrate:
            ##with self.reentrant_lock:
            self.logger.info("Next vm: " + str(vm.get_id()))
            for eachHost in new_az.get_host_list():
                if new_az.allocate_on_host(vm):
                    self.last_number_of_migrations += 1
                    break
                else:
                    self.last_number_of_migrations -= 1
                    ##with self.reentrant_lock:
                    self.logger.error("PROBLEM ON MIGRATE after overbooking" + \
                                          str(vm.get_id()) + str(eachHost.get_id()) + \
                                          str(eachHost.overb_count))
        return new_az

    def get_last_number_of_migrations(self):
        ret = self.last_number_of_migrations
        self.last_number_of_migrations = 0
        return ret

    def is_time_to_migrate(self, time):
        if time % self.trigger_to_migrate == 0:
            return True
        return False

    def is_time_to_place(self, cicle):
        if cicle % self.window_time == 0:
            return True
        return False

    def window_size_is_full(self, req_size):
        if req_size >= self.window_size:
            return True
        return False

    def alocate_vm_list_on_dc(self, vm_list):
        pass

    def dealocate_vm_list_on_dc(self, vm_list):
        pass

