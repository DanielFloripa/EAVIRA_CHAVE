#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CHAVE-Sim: The simulator for research based in clouds architecture
    CHAVE: Consolidation with High Availability on virtualyzed environments
"""
__author__ = "Daniel Camargo and Denivy Ruck"
__credits__ = "Based on eavira simulator"
__license__ = "GPL-v3"
__version__ = "2.0.1"
__maintainer__ = "Daniel Camargo"
__email__ = "daniel@colmeia.udesc.br"
__status__ = "Test"
__url__ = "http://dscar.ga/chave-sim"

from src.Physical import MACHINE,SWITCH
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
        self.pm_list.sort(key=lambda e: e.cpu)
        return list(self.pm_list)

    # def get_network_resources(self):
    #	self.sw_list.sort(key=lambda e:e.get_cpu())
    #	return list(self.sw_list)


''' TODO: document this '''


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
                if vnode.ha == -1:
                    self.insert(node)
                    break
