#!/usr/bin/python
# -*- coding: utf-8 -*-

import threading
from Users.SLAHelper import *
from Algorithms import BaseAlgorithm


class MM(BaseAlgorithm):
    def __init__(self, api):
        BaseAlgorithm.__init__(self, api)
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
        self.has_overcommitting = api.sla.g_has_overcommitting()
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

    def __repr__(self):
        return repr([self.__get])

    def run(self):
        """
        Interface for all algorithms, the name must be agnostic for all them
        In this version, we run the infrastructures in in serial mode
        :return:
        """
        start = time.time()
        milestones = int(self.api.demand.max_timestamp / self.sla.g_milestones())
        while self.global_time <= self.api.demand.max_timestamp:
            start_for = time.time()
            for az in self.api.get_az_list():
                start_place = time.time()
                self.placement(az)
                end_place = time.time() - start_place

                start_misc = time.time()
                values = (self.global_time, az.get_az_energy_consumption2(), "",)
                self.sla.metrics.set(az.az_id, 'energy_l', values)

                azload = az.get_az_load()
                if self.az_load_change_d[az.az_id] != azload:
                    self.az_load_change_d[az.az_id] = azload
                    values = (self.global_time, azload, str(az.print_hosts_distribution(level='MIN')),)
                else:
                    values = (self.global_time, azload, "0",)
                self.sla.metrics.set(az.az_id, 'az_load_l', values)
                end_misc = time.time() - start_misc
            end_for = time.time() - start_for

            start_milestone = time.time()
            if self.global_time % milestones == 0:
                memory = self.sla.check_simulator_memory()
                elapsed = time.time() - start
                self.logger.critical("gt: {} , time:{} , it toke: {:.3f}s, {}".format(
                    self.global_time, time.strftime("%H:%M:%S"), elapsed, memory))
                self.sla.metrics.set('global', 'lap_time_l', (self.global_time, elapsed, "Status:{}".format(memory)))
                start = time.time()
            self.remove_finished_azs()
            # Doc: At the end, increment the clock:
            self.global_time += self.window_time
            end_milestone = time.time() - start_milestone

            #metric_time = (self.global_time, -1.0, "plc:{} msc:{} for:{} mls:{}".format(end_place, end_misc, end_for, end_milestone))
            metric_time = (self.global_time, end_place, end_misc, end_for, end_milestone, "")
            self.sla.metrics.set('global', 'time_steps_d', metric_time)

    def reallocate_infrastructure_mm(self):
        THRESH_UP = 19  # 80%
        THRESH_LOW = 5  # ~20%
        t = 0
        bestFitVM = None
        migrationList = []

        # execute MM from Buyya
        for h in self.get_physical_resources():
            vms = sorted(h.get_virtual_resources(), key=lambda v: v.get_vcpu_usage())
            if len(vms) == 0:
                break
            hUtil = h.get_cpu_usage()
            bestFitUtil = hUtil
            while hUtil > THRESH_UP:
                for vm in vms:
                    if vm.get_vcpu_usage() > hUtil - THRESH_UP:
                        t = vm.get_vcpu_usage() - hUtil + THRESH_UP
                        if t < bestFitUtil:
                            bestFitUtil = t
                            bestFitVM = vm
                    else:
                        if bestFitUtil == hUtil:
                            bestFitVM = vm
                        break
                hUtil = hUtil - bestFitVM.get_vcpu_usage()
                present = 0
                for v in migrationList:
                    if v.get_id() == bestFitVM.get_id():
                        present = 1
                        break
                if present == 0:
                    migrationList.append(bestFitVM)

            if hUtil < THRESH_LOW:
                for vm in vms:
                    present = 0
                    for v in migrationList:
                        if v.get_id() == vm.get_id():
                            present = 1
                            break
                    if present == 0:
                        migrationList.append(vm)
        print("MM: Now I must migrate:")

        for vm in migrationList:
            print("VM id %d" % (vm.get_id()))

        # print ("\n\n*** VI before to run the migration ***")
        # vi_before_migration = vm.get_vi()
        # vi_before_migration.print_allocation()
        # print ("\n *************************** \n")

        if len(migrationList) > 0:
            # lets call MBFD to conclude migration
            self.mbfd_and_migration(migrationList)

        # print ("\n\n###### VI after to run the migration ####")
        # vi_after_migration = vm.get_vi()
        # vi_after_migration.print_allocation()
        # print ("\n ################################ \n")

    def mbfd(self, vi):
        max_power = self.get_resources(MACHINE)[0].get_max_energy()
        vmList = sorted(vi.get_virtual_resources(), key=lambda v: v.get_vcpu_usage())
        rollback = []
        # VMs: if something went wrong, just return -1. We shouldn't fix MBFD :)
        for vm in vmList:
            vm.set_datacenter(self)

            minPower = max_power
            allocatedHost = None
            for h in self.get_resources(vm.get_type()):
                if h.can_allocate(vm):
                    power = vm.get_energy_consumption_estimate(h)
                    if power <= minPower:
                        allocatedHost = h
                        minPower = power

            if allocatedHost == None:
                for row in rollback:
                    pnode = row[0]
                    vnode = row[1]
                    pnode.deallocate(vnode)
                print
                "MBFD - None: Without solution for node %s" % (vm.get_id())
                return -1

            if not allocatedHost.allocate(vm):
                for row in rollback:
                    pnode = row[0]
                    vnode = row[1]
                    pnode.deallocate(vnode)

                print
                "MBFD: Without solution for node %s" % (vm.get_id())
                return -1

        rollback.append((allocatedHost, vm))


        print
        "MBFD - moving to network allocation"
        disconnectDict = {}
        for vm in vmList:
            connect, disconnect = vm.reconnect_adjacencies()
            # no need for track connect here
            if len(connect) == 0 and len(disconnect) == 0:
                print
                "MBFD: Without solution for network!"
                # rollback all links. Connect must be empty, otherwise we have a problem :)
                for i in disconnectDict:
                    for j in disconnectDict[i]:
                        i.disconnect(j['vnode2'])
                        j['vnode2'].disconnect(i)

                # rollback all nodes
                for row in rollback:
                    pnode = row[0]
                    vnode = row[1]
                    pnode.deallocate(vnode)
                return -1
            disconnectDict[vm] = disconnect

        vi.print_allocation()
        self.nalloc += 1
        self.vi_list.append(vi)

        print
        "MBFD: OK. Allocation is done with MBFD"
        return 1


    def mbfd_and_migration(self, migrationList):
        vmList = sorted(migrationList, key=lambda v: v.get_vcpu_usage())
        for vm in vmList:
            minPower = vm.get_physical_host().get_max_energy()
            allocatedHost = None
            for h in self.get_resources(vm.get_type()):
                # avoid migration to same host
                if vm.get_physical_host() != h and h.can_allocate(vm):
                    path, available_bw = self.shortest_path(vm.get_physical_host(), h, 1)
                    if len(path) != 0 and available_bw > 0.0:
                        time = vm.get_migration_time(available_bw)
                        # ok, migration is allowed
                        power = vm.get_energy_consumption_estimate(h)
                        if power <= minPower:
                            allocatedHost = h
                            minPower = power
            if allocatedHost != None:
                # migrate vm
                original = vm.get_physical_host()
                original.deallocate(vm)
                allocatedHost.allocate(vm)

                # Try to reconnect all vnode's adjacencies to destination
                connect, disconnect = vm.reconnect_adjacencies()
                if len(connect) == 0 and len(disconnect) == 0:
                    # Return everything as it was
                    allocatedHost.deallocate(vm)
                    if not original.allocate(vm): print('vishmig2')
            self.nmig += 1
            print("MBFD just conclude the migration of %s from %s to %s" % (
            vm.get_id(), original.get_id(), allocatedHost.get_id()))

    def alg1(self, az, semaph):
        while self.global_time < self.api.demand.max_timestamp:
            pass
        self.logger.info("Exit")


    def alg2(self, lc_obj, semaph):
        while self.global_time <= self.api.demand.max_timestamp: # or not self.exceptions:
            pass
        self.logger.info("Exit")
