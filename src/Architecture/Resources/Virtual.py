#!/usr/bin/python
# -*- coding: utf-8 -*-

import math
import random

from Users.SLAHelper import *


class VirtualMachine(object):
    def __init__(self, vm_id, vcpu, vram, av, vtype, host_id, az_id, timestamp, lifetime, lock, logger):
        self.logger = logger
        self.vm_id = vm_id
        self.host_id = host_id
        self.az_id = az_id
        self.lc_id = None
        self.status = None
        self.pool_id = None
        self.is_locked = lock
        self.vcpu = vcpu
        self.usage = 1.0
        self.vram = vram
        self.running_time = 0
        self.lifetime = lifetime
        self._static_lifetime = lifetime
        self.last_ovcm_time = timestamp
        self._static_timestamp = timestamp  # do not change
        self.timestamp = timestamp
        self.dirty_pages = random.randint(100, 1000)
        self.type = vtype
        self.availab = float(av)
        self.in_overcomm_host = False

    def __repr__(self):
        return repr(('id:', self.vm_id, 'vcpu:', self.vcpu, 'vram:', self.vram, 'pool', self.pool_id,
                     'type:', self.type, 'ha:', self.availab, 'host:', self.host_id, self.az_id, self.lc_id,
                     'ts:', self.timestamp, 'lt:', self.lifetime))

    def obj_id(self):  # Return the unique hexadecimal footprint from each object
        return str(self).split(' ')[3].split('>')[0]

    def getattr(self):
        return [self.vm_id, self.vcpu, self.vram, self.availab, self.type, self.host_id,
                self.az_id, self.timestamp, self.lifetime, self.is_locked, self.logger]

    def get_migration_time(self, bw):
        if bw == 0 or self.availab == -1:
            return float('inf')
        # d = random.uniform(100.0, 1000.0)
        dd = self.dirty_pages
        ll = 4.0 * 1024.0  # bytes
        max_it = 30
        # vRAM GB -> bytes
        v = self.get_vram() * 1024 * 1024 * 1024
        max_mem = 2 * v
        p = 1000.0
        # Bandwidth to use => min(max(path)) in bytes/s
        bw = (bw / 8.0) * 1024 * 1024
        vmig = 0.0
        tmig = 0.0
        for i in range(max_it):
            v = (v / bw) * dd * ll
            tmig += (v / bw)
            vmig += v
            # print(v/1024.0/1024.0)
            if vmig >= max_mem or v / ll < p:
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

    def set_host_id(self, hostid):
        self.host_id = hostid
        self.logger.debug("Host id {} defined for {} t:{}, az:{}".format(self.host_id, self.vm_id, self.type, self.az_id))

    def get_host_id(self):
        return self.host_id

    def get_config(self):
        return '{} {} {}'.format(self.vm_id, self.vcpu, self.vram)

    def get_vram(self):
        return self.vram

    def get_vcpu(self):
        return self.vcpu

    def g_type(self)->str:
        if self.type == REGULAR:
            return "reG"
        elif self.type == REPLICA:
            return "reP"
        elif self.type == CRITICAL:
            return "C"
        else:
            return "None"

    def g_is_locked(self)->str:
        # return self.is_locked.__str__()[0]
        if self.is_locked:
            return "T"
        return "F"

    def get_vcpu_usage(self):
        # arredonde pra cima
        return int(math.ceil(self.vcpu * self.usage))

    def get_id(self):
        return self.vm_id

    def get_type(self):
        return self.type
