#!/usr/bin/python
# -*- coding: utf-8 -*-

from Physical import MACHINE,SWITCH
from random import randint

SLA_BASED = 'SLA'
VI_BASED = 'VI'


class BaseInfrastructure(object):
    def __init__(self):
        self.pm_list = []

    # self.sw_list = []

    def insert(self, node):
        if node.get_type() == MACHINE and node not in self.pm_list:
            self.pm_list.append(node)
        # elif node.get_type() == SWITCH and node not in self.sw_list:
        #	self.sw_list.append(node)

    def get_resources(self, *types):
        if MACHINE in types and SWITCH in types:
            return self.pm_list + self.sw_list

        resources = []
        for type in types:
            if type == MACHINE:
                resources += self.get_physical_resources()
            elif type == SWITCH:
                resources += self.get_network_resources()
        return resources

    def get_physical_resources(self):
        self.pm_list.sort(key=lambda e: e.get_cpu())
        return list(self.pm_list)

    # def get_network_resources(self):
    #	self.sw_list.sort(key=lambda e:e.get_cpu())
    #	return list(self.sw_list)


''' TODO: document '''


class SLABasedBaseInfrastructure(BaseInfrastructure):
    def __init__(self, resources):
        BaseInfrastructure.__init__(self)
        self.build_base_infrastructure(resources)

    """
    Method: base-infrastructure build policy
    Policy: selects the physical machines that host
            the VMs that can't be migrated
    """

    def build_base_infrastructure(self, resources):
        for node in resources:
            for vnode in node.get_virtual_resources():
                if vnode.get_ha() == -1:
                    self.insert(node)
                    break
