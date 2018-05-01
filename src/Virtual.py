#!/usr/bin/python
# -*- coding: utf-8 -*-

import random
import re
import math
import Physical

class VirtualMachine(object):
    def __init__(self, vm_id, vcpu, vram, ha, type, host_id, az_id, timestamp, lifetime, logger):
        self.logger = logger
        self.az_id = az_id
        self.vm_id = vm_id
        self.host_id = host_id
        self.state = None
        self.vcpu = vcpu
        self.usage = 1.0
        self.vram = vram
        self.lifetime = lifetime
        self.dirty_pages = random.randint(100, 1000)
        self.type = type
        self.timestamp = timestamp
        self.ha = float(ha)
        self.linked_to = []

    def __repr__(self):
        return repr(('az_id:', self.vm_id, 'vcpu:', self.vcpu, 'vram:', self.vram, 'ha:', self.ha, 'host:', self.host_id,
                     'timestamp:', self.timestamp, 'lifetime:', self.lifetime))

    def obj_id(self):  # Return the unique hexadecimal footprint from each object
        return str(self).split(' ')[3].split('>')[0]

    ##################################################
    # Input: max_it -> maximum number of iterations
    #		max_mem -> maximum amount of memory to copy
    #		p -> minimum amount of dirty pages. If it's
    #			low, stop and copy the rest
    #		bw -> available bandwidth
    # Output: time in seconds
    ##################################################
    def get_migration_time(self, bw):
        if bw == 0 or self.ha == -1:
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
        self.vcpu += vcpu
        self.vram += vram

    def remove_resources(self, vcpu, vram):
        self.vcpu -= vcpu
        self.vram -= vram

    """
    Method: check if new requested upgrade (+ or -) is supported
            by the host
    """
    # todo: move to Physical class
    def can_reconfigure(self, vcpu, vram):
        pnode = self.get_host_object()
        if self.get_vcpu() + vcpu <= pnode.cpu + self.get_vcpu() and \
                                self.get_vram() + vram <= pnode.ram + self.get_vram():
            return True
        return False

    def set_host_id(self, hostid):
        self.host_id = hostid
        self.logger.debug("Host id %s defined for %s " % (self.host_id, self.vm_id))

    def get_host_id(self):
        return self.host_id

    def get_config(self):
        return '%d %d %d' % ((self.vm_id, self.vcpu, self.vram))

    def get_vram(self):
        return self.vram

    def get_vcpu(self):
        return self.vcpu

    def get_vcpu_usage(self):
        # arredonde pra cima
        return int(math.ceil(self.vcpu * self.usage))

    def get_id(self):
        return self.vm_id

    def get_type(self):
        return self.type
