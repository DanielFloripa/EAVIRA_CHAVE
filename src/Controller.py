#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import timeit
import sys
import subprocess
import re
import time
import random

from Datacenter import Datacenter
from Algorithms import ksp_yen, dijkstra

"""
Class: Controller
Description: Controller is the class that manages
			what operations are performed
"""


class Controller(object):
    def __init__(self, datacenter):
        self.datacenter = datacenter

    def reallocate_infrastructure_mm(self):
        self.datacenter.reallocate_infrastructure_mm()

    def execute_elasticity(self, delete_requests, recfg_requests, repl_requests, offline):
        repl_requests_count = 0
        recfg_requests_count = 0
        delete_requests_count = 0

        new_delete_requests = []
        for delete in delete_requests:
            delete_requests_count += 1
            vi = self.datacenter.get_vi(delete['vi'])
            if vi != -1:
                new_vnode = vi.get_virtual_resource(delete['vnode'])
                if new_vnode != -1:
                    new_delete_requests.append(new_vnode)
        self.datacenter.answer_delete_requests(new_delete_requests)

        new_recfg_requests = []
        for recfg in recfg_requests:
            recfg_requests_count += 1
            vi = self.datacenter.get_vi(recfg['vi'])
            if vi != -1:
                new_vnode = vi.get_virtual_resource(recfg['vnode'])
                if new_vnode != -1:
                    recfg['vnode'] = new_vnode
                    new_recfg_requests.append(recfg)

        new_repl_requests = []
        for repl in repl_requests:
            repl_requests_count += 1
            vi = self.datacenter.get_vi(repl['vi'])
            if vi != -1:
                new_vnode = vi.get_virtual_resource(repl['vnode'])
                if new_vnode != -1:
                    new_repl_requests.append(new_vnode)

        # call MM, MBFD and Buyya solutions
        self.datacenter.answer_reconfiguration_requests_mbfd(new_recfg_requests)
        self.datacenter.answer_replication_requests_mbfd(new_repl_requests)

    def choose_config(self, virtual_folder):
        # Choose a random virtual file
        virtual_files = os.listdir(virtual_folder)
        return virtual_folder + virtual_files[random.randint(0, len(virtual_files) - 1)]

    def execute_mbfd(self, vi):
        return self.datacenter.mbfd(vi)

    def get_datacenter(self):
        return self.datacenter
