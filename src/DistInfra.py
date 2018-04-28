#!/usr/bin/python
# -*- coding: utf-8 -*-

from random import randrange, uniform, random, randint
from copy import deepcopy
import math
# From packages:
from Chave import *
from Controller import *
from DistInfra import *
from Demand import Demand
from Eucalyptus import *
from SLAHelper import *

from Physical import PhysicalMachine
from Virtual import VirtualMachine
from itertools import combinations


class Infrastructure(object):
    def __init__(self, sla):
        self.sla = sla
        self.logger = sla.g_logger()
        self.max_ha = 0
        self.min_ha = 0
        self.controller_list = []
        self.region_list = []

    def __repr__(self):
        return repr([self.logger, self.max_ha, self.min_ha, self.region_list, self.controller_list, self.sla])

    def obj_id(self):
        return str(self).split(' ')[3].split('>')[0]

    def create_regions_list(self, controller_list):
        region_list = []
        self.controller_list = controller_list
        for r_id, controller in enumerate(controller_list):
            region = Region(r_id, self.sla)
            region_list.append(region)
        self.region_list = region_list
        return region_list


class Region(Infrastructure):
    def __init__(self, sla, region_id, lcontroller):
        """
        Region its just a set  of AZs with one local controller
        :param sla:
        :param region_id:
        :param lcontroller:
        """
        Infrastructure.__init__(self, sla)
        self.sla = sla
        self.region_id = region_id
        self.lcontroller = lcontroller
        self.availability_zones_list = lcontroller.az_list
        self.logger = sla.g_logger()

    def __repr__(self):
        return repr([self.logger, self.region_id, self.availability_zones_list, self.lcontroller, self.sla])

    def obj_id(self):
        return str(self).split(' ')[3].split('>')[0]

    def set_ha_tree(self, av_list):
        """
        For generate the best combinations between AZs
        :param av_list:
        :return:
        """
        n = len(av_list) - 1
        y = combinations(av_list, n)
        x = []
        for element in y:
            x.append(element)
            # print x
        x.append(combinations(av_list, n+1))
        return x


class AvailabilityZone(Infrastructure):
    def __init__(self, sla, az_id, vms, ops, ha):
        Infrastructure.__init__(self, sla)
        self.sla = sla
        self.az_id = az_id
        self.logger = sla.g_logger()
        self.has_overbooking = sla.g_has_overbooking()
        self.algorithm = sla.g_algorithm()

        self.azNodes = sla.g_az_dict()[az_id]['az_nodes']
        self.azCores = sla.g_az_dict()[az_id]['az_cores']
        self.azRam = sla.g_az_dict()[az_id]['az_ram']
        self.nit = sla.g_az_dict()[az_id]['az_nit']

        self.availability = ha.get('this_az')  # first line from file
        self.vms_dict = vms
        self.op_dict = ops
        self.ha_dict = ha

        self.base_infrastructure = None
        self.host_list = []
        self.rollback_list = []
        self.total_SLA_violations = 0
        # @TODO: olha a gambi:
        self.resources = self.host_list
        self.ndelete = 0
        self.ndealloc = 0
        self.nalloc = 0
        self.trepl = 0
        self.nrepl = 0
        self.trecfg = 0
        self.nrecfg = 0
        self.nmig = 0
        if self.algorithm == "EUCA":
            self.dbg = False
        elif self.algorithm == "CHAVE":
            self.dbg = False

    def __repr__(self):
        return repr([self.azNodes, self.azCores, self.availability,
                     self.az_id, self.azRam, self.algorithm])

    def obj_id(self):
        return str(self).split(' ')[3].split('>')[0]

    def create_infrastructure(self, first_time=False, is_on=True):
        host_list = []
        for node in range(self.azNodes):
            # todo: add az_id nos hosts
            h = PhysicalMachine('NODE' + str(node),
                                self.azCores,
                                self.azRam,
                                self.algorithm,
                                self.az_id,
                                self.logger)
            h.activate_hypervisor_dom0()
            h.state = is_on
            host_list.append(h)
        self.logger.info("Infrastructure created with %s hosts." % (len(host_list)))
        if first_time:
            self.host_list = host_list
            return True
        return host_list

    def add_new_host_to_list(self):
        id = self.azNodes
        h = PhysicalMachine('NODE' + str(id),
                            self.azCores,
                            self.azRam,
                            self.algorithm,
                            self.az_id,
                            self.logger)
        h.state = True
        h.activate_hypervisor_dom0()
        try:
            self.host_list.append(h)
        except:
            self.logger.error("Problem on add new host", id)
            return False
        self.azNodes += 1
        self.logger.info("ADDED %s, now we have %s." % (h.get_id(), self.azNodes))
        return True

    def is_required_replication(self, vm):
        if vm.ha > self.availability:
            return True
        return False

    def each_cycle_get_hosts_on(self):
        host_on = 0
        host_off = 0
        hol = []
        for host in self.host_list:
            if host.is_on is True:
                host_on += 1
                hol.append(host)
            else:
                host_off += 1
        len_h = len(self.host_list)
        if (host_on + host_off) != len_h:
            self.logger.error("Size of host_list (%s) is != h-on (%s) + h-off (%s)" %
                              (len_h, host_on, host_off))
        return host_on, hol

    # TODO: need improvements
    def fragmentation(self):
        remaining_res, count = 0, 0
        s = len(self.host_list)
        for host in self.host_list:
            if host.is_on is True:
                count += 1
                remaining_res = host.cpu
        if s == count:
            return float(remaining_res) / float(self.azCores)
        else:
            self.logger.error("Some problem on fragmentation:"+str(s)+"!="+str(count))
            return -1

    def get_total_density(self):
        state_on, state_off = 0, 0
        for host in self.host_list:
            state = host.is_on
            if state:
                state_on += 1
            else:
                state_off += 1
        if state_on + state_off != len(self.host_list):
            self.logger.error("Prob on number of states"+str(state_on)+"+"+str(state_off)+"!="+str(len(self.host_list)))
            return None
        actives = float(state_on) / float(state_on) + float(state_off)
        self.logger.info("DC has"+str(actives)+"hosts actives")
        return actives

    def allocate_on_host(self, vm):
        for host in self.host_list:
            # vm.set_host_object()
            if vm.get_host_id() is not None:
                if host.get_id() == vm.get_host_id():
                    vm.set_host_object(host)
                    if host.allocate(vm):
                        self.logger.info("A: "+str(vm.get_id())+" on "+str(host.get_id()))
                        return True
                    else:
                        if self.has_overbooking and host.can_overbooking(vm):
                            self.logger.info("Overbook vm: "+str(vm.get_id())+
                                              ", with:"+str(len(self.get_list_overb_amount())))
                            host.do_overbooking(vm)
                            if host.allocate(vm):
                                self.logger.info("Alloc:"+str(vm.get_id())+" on "+str(host.get_id()))
                                return True
                    #return False
            elif vm.get_host_id() is "migrate":
                vm.set_host_object(host)
                if host.allocate(vm):
                    self.logger.info("Migr "+str(vm.get_id())+" to:"+str(host.get_id()))
                    return True
                else:
                    if self.has_overbooking and host.can_overbooking(vm):
                        self.logger.info("Overbook on migr vm:"+str(vm.get_id()))
                        host.do_overbooking(vm)
                        if host.allocate(vm):
                            self.logger.info("Migr " + str(vm.get_id()) + " to:" + str(host.get_id()))
                            return True
                    else:
                        return False
            else:
                self.logger.error("NONE found on allocate: "+str(vm.get_host_id())+str(vm.get_id()))
                return False
        return False

    def deallocate_on_host(self, vm):
        vm_host_id = vm.host_id
        for host in self.host_list:
            hostid = host.get_id()

            if vm_host_id is None or vm_host_id is "None":
                self.logger.error("None found when deallocate: (%s) or %s for %s" % (vm.obj_id(), vm, hostid))
                return False
            elif hostid is None:
                self.logger.error("None found when deallocate: %s for %s" % (vm_host_id, host))
                return False
            if hostid == vm_host_id:
                if host.deallocate(vm):
                    self.logger.info("Deallocated SUCESS! %s, from %s " % (vm.vm_id, hostid))
                    return True
                else:
                    self.logger.error("Problem on deallocate: %s != %s" % (vm_host_id, hostid))
                    return False
        self.logger.error("SERIOUS!!! Problem on deallocate: \n %s \n %s" % (vm, self.host_list))
        return False

    def get_host_SLA_violations(self, host):
        return host.get_host_SLA_violations_total()

    def get_total_SLA_violations_from_datacenter(self):
        total_sla_violations = 0
        for host in self.host_list:
            total_sla_violations += self.get_host_SLA_violations(host)
        return total_sla_violations

    def get_list_overb_amount(self):
        overb_list = []
        for host in self.host_list:
            overb = host.get_host_SLA_violations_total()
            if overb > 0:
                overb_list.append({host.get_id():overb})
        return overb_list

    def host_resource_usage(self):
        pass

    def host_status(self):
        pass

    def get_resource(self, id):
        for pnode in self.resources:
            if pnode.get_id() == id:
                return pnode
        return -1

    def get_host_list(self):
        return self.host_list

    def get_physical_resources_ordered(self):
        self.host_list.sort(key=lambda e: e.cpu)
        return list(self.host_list)

    """
    Method: guarantees at least % resources
            for the next reallocation iteration
    """
    def provide_elasticity(self, pe):
        return True

    def get_used_resources(self):
        used_resources = 0
        return used_resources

    def get_total_resources(self):
        total_resources = 0
        for pnode in self.resources:
            total_resources += pnode.get_total_cpu()
        return total_resources

    def get_vms_load(self):
        ret = []
        return ret

    def get_az_energy_consumption(self):
        return sum([host.get_energy_consumption() for host in self.host_list if host.has_virtual_resources()])


    '''def get_dc_node_load(self):
        ret = []
        for node in self.host_list:
            rn = []
            rn.append(node.get_id())
            rn.append(node.get_used_ram())
            rn.append(node.get_used_cpu())
            rn.append(node.get_cpu_usage())
            rn.append(node.get_energy_consumption())
            rn.append(node.get_wasted_energy())
            ret.append(rn)
        return ret

    def get_wasted_energy(self):
        total_waste = 0.0

        # total_resources = self.get_total_resources()
        # needed_for_pe = pe*total_resources

        # not_used = 0.0
        # for pnode in self.resources:
        #	if pnode.has_virtual_resources():
        #		not_used += pnode.get_cpu()

        # Simulating turning a machine on
        # while not_used < needed_for_pe:
        #	total_waste += 116
        #	not_used += 24

        return total_waste + sum([node.get_wasted_energy() for node in self.resources if node.has_virtual_resources()])

    def get_nop(self):
        return self.ndelete + self.ndealloc + self.nalloc + self.nrepl + self.nrecfg + self.nmig


    def clear(self):
        self.ndealloc = 0
        self.ndelete = 0
        self.nalloc = 0
        self.nrepl = 0
        self.nrecfg = 0
        self.nmig = 0
        self.rollback_list = []
    '''