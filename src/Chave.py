#!/usr/bin/python
# -*- coding: utf-8 -*-

from random import randint
import math
from copy import deepcopy
from threading import Thread, RLock
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
        self.localcontroller_list = None
        self.region_list = None
        self.all_vms_dict = dict()
        self.all_op_dict = dict()
        self.all_ha_dict = dict()
        self.az_list = []
        self.thread_list = []
        self.some_rlock = RLock()

    def __repr__(self):
        return repr([self.logger, self.nit, self.trigger_to_migrate,
                     self.frag_percentual, self.pm_mode, self.ff_mode,
                     self.window_size, self.window_time, self.has_overbooking,
                     self.all_vms_dict, self.all_op_dict, self.all_ha_dict, self.sla])

    def run(self):
        self.threaded_gvt()

    def gvt(self, max):
        print "Init GVT"
        for self.global_time in range(max):
            self.global_time += self.window_time
            time.sleep(0.001)

    def threaded_gvt(self):
        '''
        Interface for all algorithms, the name must be agnostic for all them
        :return: Void
        '''
        gvt = Thread(target=self.gvt, args=[99999999])
        gvt.start()
        arrival_time = 0
        this_cycle = self.window_time
        #        while arrival_time < self.global_time:

        for az in self.api.get_az_list():
            self.thread_list[str(az.az_id)] = Thread(
                name="cons_" + str(az.az_id),
                target=self.az_consolidation,
                args=[az])
            self.thread_list.get(str(az.az_id)).start()
            self.thread_list.get(str(az.az_id)).join(2)
            # consolida = Thread(target=self.az_consolidation(), args=[az])
            print "AZ THREAD: ", self.thread_list.get(str(az.az_id)).getName()
            ha_regions = Thread(target=self.ha_in_regions(), args=[0])
            ha_global = Thread(target=self.ha_global(), args=[0])
        # for region in self.api.get

    def az_consolidation(self, az):
        self.sla.metrics("init", "ALL", "ZEROS", self.nit)
        requisitions_list = []
        req_size, req_size2, energy = 0, 0, 0.0
        max_host_on = 0
        req_size_list = []
        op_dict_temp = self.operation_dict
        FORCE_PLACE = False
        # Se o tempo de chegada está neste ciclo, então:
        while len(op_dict_temp.items()) > 0:
            new_host_on, off = az.each_cycle_get_hosts_on()
            if new_host_on > max_host_on:
                max_host_on = new_host_on
                with self.some_rlock: self.logger.info(
                    "New max host on:" + str(max_host_on) + "at" + str(arrival_time) + "sec.")
            for op_id, op_vm in op_dict_temp.items():
                # MIGRATE FIRST
                #            if pm == "MigrationFirst" and (chave.is_time_to_migrate(this_cycle) or dc.has_fragmentation()):
                #                dc = chave.migrate(dc)
                #                print "migrating at:", this_cycle, "with:", chave.get_last_number_of_migrations(), "migrations"
                arrival_time = op_vm.get_timestamp()
                vm = self._opdict_to_vmlist(op_vm.get_id(), az.vm_list)
                if arrival_time < self.global_time:
                    this_state = op_id.split('-')[2]
                    if this_state == "START":
                        requisitions_list.append(vm)
                        req_size += 1
                        # PLACEMENT
                        if (self.is_time_to_place(self.global_time) or self.window_size_is_full(
                                req_size)) or FORCE_PLACE is True:
                            new_host_list = self.place(requisitions_list, az.get_host_list())
                            if new_host_list is not None:
                                energy = energy + az.get_total_energy_consumption()
                                # x = metrics('add','energy_ttl',energy, None)
                                az.set_host_list(new_host_list)
                                requisitions_list = []
                                req_size = 0
                                FORCE_PLACE = False
                            else:
                                with self.some_rlock:
                                    self.logger.error("New_host_list problem: " + str(new_host_list))
                            del op_dict_temp[op_id]

                    elif this_state == "STOP" and vm not in requisitions_list:  # adicionado na ultima janela
                        az.deallocate_on_host(vm)
                        del op_dict_temp[op_id]
                    else:
                        with self.some_rlock:
                            self.logger.info("OOOps, " + str(op_id) + " STILL IN REQ_LIST, LETS BREAK.")
                        FORCE_PLACE = True
                        break
                else:
                    # Enquanto não há requisições, incremente o relógio
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
            with self.some_rlock:
                self.logger.debug("Final: last arrival:" + str(arrival_time) + ", lastCicle:" + str(
                    self.global_time) + ", len(op_dict):" + str(len(op_dict_temp.items())))
        return az, max_host_on

    def first_place(self):
        pass

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
            host_list.sort(key=lambda e: e.get_cpu())
        elif self.ff_mode == "FF3D":  # decrescente
            host_list.sort(key=lambda e: e.get_cpu(), reverse=True)
        return host_list  # se nenhuma configuração

    def best_host(self, vm, host_list):
        for host in host_list:
            if host.get_cpu() >= vm.get_vcpu() and host.get_ram() >= vm.get_vram():  # TODO: add analise de ram
                with self.some_rlock:
                    self.logger.debug(
                        "Yes!, Best host for" + str(vm.get_id()) + "(" + str(vm.get_vcpu()) + "vcpu), is" + str(
                            host.get_id()) + \
                        "(" + str(host.get_cpu()) + "cpu). OverbCount:" + str(host.overb_count) + "tax:" + str(
                            host.actual_overb) + \
                        "has?" + str(host.has_overbooking))
                return host, True
            else:
                if self.has_overbooking and host.can_overbooking(vm):
                    with self.some_rlock:
                        self.logger.debug("Overb. for" + vm.get_id() + "(" + str(vm.get_vcpu()) + "cpu), is" + \
                                          host.get_id() + "(" + str(host.get_cpu()) + "). Overb:" + str(
                            host.overb_count) + \
                                          str(host.actual_overb) + str(host.has_overbooking))
                    host.do_overbooking(vm)
                    return host, True
        return host, False

    def place(self, vm_list, host_list):
        vm_list.sort(key=lambda e: e.get_cpu(), reverse=True)  # decrescente
        host_ff_mode = host_list  # TODO: ver se e necessario: self.order_ff_mode(host_list)
        for vm in vm_list:
            bhost, state = self.best_host(vm, host_ff_mode)
            if state is False:
                with self.some_rlock:
                    self.logger.error("PROBLEM: not found best host for placement.")
            else:
                vm.set_physical_host(bhost.get_id())
                if bhost.allocate(vm):
                    host_ff_mode.append(bhost)
                else:
                    with self.some_rlock:
                        self.logger.error("Problem on allocate at placement")
                    return host_list
        return host_ff_mode

    def migrate(self, dc):
        vm_list_to_migrate = []

        new_dc = AvailabilityZone(dc.get_azNodes(), dc.get_azCores(), dc.get_availability(),
                                  dc.get_id(), dc.get_azRam(), dc.get_algorithm(), dc.get_flag_overbooking())
        # Criando a lista com todas as mvs em execução:
        for eachHost in dc.get_host_list():
            for vm in eachHost.get_virtual_resources():
                # TODO porque 'migrate?' Marcacao Transitoria
                vm.set_physical_host("migrate")
                vm_list_to_migrate.append(vm)

        # Aplicando o ordenação decrescente:
        vm_list_to_migrate.sort(key=lambda e: e.get_vcpu(), reverse=True)

        for vm in vm_list_to_migrate:
            with self.some_rlock:
                self.logger.debug("next vm:" + str(vm.get_id()))
            for eachHost in new_dc.get_host_list():
                if new_dc.allocate_on_host(vm):
                    self.last_number_of_migrations += 1
                    break
                else:
                    self.last_number_of_migrations -= 1
                    with self.some_rlock:
                        self.logger.error("PROBLEM ON MIGRATE after overbooking" + \
                                          str(vm.get_id()) + str(eachHost.get_id()) + \
                                          str(eachHost.overb_count))
        return new_dc

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
                                energy = energy + az.get_total_energy_consumption()
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
            self.logger.debug("Final: last arrival:" + str(arrival_time) + ", lastCicle:" + str(
                this_cycle) + ", len(op_dict):" + str(len(op_dict_temp.items())))
        return az, max_host_on

    '''
