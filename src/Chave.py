#!/usr/bin/python
# -*- coding: utf-8 -*-

from random import randint
import math
from copy import deepcopy
from threading import Thread, RLock, current_thread, currentThread
import time
from DistributedInfrastructure import *


class Chave(object):
    global_time = 0  # type: int

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
        self.az_list = []
        self.thread_dict = dict()

    def __repr__(self):
        return repr([self.logger, self.nit, self.trigger_to_migrate,
                     self.frag_percentual, self.pm_mode, self.ff_mode,
                     self.window_size, self.window_time, self.has_overbooking,
                     self.all_vms_dict, self.all_op_dict, self.all_ha_dict, self.sla])

    def gvt(self, max):
        self.logger.info("Init GVT")
        for self.global_time in range(max):
            self.global_time += self.window_time
            #self.logger.debug(self.global_time)
            time.sleep(0.000001)
        self.logger.info("End of GVT!")


    def run(self):
        '''
        Interface for all algorithms, the name must be agnostic for all them
        :return: Void
        '''
        self.thread_dict['gvt'] = Thread(name="T_gvt", target=self.gvt, args=[99999999])
        # Creating Thread list
        for az in self.api.get_az_list():
            self.thread_dict[str(az.az_id)] = Thread(
                name="Tz_" + str(az.az_id),
                target=self.az_consolidation,
                args=[az])
        for r_id, r_obj in self.api.get_regions_d().viewitems():
            self.thread_dict[str(r_id)] = Thread(
                name="Tr_" + str(r_id),
                target=self.region_replication,
                args=[r_obj])
        # Release Threads
        for t_id, t_obj in self.thread_dict.viewitems():
            self.logger.debug("Executing thread for: %s" % (t_obj.getName()))
            t_obj.start()
            #t_obj.join(0.001)
            # Join Threads? NO!

    def az_consolidation(self, az):
        self.sla.metrics(az.az_id, "INIT", "ALL", "ZEROS")
        requisitions_queue = []
        req_size, req_size2, energy = 0, 0, 0.0
        max_host_on = 0
        vms_in_execution = OrderedDict()
        op_dict_temp = az.op_dict
        FORCE_PLACE = False
        arrival_time = 0
        # Enquanto houverem operações:
        while len(op_dict_temp.items()) > 0:
            new_host_on, off = az.each_cycle_get_hosts_on()
            if new_host_on > max_host_on:
                max_host_on = new_host_on
                self.sla.metrics(az.az_id, 'set', 'max_host_on_i', max_host_on)
                #self.max_host_on[az.az_id].append(max_host_on)
                self.logger.info("New max host on: %s at %s sec." % (max_host_on, arrival_time))
            for op_id, vm in op_dict_temp.items():
                # MIGRATE FIRST
                #            if pm == "MigrationFirst" and (chave.is_time_to_migrate(this_cycle) or dc.has_fragmentation()):
                #                dc = chave.migrate(dc)
                #                print "migrating at:", this_cycle, "with:", chave.get_last_number_of_migrations(), "migrations"
                arrival_time = vm.timestamp
                this_time = self.global_time
                if arrival_time <= this_time:
                    this_state = op_id.split('_')[1]
                    if this_state == "START":
                        requisitions_queue.append(vm)
                        req_size += 1
                        # Let's PLACE
                        if (self.is_time_to_place(this_time) or
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
                                self.logger.error("New_host_list problem: ", az.az_id)
                            del op_dict_temp[op_id]

                    elif this_state == "STOP" and vm not in requisitions_queue:  # adicionado na ultima janela
                        energy = az.get_az_energy_consumption()
                        self.sla.metrics(az.az_id, 'set', 'energy_l', energy)
                        self.sla.metrics(az.az_id, 'set', 'energy_hour_l', energy)
                        try:
                            exec_vm = vms_in_execution.pop(vm.vm_id)
                        except IndexError:
                            self.logger.error("Problem on pop vm %s executed in az %s" % (vm.vm_id, az.az_id))
                            exit(1)
                        az.deallocate_on_host(exec_vm)
                        del op_dict_temp[op_id]
                    else:
                        self.logger.error("OOOps, " + str(op_id) + " STILL IN REQ_LIST, LETS BREAK.")
                        FORCE_PLACE = True
                        break
                else:  # While there are not requisition, wait for the Thread_GVT
                    self.logger.debug("Waiting GVT at %s" % (this_time))
                    if (this_time % 3600) < 2:
                        try:
                            mean_last_hour = self.sla.metrics(az.az_id, 'avg', 'energy_hour_l', energy)
                            self.logger.critical("Media da ultima HORA:", mean_last_hour)
                            self.sla.metrics(az.az_id, 'set', 'energy_avg_l', mean_last_hour)
                            self.sla.metrics(az.az_id, 'set', 'energy_hour_l', [])
                            self.sla.metrics(az.az_id, 'add', 'total_energy_f', mean_last_hour)
                        except ZeroDivisionError:
                            self.logger.error("Zero Division at %s" % (this_time))
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
        return az, max_host_on

    def region_replication(self, region_obj):
        pass
        #print "Replicating: ", region_obj, "thrd:", current_thread().name

    def set_demand(self, demand):
        self.demand = demand
        self.all_vms_dict = demand.all_vms_dict
        self.all_op_dict = demand.all_op_dict()
        self.all_ha_dict = demand.all_ha_dict()

    def set_localcontroller(self, localcontroller):
        self.localcontroller_list = localcontroller
        for lc in localcontroller:
            print lc.lc_id
            print lc.az_list

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
            bhost, state = self.best_host(vm, az)
            if state is True:
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

    ''' OLD:
    def az_consolidation(self, az, ):
        self.sla.metrics("init", "ALL", "ZEROS", self.nit)
        requisitions_list = []
        this_cycle = self.window_time
        arrival_time = 0
        req_size, req_size2, energy = 0, 0, 0.0
        max_host_on = 0
        req_size_list = []
        op_dict_temp = self.operation_dict
        FORCE_PLACE = False
        # Se o tempo de chegada está neste ciclo, então:
        while arrival_time < this_cycle and len(op_dict_temp.items()) > 0:
            new_host_on, off = az.each_cycle_get_hosts_on()
            if new_host_on > max_host_on:
                max_host_on = new_host_on
                self.logger.info("New max host on:"+str(max_host_on)+str(off)+\
                                 "at"+str(arrival_time)+"sec.")
            for op_id, op_vm in op_dict_temp.items():
                # MIGRATE FIRST
                #            if pm == "MigrationFirst" and (chave.is_time_to_migrate(this_cycle) or dc.has_fragmentation()):
                #                dc = chave.migrate(dc)
                #                print "migrating at:", this_cycle, "with:", chave.get_last_number_of_migrations(), "migrations"
                arrival_time = op_vm.get_timestamp()
                vm = self._opdict_to_vmlist(op_vm.get_id(), az.vm_list)
                if arrival_time < this_cycle:
                    this_state = op_id.split('-')[2]
                    if this_state == "START":
                        requisitions_list.append(vm)
                        req_size += 1
                        # PLACEMENT
                        if (self.is_time_to_place(this_cycle) or self.window_size_is_full(
                                req_size)) or FORCE_PLACE is True:
                            new_host_list = self.place(requisitions_list, az.get_host_list())
                            if new_host_list is not None:
                                energy = energy + az.get_az_energy_consumption()
                                # x = metrics('add','energy_ttl',energy, None)
                                az.set_host_list(new_host_list)
                                requisitions_list = []
                                req_size = 0
                                FORCE_PLACE = False
                            else:
                                self.logger.error("New_host_list problem: " + str(new_host_list))
                            del op_dict_temp[op_id]

                    elif this_state == "STOP" and vm not in requisitions_list:  # adicionado na ultima janela
                        az.deallocate_on_host(vm)
                        del op_dict_temp[op_id]
                    else:
                        self.logger.info("OOOps, " + str(op_id) + " STILL IN REQ_LIST, LETS BREAK.")
                        FORCE_PLACE = True
                        break
                else:
                    # Enquanto não há requisições, incremente o relógio
                    while arrival_time >= this_cycle:
                        this_cycle += self.window_time
                    # print "\nNOVA FILA: ", this_cycle, "[", arrival_time, op_id.split('-')[1], "],[",
                    req_size_list.append(req_size)
                    req_size = 0
                    requisitions_list = []
                    break
            # PLACEMENT FIRST
            #        if pm == "PlacementFirst" and (chave.is_time_to_migrate(this_cycle) or dc.has_fragmentation()):
            #            dc = chave.migrate(dc)
            ##            last_host_list = dc.get_host_list()
            ##            empty_host_list = dc.create_infrastructure()
            ##            new_host_list = chave.migrate(last_host_list, empty_host_list)
            ##            dc.set_host_list(new_host_list)
            #            print "migrating at:", this_cycle, "with:", chave.get_last_number_of_migrations(), "migrations"
            self.logger.info("Final: last arrival:" + str(arrival_time) + ", lastCicle:" + str(
                this_cycle) + ", len(op_dict):" + str(len(op_dict_temp.items())))
        return az, max_host_on

    '''
