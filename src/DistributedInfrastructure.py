#!/usr/bin/python
# -*- coding: utf-8 -*-

from random import randrange, uniform, random, randint
from copy import deepcopy
import math

from Physical import PhysicalMachine
from Virtual import VirtualMachine
from itertools import combinations

class Infrastructure(object):
    def __init__(self, logger, *args):
        self.logger = logger
        self.global_manager = args[0]
        self.local_manager = args[1]
        self.max_ha = 0
        self.min_ha = 0


class Region(Infrastructure):
    def __init__(self, region_id, az_list, logger, *args):
        Infrastructure.__init__(logger, *args)
        self.logger = logger
        self.region_id = region_id
        self.availability_zones_list = az_list
        self.av_list = av_list

    def set_ha_tree(self, av_list):
        n = len(av_list) - 1
        y = combinations(av_list, n)
        x = []
        for element in y:
            x.append(element)
            print x
        x.append(combinations(av_list, n+1))
        return x

class AvailabilityZone(Infrastructure):
    def __init__(self, localController, azNodes, azCores, availability, az_id, azRam, algorithm, has_overbooking, logger, *args):
        Infrastructure.__init__(logger, *args)
        self.localController = localController  # Object
        self.logger = logger
        self.dc_has_overbooking = has_overbooking
        self.algorithm = algorithm
        self.azNodes = azNodes
        self.azCores = azCores
        self.availability = availability
        self.az_id = az_id
        self.azRam = azRam
        self.base_infrastructure = None
        self.host_list = []
        self.rollback_list = []
        #self.total_SLA_violations = 0
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
        if algorithm == "EUCA":
            self.dbg = False
        elif algorithm == "CHAVE":
            self.dbg = False

    def __repr__(self):
        return repr([self.azNodes, self.azCores, self.availability, self.az_id, self.azRam, self.algorithm])

    def is_required_replication(self, vm):
        if vm.get_ha() > self.availability:
            return True
        return False

    def each_cycle_get_hosts_on(self):
        host_on, host_off = 0, 0
        self.logger.info("Size of HOST_LIST : "+str(len(self.host_list)))
        for host in self.host_list:
            if host.get_state() == "ON":
                host_on += 1
            else:
                host_off += 1
        return host_on, host_off

    # TODO: improvements
    def fragmentation(self):
        remaining_res, count = 0, 0
        s = len(self.host_list)
        for host in self.host_list:
            if host.get_state() == "ON":
                count += 1
                remaining_res = host.get_cpu()
        if s == count:
            return float(remaining_res) / float(self.azCores)
        else:
            self.logger.error("Some problem on fragmentation:"+str(s)+"!="+str(count))
            return -1

    def get_total_density(self):
        state_on, state_off = 0, 0
        for host in self.host_list:
            state = host.get_state()
            if state == "ON":
                state_on += 1
            elif state == "OFF":
                state_off += 1
            else:
                self.logger.error("Prob on get_total_density(): states on"+str(host.get_id())+str(state))
        if state_on + state_off != len(self.host_list):
            self.logger.error("Prob on number of states"+str(state_on)+"+"+str(state_off)+"!="+str(len(self.host_list)))
            return None
        actives = float(state_on) / float(state_on) + float(state_off)
        self.logger.info("DC has"+str(actives)+"hosts actives")
        return actives

    def allocate_on_host(self, vm):
        for host in self.host_list:
            # vm.set_host_object()
            if vm.get_physical_host() is not None:
                if host.get_id() == vm.get_physical_host():
                    vm.set_host_object(host)
                    if host.allocate(vm):
                        self.logger.debug("A: "+str(vm.get_id())+" on "+str(host.get_id()))
                        return True
                    else:
                        if self.dc_has_overbooking and host.can_overbooking(vm):
                            self.logger.debug("Overbook vm: "+str(vm.get_id())+", with:"+str(len(self.get_list_overb_amount())))
                            host.do_overbooking(vm)
                            if host.allocate(vm):
                                self.logger.debug("A:"+str(vm.get_id())+"on"+str(host.get_id()))
                                return True
                    #return False
            elif vm.get_physical_host() is "migrate":
                vm.set_host_object(host)
                if host.allocate(vm):
                    self.logger.debug("Migr."+str(vm.get_id())+" to:"+str(host.get_id()))
                    return True
                else:
                    if self.dc_has_overbooking and host.can_overbooking(vm):
                        self.logger.debug("Overbook on migr. vm:"+str(vm.get_id()))
                        host.do_overbooking(vm)
                        if host.allocate(vm):
                            self.logger.debug("Migr." + str(vm.get_id()) + " to:" + str(host.get_id()))
                            return True
                    else:
                        return False
            else:
                self.logger.error("NONE found on allocate: "+str(vm.get_physical_host())+str(vm.get_id()))
                return False
        return False

    def deallocate_on_host(self, vm):
        for host in self.host_list:
            try:
                vmid = vm.get_physical_host()
                hostid = host.get_id()
            except:
                self.logger.error("None found on deallocate: "+str(vm.get_parameters()))
                return False
            if hostid == vmid:
                if host.deallocate(vm):
                    self.logger.info("\t\t\tD:"+str(vm.get_id())+", from "+str(host.get_id()))
                    return True
                else:
                    self.logger.error("Problem on deallocate:"+str(vm.get_physical_host()))
        return False

    def create_infrastructure(self, first_time=False):
        host_list = []
        for node in range(self.azNodes):
            # todo: add az_id nos hosts
            h = PhysicalMachine('NODE' + str(node),
                                self.azCores,
                                self.azRam,
                                self.algorithm,
                                #self.az_id,
                                self.logger)
            host_list.append(h)
        self.logger.info("Infrastructure created with "+str(len(host_list))+" hosts")
        if first_time:
            self.host_list = host_list
            return True
        #else:
        return host_list

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

    def host_add(self):
        pass

    def host_status(self):
        pass

    def set_debug_level(self, dbg_level):
        assert (dbg_level in [0,1,2]), "Debug Level must be" + str([0,1,2])
        self.dbg = dbg_level

    def set_id(self, id):
        self.az_id = id

    def set_azNodes(self, azNodes):
        self.azNodes = azNodes

    def set_azCores(self, azCores):
        self.azCores = azCores

    def set_azRam(self, azRam):
        self.azRam = azRam

    def set_availability(self, availability):
        self.availability = availability

    def set_ram2core(self, ram2core):
        self.ram2core = ram2core

    ''' GETTERS'''

    def get_flag_overbooking(self):
        return self.dc_has_overbooking

    def get_id(self):
        return self.az_id

    def get_azNodes(self):
        return self.azNodes

    def get_azCores(self):
        return self.azCores

    def get_azRam(self):
        return self.azRam

    def get_availability(self):
        return self.availability

    def get_ram2core(self):
        return self.ram2core

    def get_algorithm(self):
        return self.algorithm

    def build_base_infrastructure(self):
        self.base_infrastructure = None
        # if self.bi_type == VI_BASED:
        #	if len(self.vi_list) >= 1:
        #		self.base_infrastructure = VIBasedBaseInfrastructure(self.vi_list)
        #self.base_infrastructure = SLABasedBaseInfrastructure(self.resources)

    def answer_replication_requests_mbfd(self, repl_requests):
        if len(repl_requests) == 0: return
    
        for vnode in repl_requests:
            self.trepl += 1
            vi = vnode.get_vi()
            new_id = vi.get_new_id()
    
            new_replica = VirtualMachine(new_id, \
                                         vnode.get_vi(), \
                                         vnode.get_vcpu(), \
                                         vnode.get_vram(), \
                                         vnode.get_vstorage(), \
                                         vnode.get_sla_time(), \
                                         vnode.get_type(), \
                                         None)
            new_replica.set_datacenter(self)
    
            for link in vnode.get_links():
                vnode2 = link.get_destination()
                bw = link.get_allocated_bandwidth()
    
                new_replica.connect(vnode2, [], bw)
                vnode2.connect(new_replica, [], bw)
    
            # Lets find a host on datacenter using MBFD
            minPower = vnode.get_physical_host().get_max_energy()
            allocatedHost = None
            for h in self.get_resources(new_replica.get_type()):
                if h.can_allocate(new_replica):
                    power = new_replica.get_energy_consumption_estimate(h)
                    if power <= minPower:
                        allocatedHost = h
                        minPower = power
            if allocatedHost != None:
                if allocatedHost.allocate(new_replica):
                    connect, disconnect = new_replica.reconnect_adjacencies()
                    if len(connect) == 0 and len(disconnect) == 0:
                        # Return everything as it was
                        allocatedHost.deallocate(new_replica)
    
                    # Otherwise, couldn't replicate, undo everything
            if new_replica.get_physical_host() == None:
                for link in new_replica.get_links():
                    vnode2 = link.get_destination()
                    new_replica.disconnect(vnode2)
                    vnode2.disconnect(new_replica)
            else:
                self.nrepl += 1
                vi.add_virtual_resource(new_replica)
                if self.dbg: print("OK, just replicated a new VM with az_id %d hosted by %d" % (
                new_replica.get_id(), new_replica.get_physical_host().get_id()))

    def migrate(self, vnode, resources):
        pnode = vnode.get_physical_host()
        # Try to migrate in all candidates
        for destination in resources:
            if destination != pnode and destination.can_allocate(vnode):
                path, available_bw = self.shortest_path(pnode, destination, 1)
                if len(path) != 0 and available_bw != 0.0:
                    time = vnode.get_migration_time(available_bw)
                    if self.sla_type == 'FREE' or time < vnode.get_sla_time():
                        # We can migrate
                        pnode.deallocate(vnode)
                        destination.allocate(vnode)
    
                        # Try to reconnect all vnode's adjacencies to destination
                        connect, disconnect = vnode.reconnect_adjacencies()
                        if len(connect) == 0 and len(disconnect) == 0:
                            # Return everything as it was
                            destination.deallocate(vnode)
                            if not pnode.allocate(vnode): 
                                if self.dbg: print('vishmig2')
                        else:
                            # Migration successful
                            self.rollback_list.append(
                                {'vnode': vnode, 'connect': connect, 'disconnect': disconnect, 'pnode': pnode})
                            if pnode == None:
                                if self.dbg: print "Migrate AAHAHAHAHAHA -- just added a vnode without pnode %s" % (vnode.get_id())
                            return destination
                        # Failure
        return -1

    def get_sla_breaks(self):
        sla = 0
        steal = 0
        for h in self.get_resources(MACHINE):
            sum_nodes = 0
            for vm in h.get_virtual_resources():
                if self.dbg: print "%s %s %s %s" % (vm.get_id(), vm.get_vcpu_usage(), vm.get_vcpu_network(),
                                       int(math.ceil(vm.get_vcpu_usage() + vm.get_vcpu_network())))
    
                sum_nodes = sum_nodes + int(math.ceil(vm.get_vcpu_usage() + vm.get_vcpu_network()))
                if sum_nodes > h.get_total_cpu():
                    sla = sla + 1
    
            if sum_nodes > h.get_total_cpu():
                steal = steal + (sum_nodes - h.get_total_cpu())
    
        for h in self.get_resources(SWITCH):
            sum_nodes = 0
            for vm in h.get_virtual_resources():
                sum_nodes = sum_nodes + int(math.ceil(vm.get_vcpu_usage() + vm.get_vcpu_network()))
                if sum_nodes > h.get_total_cpu():
                    sla = sla + 1
    
            if sum_nodes > h.get_total_cpu():
                steal = steal + (sum_nodes - h.get_total_cpu())
    
        return sla, steal

    def reallocate_infrastructure_mm(self):
        THRESH_UP = 19  # 80%
        THRESH_LOW = 5  # ~20%
        t = 0
        bestFitVM = None
        migrationList = []
    
        # execute MM from Buyya
        for h in self.get_physical_resources_ordered():
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
        if self.dbg: print ("MM: Now I must migrate:")
    
        for vm in migrationList:
            if self.dbg: print("VM az_id %d" % (vm.get_id()))
    
        # if self.dbg: print ("\n\n*** VI before to run the migration ***")
        # vi_before_migration = vm.get_vi()
        # vi_before_migration.print_allocation()
        # if self.dbg: print ("\n *************************** \n")
    
        if len(migrationList) > 0:
            # lets call MBFD to conclude migration
            self.mbfd_and_migration(migrationList)
    
            # if self.dbg: print ("\n\n###### VI after to run the migration ####")
            # vi_after_migration = vm.get_vi()
            # vi_after_migration.print_allocation()
            # if self.dbg: print ("\n ################################ \n")

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
                if self.dbg: print "MBFD - None: Without solution for node %s" % (vm.get_id())
                return -1
    
            if not allocatedHost.allocate(vm):
                for row in rollback:
                    pnode = row[0]
                    vnode = row[1]
                    pnode.deallocate(vnode)
    
                if self.dbg: print "MBFD: Without solution for node %s" % (vm.get_id())
                return -1
    
            rollback.append((allocatedHost, vm))
        if self.dbg: print "MBFD - moving to network allocation"
        disconnectDict = {}
        for vm in vmList:
            connect, disconnect = vm.reconnect_adjacencies()
            # no need for track connect here
            if len(connect) == 0 and len(disconnect) == 0:
                if self.dbg: print "MBFD: Without solution for network!"
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
    
        if self.dbg: print "MBFD: OK. Allocation is done with MBFD"
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
                    if not original.allocate(vm): if self.dbg: print('vishmig2')
                self.nmig += 1
                if self.dbg: print("MBFD just conclude the migration of %s from %s to %s" % (
                vm.get_id(), original.get_id(), allocatedHost.get_id()))

    def update_vcpu_usage(self):
        for h in self.host_list:
            for vm in h.get_virtual_resources():
                vm.update_usage()

    def print_datacenter(self):
        print('Physical Infrastructure')
        for pm in self.pm_list:
            spc = '----|'
            print "pm_get_usage:", pm.get_usage()
            for link in pm.get_links():
                print spc + str(link.get_destination().id) + ' bw: %.4lf' % (link.weight)

    def physical_cfg_to_file(self):
        with open('../output/physical.dat', 'w') as physical_file:
            physical_file.write(str(len(self.resources)) + '\n')
            for node in self.resources:
                physical_file.write(node.get_config() + '\n')

            nr_links = sum([len(node.get_links()) for node in self.resources]) / 2
            physical_file.write(str(int(nr_links)) + '\n')
            visited = []
            for node in self.resources:
                visited.append(node)
                for link in node.get_links():
                    if link.get_destination() not in visited:
                        to_write = '%d %d %d\n' % (node.get_id(), link.get_destination().get_id(), link.get_residual())
                        physical_file.write(to_write)

    def get_resource(self, id):
        for pnode in self.resources:
            if pnode.get_id() == id:
                return pnode
        return -1

    def get_host_list(self):
        return self.host_list

    def set_host_list(self, host_list):
        self.host_list = host_list

    def get_physical_resources_ordered(self):
        self.host_list.sort(key=lambda e: e.get_cpu())
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

    def get_dc_node_load(self):
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

    def get_total_energy_consumption(self):
        return sum([host.get_energy_consumption() for host in self.host_list if host.has_virtual_resources()])

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
