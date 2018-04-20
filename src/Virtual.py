#!/usr/bin/python
# -*- coding: utf-8 -*-

import random
import re
import math
import Physical

class VirtualMachine(object):
    def __init__(self, vm_id, vcpu, vram, ha, type, host, az_id, timestamp, lifetime, logger):
        self.logger = logger
        self.az_id = az_id
        self.id = vm_id
        self.state = None # old: az_id.split('-')[2]
        self.vcpu = vcpu
        self.usage = 1.0  # starts with 100
        self.vram = vram
        self.lifetime = lifetime
        self.dirty_pages = random.randint(100, 1000)
        self.type = type
        self.timestamp = timestamp
        self.host = host
        self.ha = float(ha)
        self.linked_to = []
        self.energy_table = self.fetch_energy_info()
        self.dbg = False
        self.host_obj = None

    def __repr__(self):
        return repr(('az_id:',self.id, 'vcpu:',self.vcpu, 'vram:',self.vram, 'ha:',self.ha,'host:',self.host,
                     'timestamp:',self.timestamp, 'lifetime:', self.lifetime))

    def set_host_object(self, host_obj):
        self.host_obj = host_obj

    def get_host_object(self):
        return self.host_obj

    def get_parameters(self):
        return {'az_id': self.id, 'vcpu': self.vcpu, 'vram': self.vram, 'ha': self.ha, 'type': self.type,
                'host': self.host, 'timestamp': self.timestamp, 'lifetime': self.lifetime}

    ##################################################
    # Input: max_it -> maximum number of iterations
    #		max_mem -> maximum amount of memory to copy
    #		p -> minimum amount of dirty pages. If it's
    #			low, stop and copy the rest
    #		bw -> available bandwidth
    # Output: time in seconds
    ##################################################
    def get_migration_time(self, bw):
        if bw == 0 or self.get_ha() == -1:
            return float('inf')

        # d = random.uniform(100.0, 1000.0)
        d = self.dirty_pages
        l = 4.0 * 1024.0  # bytes

        max_it = 30
        # vRAM GB -> bytes
        v = self.get_vram() * 1024 * 1024 * 1024
        max_mem = 2 * v
        p = 1000.0

        # Bandwidth to use => min(max(path)) in bytes/s
        bw = (bw / 8.0) * 1024 * 1024

        vmig = 0.0
        tmig = 0.0
        t = 0.0
        for i in range(max_it):
            t = v / bw
            v = t * d * l
            tmig += t
            vmig += v

            # print(v/1024.0/1024.0)

            if vmig >= max_mem or v / l < p:
                break
        tdown = v / bw
        tmig += tdown
        return tmig

    def add_resources(self, vcpu, vram):
        self.set_vcpu(self.get_vcpu() + vcpu)
        self.set_vram(self.get_vram() + vram)

    def remove_resources(self, vcpu, vram):
        self.set_vcpu(self.get_vcpu() - vcpu)
        self.set_vram(self.get_vram() - vram)

    """
    Method: check if new requested upgrade (+ or -) is supported
            by the host
    """

    def can_reconfigure(self, vcpu, vram):
        pnode = self.get_host_object()
        if self.get_vcpu() + vcpu <= pnode.get_cpu() + self.get_vcpu() and \
                                self.get_vram() + vram <= pnode.get_ram() + self.get_vram():
            return True
        return False

    def get_ha(self):
        return self.ha

    def get_cpu(self):
        return self.vcpu

    def get_timestamp(self):
        return self.timestamp

    def get_physical_host(self):
        return self.host

    def get_state(self):
        return self.state

    def get_config(self):
        return '%d %d %d' % ((self.id, self.vcpu, self.vram))

    def get_vram(self):
        return self.vram

    def get_vcpu(self):
        return self.vcpu

    def get_vcpu_usage(self):
        return int(math.ceil(self.vcpu * self.usage))

    def get_id(self):
        return self.id

    def get_type(self):
        return self.type

    def set_debug_level(self, dbg_level):
        assert (dbg_level in [0,1,2]), "Debug Level must be" + str([0,1,2])
        self.dbg = dbg_level

    def set_state(self, state):
        self.state = state

    def set_az(self, az_id):
        self.az_id = az_id

    def set_vram(self, vram):
        self.vram = vram

    def set_vcpu(self, vcpu):
        self.vcpu = vcpu

    def set_physical_host(self, physical_host_id):
        self.host = physical_host_id

    def get_energy_consumption_estimate(self, pnode):
        p = float(self.get_vcpu_usage()) / float(pnode.get_total_cpu())
        U_min = pnode.get_min_energy() * p
        U_g = pnode.get_management_consumption() * p
        U_p = self.get_cpu_energy_usage() - pnode.get_min_energy()
        v = U_min + U_g + U_p

        if v > pnode.get_max_energy():
            return pnode.get_max_energy()

        return v

    def get_energy_consumption_virtual(self):
        pnode = self.get_host_object()
        if pnode == None:
            self.logger.error("There is something wrong!!!! pnode is None for vm "+str(self.get_id()))
        p = float(self.get_vcpu_usage()) / float(pnode.get_total_cpu())
        u_min = pnode.get_min_energy() * p
        u_g = pnode.get_management_consumption() * p
        u_p = self.get_cpu_energy_usage() - pnode.get_min_energy()
        v = u_min + u_g + u_p

        if v > pnode.get_max_energy():
            return pnode.get_max_energy()
        return v

    def get_cpu_energy_usage(self):
        # due to overbooking we can have more vcpus than previouslly discussed.
        # #In this case, I'm assuming the power consumption isn't impacted and returning the max value
        u = self.get_vcpu_usage()
        m = 0
        for k in self.energy_table['HOST']:
            if k > m:
                m = k
        if u > m:
            return self.energy_table['HOST'][m]
        else:
            return self.energy_table['HOST'][u]

    def fetch_energy_info(self):
        host_energy = open('../input/energy/processador.dad', 'r')

        host_table = {}
        for line in host_energy:
            info = re.findall(r'[-+]?\d*\.\d+|\d+', line)
            ncpu = int(info[0])
            venergy = float(info[1])

            host_table[ncpu] = venergy
        host_energy.close()

        same_energy = open('../input/energy/cenario2.dad', 'r')

        same_table = {}
        for line in same_energy:
            info = re.findall(r'[-+]?\d*\.\d+|\d+', line)
            bw = int(info[0])
            venergy = float(info[1])

            same_table[bw] = venergy
        same_energy.close()

        apart_energy = open('../input/energy/cenario4.dad', 'r')

        apart_table = {}
        for line in apart_energy:
            info = re.findall(r'[-+]?\d*\.\d+|\d+', line)
            bw = int(info[0])
            venergy = float(info[1])

            apart_table[bw] = venergy
        apart_energy.close()

        net_table = {'SAME': same_table, 'APART': apart_table}

        return {'HOST': host_table, 'NET': net_table}


########################################
# Used inheritance otherwiser i'd need to
#	write the same methods again. Don't
#	know if it's right, my OOP sucks
########################################
#class VirtualMachine(VirtualResource):
#    def __init__(self, az_id, vcpu, vram, ha, av, type, physical_host, az, timestamp, lifetime, logger):
#        VirtualResource.__init__(self, az_id, vcpu, vram, ha, av, type, physical_host, az, timestamp, lifetime, logger)

