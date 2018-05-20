#!/usr/bin/python
# -*- coding: utf-8 -*-

# From packages:

from itertools import combinations
from Architecture.Resources.Physical import *


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

    def obj_id(self):  # Return the unique hexadecimal footprint from each object
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

    def obj_id(self):  # Return the unique hexadecimal footprint from each object
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
        self.lc_id = None  # until instance object
        self.logger = sla.g_logger()
        self.has_overcommitting = sla.g_has_overcommitting()
        self.algorithm = sla.g_algorithm()
        self.azNodes = sla.g_az_dict()[az_id]['az_nodes']
        self.azCores = sla.g_az_dict()[az_id]['az_cores']
        self.azRam = sla.g_az_dict()[az_id]['az_ram']
        self.nit = sla.g_az_dict()[az_id]['az_nit']
        self.availability = ha.get('this_az')  # first line from file
        # Qual percentual de um host em relação ao numero total de cores?:
        self.frag_min = float(self.azCores) / float(self.azNodes * self.azCores)
        self.vms_dict = vms
        self.op_dict = ops
        self.ha_dict = ha
        self.base_infrastructure = None
        self.host_list = []
        self.host_list_d = dict()
        self.rollback_list = []
        self.total_SLA_violations = 0
        # @TODO: olha a gambi:
        self.resources = self.host_list

    def __repr__(self):
        return repr(['node:', self.azNodes, 'core:', self.azCores, 'av:', self.availability,
                     'id:', self.az_id, 'ram:', self.azRam, 'alg:', self.algorithm])

    # Return the unique hexadecimal footprint from each object
    def obj_id(self):
        return str(self).split(' ')[3].split('>')[0]

    def create_infra(self, first_time=False, host_state=True):
        host_list = []
        host_list_d = dict()
        for node in range(self.azNodes):
            host_id = 'HOST' + str(node)
            h = PhysicalMachine(host_id,
                                self.azCores,
                                self.azRam,
                                self.algorithm,
                                self.az_id,
                                self.sla,
                                self.logger)
            h.activate_hypervisor_dom0(log=False)
            h.state = host_state
            host_list.append(h)
            host_list_d[host_id] = h
        self.logger.debug("{0} created {1} hosts, {2} cores and av: {3}".format(
            self.az_id, len(host_list), self.azCores, self.availability))
        if first_time:
            self.host_list = host_list
            self.host_list_d = host_list_d
            return True
        return host_list

    def add_new_host_to_list(self, host_state=True):
        host_id = 'HOST' + str(self.azNodes)
        h = PhysicalMachine(host_id,
                            self.azCores,
                            self.azRam,
                            self.algorithm,
                            self.az_id,
                            self.sla,
                            self.logger)
        h.state = host_state
        h.activate_hypervisor_dom0(log=True)
        try:
            self.host_list.append(h)
            self.host_list_d[host_id] = h
        except Exception as e:
            self.logger.exception(type(e))
            self.logger.error("{} Problem on add new host {}".format(self.az_id, id))
            return False
        self.azNodes += 1
        self.logger.info("Done! {}, now we have {} hosts. {}.".format(h.get_id(), self.azNodes, h))
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

    def fragmentation(self):
        """
        Fragmentation from active hosts
        :return: float percentual fragmentation
        """
        remaining_cpu, active_hosts = 0, 0
        for host in self.host_list:
            if host.is_on is HOST_ON:
                remaining_cpu += host.cpu
                active_hosts += 1
        return float(remaining_cpu) / float(self.azCores * self.azNodes)

    def get_hosts_density(self):
        state_on, state_off = 0, 0
        for host in self.host_list:
            if host.is_on:
                state_on += 1
            else:
                state_off += 1
        if state_on + state_off != len(self.host_list):
            self.logger.error("Prob on number of states {}+{}!={}".format(
                state_on, state_off, len(self.host_list)))
            return None
        actives = float(state_on) / (float(state_on) + float(state_off))
        self.logger.info("AZ {} has {}% hosts actives".format(self.az_id, actives*100))
        return actives

    def allocate_on_host(self, vm, defined_host=None):
        for host in self.host_list:
            # vm.set_host_object()
            if vm.get_host_id() is not None:
                if host.get_id() == vm.get_host_id():
                    vm.set_host_object(host)
                    if host.allocate(vm):
                        self.logger.info("A: "+str(vm.get_id())+" on "+str(host.get_id()))
                        return True
                    else:
                        if self.has_overcommitting and host.can_overcommitting(vm):
                            self.logger.info("Overcommit vm: "+str(vm.get_id())+
                                              ", with:"+str(len(self.get_list_overcom_amount())))
                            host.do_overcommitting(vm)
                            if host.allocate(vm):
                                self.logger.info("Alloc:"+str(vm.get_id())+" on "+str(host.get_id()))
                                return True
            elif vm.get_host_id() is "migrate":
                vm.set_host_object(host)
                if host.allocate(vm):
                    self.logger.info("Migr "+str(vm.get_id())+" to:"+str(host.get_id()))
                    return True
                else:
                    if host.can_overcommitting(vm):
                        self.logger.info("Overcommit on migr vm:"+str(vm.get_id()))
                        host.do_overcommitting(vm)
                        if host.allocate(vm):
                            self.logger.info("Migr " + str(vm.get_id()) + " to:" + str(host.get_id()))
                            return True
                    else:
                        return False
            else:
                self.logger.error("NONE found on allocate: "+str(vm.get_host_id())+str(vm.get_id()))
                return False
        return False

    def deallocate_on_host(self, vm, defined_host=None, timestamp=None):
        vm_host_id = vm.host_id
        for host in self.host_list:
            hostid = host.get_id()

            if vm_host_id is None or vm_host_id is "None":
                self.logger.error("{} found in vm_host_id when deallocate: {} or {} for {} {}".format(
                    vm_host_id, vm.obj_id(), vm, hostid, vm.az_id, vm.type))
                return False
            elif hostid is None:
                self.logger.error("{} found in hostid when deallocate: {} for {} {} {}".format(
                    hostid, vm_host_id, host, vm.az_id, vm.type))
                return False
            if hostid == vm_host_id:
                if host.deallocate(vm, timestamp):
                    self.logger.info("Deallocated SUCESS! {0} {1} from {2} {3} typ: {4}".format(
                        vm.vm_id, hostid, vm.az_id, vm.pool_id, vm.type))
                    return True
                else:
                    self.logger.error("Problem on deallocate: {0} != {1} {2} {3}".format(
                        vm_host_id, hostid, vm.az_id, vm.type))
                    return False
        self.logger.error("SERIOUS!!! Problem on deallocate: \n{0} \n {1}".format(vm, self.host_list))
        return False

    def get_host_SLA_violations(self, host):
        return host.get_host_SLA_violations_total()

    def get_total_SLA_violations_from_datacenter(self):
        total_sla_violations = 0
        for host in self.host_list:
            total_sla_violations += self.get_host_SLA_violations(host)
        return total_sla_violations

    def get_list_overcom_amount(self):
        overcom_list = []
        for host in self.host_list:
            overcom = host.get_host_SLA_violations_total()
            if overcom > 0:
                overcom_list.append({host.get_id():overcom})
        return overcom_list

    def host_resource_usage(self):
        pass

    def host_status(self):
        pass

    def get_resource(self, id):
        for pnode in self.resources:
            if pnode.get_id() == id:
                return pnode
        return False

    def get_host_list(self):
        return self.host_list

    def get_physical_resources_ordered(self):
        self.host_list.sort(key=lambda e: e.cpu)
        return list(self.host_list)

    def get_used_resources(self):
        used_resources = 0
        return used_resources

    def get_total_resources(self):
        total_resources = 0
        for pnode in self.resources:
            total_resources += pnode.get_total_cpu()
        return total_resources

    def get_vms_dict(self):
        all_vms_dict = dict()
        for host in self.host_list:
            all_vms_dict.update(host.virtual_machine_dict)
        return all_vms_dict

    def get_id(self):
        return self.az_id

    def get_az_energy_consumption2(self, append_metrics=False):
        _sum = 0
        host_cons_dict = dict()
        for host in self.host_list:
            if host.is_on:
                host_cons = host.get_energy_consumption()
                _sum += host_cons
                host_cons_dict[host.get_id()] = host_cons
        if append_metrics:
            self.sla.metrics(self.az_id, 'set', 'az_load_l', _sum)
            self.sla.metrics(self.az_id, 'set', 'hosts_load_l', host_cons_dict)
        return _sum
        #return sum([host.get_energy_consumption() for host in self.host_list if host.has_virtual_resources()])

    def get_az_watt_hour(self):
        total_az_hour = 0
        for host in self.host_list:
            total_az_hour += host.get_emon_hour()
        return total_az_hour


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