#!/usr/bin/python
# -*- coding: utf-8 -*-

from random import randint
import math
from copy import deepcopy
import threading
from collections import OrderedDict
import time
from DistInfra import *


class Chave(object):
    def __init__(self, api):
        self.api = api
        self.sla = api.sla
        self.logger = api.sla.g_logger()
        self.nit = api.sla.g_nit()
        self.trigger_to_migrate = api.sla.g_trigger_to_migrate()
        self.frag_percent = api.sla.g_frag_percentual()
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
        self.exceptions = False
        self.executing_replicas_d = dict()
        self.replication_pool_d = dict()
        # key['lcid_azid_vmid'] =
        #       {'critical':[AZc, VMc],
        #        'replicas':[[AZr1,VMr1],[...], [AZrn,VMrn]]}

    def __repr__(self):
        return repr([self.logger, self.nit, self.trigger_to_migrate,
                     self.frag_percent, self.pm_mode, self.ff_mode,
                     self.window_size, self.window_time, self.has_overbooking,
                     self.all_vms_dict, self.all_op_dict, self.all_ha_dict, self.sla])

    def gvt(self, max):
        self.logger.info("Init GVT in {0} to {1}".format
                         (self.global_time, self.api.demand.max_timestamp))
        while self.global_time < self.api.demand.max_timestamp + 1 and not self.exceptions:
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
        In this version, we use Threads for running infrastructures in parallel
        :return: Void
        '''
        lock = threading.Lock()
        self.thread_dict['gvt'] = threading.Thread(
            name="T_gvt",
            target=self.gvt,
            args=[0])
        # Creating Thread list
        for az in self.api.get_az_list():
            self.executing_replicas_d[az.az_id] = dict()
            self.thread_dict[str(az.az_id)] = threading.Thread(
                name="Tz_" + str(az.az_id),
                target=self.az_optimized_placement,
                args=[az, lock])
        for lc_id, lc_obj in self.api.get_localcontroller_d().items():
            #self.buffer_lc_replicas_d[lc_obj.get_id()] = OrderedDict()
            self.thread_dict[str(lc_id)] = threading.Thread(
                name="Tr_" + str(lc_id),
                target=self.region_replication,
                args=[lc_obj, lock])
        # Release Threads
        for t_id, t_obj in self.thread_dict.items():
            self.logger.debug("Executing thread for: {0}".format(
                t_obj.getName()))
            t_obj.start()
            t_obj.join(1000)
            # Join Threads? NO!
        while True:
            for t_id, t_obj in self.thread_dict.items():
                if not t_obj.isAlive():
                    #self.exceptions = True
                    self.logger.error("Thread {0} is dead!".format(t_obj.getName()))
                    raise RuntimeError("Thread {0} is dead!".format(t_obj.getName()))

    def az_optimized_placement(self, az, lock):
        self.logger.info("Passando pela az: {0}".format(az.az_id))
        requisitions_queue = []
        req_size, req_size2, energy = 0, 0, 0.0
        max_host_on = 0
        vms_in_execution = dict()
        op_dict_temp = az.op_dict
        FORCE_PLACE = False
        arrival_time = 0

        while len(op_dict_temp.items()) > 0 and not self.exceptions:

            for op_id, vm in op_dict_temp.items():
                # MIGRATE FIRST
                #            if pm == "MigrationFirst" and (chave.is_time_to_migrate(this_cycle) or dc.has_fragmentation()):
                #                dc = chave.migrate(dc)
                #                print "migrating at:", this_cycle, "with:", chave.get_last_number_of_migrations(), "migrations"
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
                            status, placed_list = self.one_thread_place(lock, requisitions_queue, az)
                            if status:
                                for vmq in placed_list:
                                    vms_in_execution[vmq.vm_id] = vmq

                                for vmop in requisitions_queue:
                                    del op_dict_temp[vmop.vm_id+"_START"]
                                # TODO: We measure energy consumption on each placement
                                self.measure_energy(az)
                                requisitions_queue = []
                                self.sla.metrics(az.get_id(), 'set', "req_size", req_size)
                                req_size = 0
                                FORCE_PLACE = False
                            else:
                                self.logger.error("Problem on place queue: {0}".format(requisitions_queue))
                                #raise ConnectionAbortedError
                    # For 'STOP' state:
                    elif this_state == "STOP" and vm not in requisitions_queue:  # não adicionado na ultima janela
                        exec_vm = None
                        try:
                            exec_vm = vms_in_execution.pop(vm.vm_id)
                        except IndexError:
                            self.logger.error("Problem INDEX on pop vm {0}".format(vm.vm_id))
                        except KeyError:
                            self.logger.error("Problem KEY on pop vm {0} {1}".format(vm.vm_id, exec_vm))
                        #                           #exit(1)
                        if exec_vm is not None:
                            if az.deallocate_on_host(exec_vm):
                                self.measure_energy(az)
                                del op_dict_temp[op_id]
                            else:
                                self.logger.error("Problem for deallocate {0}".format(exec_vm.vm_id))
                                #if exec_vm.vm_id in self.executing_replicas_d:
                            if vm.pool_id is not None:
                                if vm.pool_id in self.replication_pool_d.keys():
                                    pop_vm_replica = self.executing_replicas_d.pop(exec_vm.vm_id)
                                    azid_replica = pop_vm_replica.az_id
                                    lc_id = self.api.get_lc_id_from_az_id(pop_vm_replica.az_id)
                                    self.api.localcontroller_d[lc_id].az_dict[azid_replica].deallocate_on_host(pop_vm_replica)
                                else:
                                    self.logger.error("NOT FOUND {0}".format(self.replication_pool_d[vm.pool_id]))
                                    pass
                            else:
                                pass
                        else:
                            self.logger.error("Problem for deallocate: VM is None. Original {0}".format(vm))
                    else:
                        self.logger.error("OOOps, DIVERGENCE between {0} and {1} ".format(this_state, op_id))
                        FORCE_PLACE = True
                        continue
                else:
                    # While there are not requisition, wait for the Thread_GVT
                    #self.logger.debug("Waiting GVT at %s" % (self.global_time))
                    requisitions_queue = []
                    req_size = 0
                    continue

        self.logger.info("Exit for {0} {1} {2}".format(
            threading.currentThread().getName(), self.global_time, az.az_id))
        '''while self.thread_dict['gvt'].isAlive():
            time.sleep(60)
            self.logger.info("AAAAAAAAAAA {0}".format(self.global_time))
            pass
            # PLACEMENT FIRST
            #        if pm == "PlacementFirst" and (chave.is_time_to_migrate(this_cycle) or dc.has_fragmentation()):
            #            dc = chave.migrate(dc)
            ##            last_host_list = dc.get_host_list()
            ##            empty_host_list = dc.create_infrastructure()
            ##            new_host_list = chave.migrate(last_host_list, empty_host_list)
            ##            dc.set_host_list(new_host_list)
            #            print "migrating at:", this_cycle, "with:", chave.get_last_number_of_migrations(), "migrations"
            ##self.logger.info("Last arrival:" + str(arrival_time) + ", lastCicle:" + str(
            #    self.global_time) + ", len(op_dict):" + str(len(op_dict_temp.items())))
            # #time.sleep(5)'''

    def best_host(self, vm, az):
        for host in az.host_list:
            if host.cpu >= vm.get_vcpu() and host.ram >= vm.get_vram():
                self.logger.info("Best host for {0}-{1} (vcpu:{2}) is {3} (cpu:{4}). ovbCount:{5}, tax:{6} hasOvb? {7}.".format(
                    vm.get_id(), vm.type, vm.get_vcpu(), host.get_id(), host.cpu, host.overb_count,
                    host.actual_overb, host.has_overbooking))
                return host, True
            else:
                if self.has_overbooking and host.can_overbooking(vm):
                    self.logger.info("Overb for {0} (vcpu:{1}), is {2} (cpu:{3}). Overb cnt:{4}, actual:{5}, has:{6}.".format(
                                      vm.get_id(), vm.get_vcpu(), host.get_id(), host.cpu,
                                      host.overb_count, host.actual_overb, host.has_overbooking))
                    host.do_overbooking(vm)
                    return host, True
        self.logger.error("PROBLEM: not found best host in len:{0} for place {1}. Try a new host. \n {2}\n{3}".format(len(az.host_list), vm.get_id(), vm, az))
        if self.api.create_new_host(az.az_id):
            for host in az.host_list:
                if host.cpu >= vm.get_vcpu() and host.ram >= vm.get_vram():
                    self.logger.info("After new host, for %s (vcpu:%s) is %s (cpu:%s). ovbCount:%s, tax:%s hasOvb? %s." %
                                     (vm.get_id(), vm.get_vcpu(), host.get_id(), host.cpu, host.overb_count,
                                      host.actual_overb, host.has_overbooking))
                    return host, True
        return None, False

    def one_thread_place(self, lock, vm_list, az, type=None):
        with lock:
            r_bool, r_list = self.place(vm_list, az, type)
            return r_bool, r_list

    def place(self, vm_list, az, type=None):
        vm_list_ret = []
        vm_list.sort(key=lambda e: e.get_vcpu(), reverse=True)  # decrescente
        # host_ff_mode = az.get_host_list()
        #  TODO: ver se é necessário: self.order_ff_mode(az.host_list)
        for vm in vm_list:
            bhost, is_ok = self.best_host(vm, az)
            if is_ok is True:
                vm.lc_id = az.lc_id

                if self.require_replica(vm, az) and type is None:
                    self.replicate_vm(vm, az)
                vm.set_host_id(bhost.host_id)
                vm.az_id = az.az_id

                if type == self.sla.REPLICA:
                    pool = self.replication_pool_d.get(vm.pool_id)
                    #self.logger.error("Get replicas from {0} {1}".format(vm.pool_id, pool))
                    try:
                        replicas = pool.get(self.sla.REPLICA)
                        replicas.append([vm, az])
                        self.replication_pool_d[vm.pool_id].update({self.sla.REPLICA: replicas})
                    except AttributeError:
                        self.logger.error("Get replicas from {0} {1}".format(vm.pool_id,pool))
                        exit(0)

                self.logger.info("Allocating {0} in {1} {2} {3}".format(vm.vm_id, vm.host_id, vm.type, vm.az_id))
                if bhost.allocate(vm):
                    vm_list_ret.append(vm)
                    return True, vm_list_ret  # host_ff_mode.append(bhost)
                else:
                    self.logger.error("Problem place {0}-{1} in {2}-{3}=?{4}".format(
                        vm.vm_id, vm.type, vm.host_id, az.az_id, vm.az_id))
                    return False, []
        return True, vm_list_ret

    def choose_az_for_vm_replica(self, vm, az_list):
        az_select = self.sla.g_az_selection()
        az_max_target = 0
        best_az = None
        temp_az_list = list(az_list)
        critical_az = None
        min_cpu = [0, None]
        max_cpu = [1024, None]
        for az in az_list:
            if vm.az_id == az.get_id():
                critical_az = az
                #break
        try:
            temp_az_list.remove(critical_az)
            self.logger.debug("In {0}-{1} Removed {2}=?{3}, from {4}".format(
                vm.vm_id, vm.type, vm.az_id, critical_az.az_id, len(temp_az_list)))
        except ValueError:
            self.logger.error("azid {0} ({1}) not in list {2}".format(vm.az_id, critical_az, temp_az_list))
        except Exception as e:
            self.logger.exception(type(e))
            self.logger.error("UNKNOWN: azid {0} ({1}) not in list {2}".format(vm.az_id, critical_az, temp_az_list))

        for az in temp_az_list:
            if az.azCores > min_cpu[0]:
                min_cpu[0] = az.azCores
                min_cpu[1] = az
            if az.azCores < max_cpu[0]:
                max_cpu[0] = az.azCores
                max_cpu[1] = az

        for az in temp_az_list:
            if vm.vcpu > max_cpu[0]:
                best_az = max_cpu[1]
                best_az.has_overbooking = True
            if az_select == 'HA':
                if float(az_max_target) < float(az.availability):
                    az_max_target = float(az.availability)
                    best_az = az
            elif az_select == 'LB':
                usage = az.get_hosts_density()
                if az_max_target < usage:
                    az_max_target = usage
                    best_az = az
            else:  # random?
                best_az = temp_az_list[ randint(0, len(temp_az_list)) ]
                break
        if best_az is None:
            best_az = temp_az_list[randint(0, len(temp_az_list)-1)]
            self.logger.error("VM {0} (from {1}) is NONE, force selected for {2}".format(
                vm.vm_id, vm.az_id, best_az))
        self.logger.info("VM {0} (from {1}) will be replicated for {2}".format(
            vm.vm_id, critical_az.az_id, best_az.az_id))
        return best_az

    def region_replication(self, lc_obj, lock):
        this_lc_azs = [az.get_id() for az in lc_obj.az_list]
        if len(self.replication_pool_d.items()) > 0:
            for pool_id, pool_d in self.replication_pool_d.items():
                lc_pool = pool_id.split('_')[0]
                if lc_pool == lc_obj.lc_id:
                    # for type, pool_t_l in pool_d:
                    vm_r = pool_d[self.sla.REPLICA][0][1]
                    if vm_r.az_id in this_lc_azs:
                        az = self.choose_az_for_vm_replica(vm_r, lc_obj.az_list)
                        r_bool, r_list = self.one_thread_place(lock, [vm_r], az, self.sla.REPLICA)
                        if r_bool:
                            self.logger.info("Allocating REPLICA {0} on {1}".format(
                                vm_r.vm_id, vm_r.az_id))
                            try:
                                #vm_in_exec = self.buffer_vm_replicas_d.pop(vm_r.vm_id)
                                self.executing_replicas_d[vm_r.vm_id] = vm_r
                            except Exception as e:
                                self.logger.exception(type(e))
                                self.logger.error("Problem to allocating REPLICA {0} on {1}".format(
                                    vm_r.vm_id, vm_r.az_id))
                        else:
                            self.logger.error("On place REPLICA {0}".format(pool_id))
                    else:
                        pass
                        #self.logger.error("pool:{2} az_id {0} not in {1}".format(vm_r.az_id, this_lc_azs, pool_id))
                else:
                    pass
                    #self.logger.error("pool {0} != {1} lc_obj.lc_id".format(pool_id, lc_obj.lc_id))
        self.logger.info("Exit for {0} {1} {2}".format(
            threading.currentThread().getName(), self.global_time, lc_obj.lc_id))
        '''while self.thread_dict['gvt'].isAlive():
            time.sleep(60)
            self.logger.info("BBBBBBBBBBB {0}".format(self.global_time))'''

    '''
    def region_replication(self, lc_obj):
        self.logger.info("Into thread for REPLICATION: {0}".format(lc_obj.get_id()))
        this_lc_azs = [az.get_id() for az in lc_obj.az_list]
        while self.global_time < self.api.demand.max_timestamp: #self.thread_dict['gvt'].isAlive():
            #while self.buffer_vm_replicas_d.items() > 0:
            for vm_id, vm_r in self.buffer_vm_replicas_d.items():
                if vm_r.az_id in this_lc_azs:
                    az = self.choose_az_for_vm_replica(vm_r, lc_obj.az_list)
                    vm_r.az_id = az.get_id()
                    if self.place([vm_r], az):
                        self.logger.info("Allocating REPLICA {0} on {1}".format(
                            vm_r.vm_id, vm_r.az_id))
                        vm_in_exec = self.buffer_vm_replicas_d.pop(vm_r.vm_id)
                        self.executing_replicas_d[vm_r.vm_id] = vm_r
    '''

    def require_replica(self, vm, az):
        if type(vm.type) is str and type(vm.ha) is float and type(az.availability) is float:
            if vm.ha > az.availability and vm.type != self.sla.REPLICA:
                self.logger.info("{0}-{1} require replication! {2}=?{3}".format(vm.vm_id, vm.type, vm.az_id, az.az_id))
                return True
            return False
        else:
            self.logger.error("Types: vm:{0}, ha:{1}, av:{2}".format(type(vm.type), type(vm.ha), type(az.availability)))
        return False

    def replicate_vm(self, vm, az):
        pool_id = vm.lc_id + '_' + vm.az_id + '_' + vm.vm_id
        if pool_id not in self.replication_pool_d:
            attr = vm.getattr()
            vm_replica = VirtualMachine(*attr)
            vm_replica.type = self.sla.REPLICA
            vm.type = self.sla.CRITICAL
            #self.buffer_vm_replicas_d[vm_replica.vm_id] = vm_replica
            vm_replica.pool_id = pool_id
            vm.pool_id = pool_id
            self.replication_pool_d[pool_id] = {self.sla.CRITICAL: [az, vm], self.sla.REPLICA: [["", vm_replica]]}
            return True
        return False

    def migrate(self, az):
        vm_list_to_migrate = []

        new_az = AvailabilityZone(az.get_azNodes(), az.get_azCores(), az.get_availability(),
                                  az.get_id(), az.get_azRam(), az.algorithm, az.has_overbooking)
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

    def measure_energy(self, az):
        energy = az.get_az_energy_consumption()
        self.sla.metrics(az.az_id, 'set', 'energy_l', energy)
        self.sla.metrics(az.az_id, 'set', 'energy_hour_l', energy)

    def resume_energy_hour(self, az):
        if (self.global_time % 3600) == 0:
            mean_last_hour = self.sla.metrics(az.az_id, 'avg', 'energy_hour_l')
            if mean_last_hour is False:
                return False
            self.logger.info("Media da ultima HORA: {0} at {1}h or {2}".format(
                mean_last_hour, self.global_hour, self.global_time))
            self.sla.metrics(az.az_id, 'set', 'energy_avg_l', mean_last_hour)
            self.sla.metrics(az.az_id, 'rst', 'energy_hour_l')
            self.sla.metrics(az.az_id, 'add', 'total_energy_f', mean_last_hour)
            return True
        return False

    def set_demand(self, demand):
        self.demand = demand
        self.all_vms_dict = demand.all_vms_dict
        self.all_op_dict = demand.all_op_dict()
        self.all_ha_dict = demand.all_ha_dict()

    def set_localcontroller(self, localcontroller):
        self.localcontroller_list = localcontroller
        for lc in localcontroller:
            print(lc.lc_id, lc.az_list)

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

    def get_last_number_of_migrations(self):
        ret = self.last_number_of_migrations
        self.last_number_of_migrations = 0
        return ret

    def is_time_to_migrate(self, this_time):
        if this_time % self.trigger_to_migrate == 0:
            return True
        return False

    def is_time_to_place(self, cycle):
        if cycle % self.window_time == 0:
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

