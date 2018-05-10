class MBFD:
    def __init__(self, a):
        self.a = a

    # def build_base_infrastructure(self):
    # self.base_infrastructure = None
    # if self.bi_type == VI_BASED:
    #	if len(self.vi_list) >= 1:
    #		self.base_infrastructure = VIBasedBaseInfrastructure(self.vi_list)
    # self.base_infrastructure = SLABasedBaseInfrastructure(self.resources)

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
            minPower = vnode.get_host_id().get_max_energy()
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
            if new_replica.get_host_id() == None:
                for link in new_replica.get_links():
                    vnode2 = link.get_destination()
                    new_replica.disconnect(vnode2)
                    vnode2.disconnect(new_replica)
            else:
                self.nrepl += 1
                vi.add_virtual_resource(new_replica)
                if self.dbg: print("OK, just replicated a new VM with az_id %d hosted by %d" % (
                    new_replica.get_id(), new_replica.get_host_id()))


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
                                print("Migrate AAHAHAHAHAHA -- just added a vnode without pnode %s"
                                      % (vnode.get_id()))
                            return destination
                        # Failure
        return -1


    def get_sla_breaks(self):
        sla, steal = 0, 0
        for h in self.resources:
            sum_nodes = 0
            for vm in h.get_virtual_resources():
                if self.dbg: print("%s %s %s %s" % (vm.get_id(), vm.get_vcpu_usage(), vm.get_vcpu_network(),
                                                    int(math.ceil(vm.get_vcpu_usage() + vm.get_vcpu_network()))))
                sum_nodes = sum_nodes + int(math.ceil(vm.get_vcpu_usage() + vm.get_vcpu_network()))
                if sum_nodes > h.get_total_cpu():
                    sla = sla + 1
            if sum_nodes > h.get_total_cpu():
                steal = steal + (sum_nodes - h.get_total_cpu())
        '''for h in self.get_resources(SWITCH):
            sum_nodes = 0
            for vm in h.get_virtual_resources():
                sum_nodes = sum_nodes + int(math.ceil(vm.get_vcpu_usage() + vm.get_vcpu_network()))
                if sum_nodes > h.get_total_cpu():
                    sla = sla + 1
            if sum_nodes > h.get_total_cpu():
                steal = steal + (sum_nodes - h.get_total_cpu())'''
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
        max_power = self.resources[0].get_max_energy()
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
            if allocatedHost is not None:
                # migrate vm
                original = vm.get_physical_host()
                original.deallocate(vm)
                allocatedHost.allocate(vm)

                # Try to reconnect all vnode's adjacencies to destination
                connect, disconnect = vm.reconnect_adjacencies()
                if len(connect) == 0 and len(disconnect) == 0:
                    # Return everything as it was
                    allocatedHost.deallocate(vm)
                    if not original.allocate(vm):
                        print('vishmig2')
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