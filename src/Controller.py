#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from collections import OrderedDict
import random
# From packages:
from Chave import *
from Controller import *
from DistributedInfrastructure import *
from Demand import Demand
from Eucalyptus import *
from SLAHelper import *

"""
Class: Controller
Description: Controller is the class that manages what operations are performed
Have two subclass: global and local
"""


class Controller(object):
    def __init__(self, sla, list):
        self.sla = sla
        self.algorithm = sla.g_algorithm()
        self.logger = sla.g_logger()
        self.context_list = list

    def __repr__(self):
        return repr([self.sla, self.logger, self.algorithm, self.context_list])

    def get_algorithm(self):
        return self.algorithm

    def create_lcontroller_list(self, az_list):
        s_noa = self.sla.g_number_of_azs()
        s_mapr = self.sla.g_max_az_per_region()
        if (s_noa <= 2) and (s_mapr <= 2):
            self.logger.error("Inconsistency in SLA specifications: ", s_noa, s_mapr)
        # TODO: ver arranjo entre AZs para atribuir nas Regioes
        # best_az_arrange = helper.best_arrange(az2regions, az_list)

        # ______max_az_per_region = 4___________________________________________________________
        # %0 12/4 -> 3R(4)              -> [0:3][4:7][8:11]
        # %1 13/4 -> 2R(4)+1R(3)+1R(2)  -> [0:3][4:7][8:10][11:12]
        # %2 14/4 -> 3R(4)+1R(2)        -> [0:3][4:7][8:11][11:13]
        # %3 15/4 -> 3R(4)+1R(3)        -> [0:3][4:7][8:11][11:14]
        # ______max_az_per_region = 3___________________________________________________________
        # %0 6/3 -> 2R(3)         -> [0:2][3:5]     | 9/3 ->3R(3)       ~>[0:2][3:5][6:8]
        # %1 7/3 -> 1R(3)+2R(2)   -> [0:2][3:4][5:6]| 10/3->2R(3)+2R(2) ~>[0:2][3:5][6:7][8:9]
        # %2 8/3 -> 2R(3)+1R(2)   -> [0:2][3:5][6:7]| 11/3->3R(3)+1R(2) ~>[0:2][3:5][6:8][9:10]
        # ______max_az_per_region = 2___________________________________________________________
        # %0 6/2 -> 2R(3)         -> [0:2][3:5]     | 9/3 ->3R(3)       ~>[0:2][3:5][6:8]
        # %1 7/2 -> 1R(3)+2R(2)   -> [0:2][3:4][5:6]| 10/3->2R(3)+2R(2) ~>[0:2][3:5][6:7][8:9]
        # %0 8/2 -> 3R(3)         -> [0:2][3:5][6:8]| 11/3->3R(3) ~>[0:2][3:5][6:8][9:10]
        modulus_az_region = s_noa % s_mapr
        lcontroller_list = []
        controllers = s_noa / s_mapr

        if modulus_az_region == 0:
            for r in range(controllers):
                idx0 = r * s_mapr
                idx1 = ((r + 1) * s_mapr) - 1
                local_controller = LocalController(self.sla, r, az_list[idx0:idx1])
                lcontroller_list.append(local_controller)
                # del local_controller
            return lcontroller_list
        elif modulus_az_region == 1:
            for r in range(controllers - 1):
                idx0 = r * s_mapr
                idx1 = ((r + 1) * s_mapr) - 1
                local_controller = LocalController(self.sla, r, az_list[idx0:idx1])
                lcontroller_list.append(local_controller)
                del local_controller
            r += 1
            local_controller1 = LocalController(self.sla, r, (az_list[s_noa - 4: s_noa - 3]))
            lcontroller_list.append(local_controller1)
            r += 1
            local_controller2 = LocalController(self.sla, r, (az_list[s_noa - 2: s_noa - 1]))
            lcontroller_list.append(local_controller2)
            return lcontroller_list
        elif modulus_az_region == 2:
            for r in range(controllers):
                idx0 = r * s_mapr
                idx1 = ((r + 1) * s_mapr) - 1
                local_controller = LocalController(self.sla, r, az_list[idx0:idx1])
                lcontroller_list.append(local_controller)
                #del local_controller
            r += 1
            local_controller1 = LocalController(self.sla, r,  az_list[s_noa - 2: s_noa - 1])
            lcontroller_list.append(local_controller1)
            return lcontroller_list
        else:
            self.logger.error("Relation between 'number_of_azs' and 'max_az_per_region' must be modulus <= 2!")
            exit(1)
        return False

#################################################
#######      CLASS GLOBAL CONTROLLER      #######
#################################################
class GlobalController(Controller):
    def __init__(self, sla, demand, localcontroller_list, region_list):
        Controller.__init__(self, sla, region_list)
        self.sla = sla
        self.algorithm = sla.g_algorithm()
        self.region_list = region_list  # lista de objetos
        self.localcontroller_list = localcontroller_list  # lista de objetos
        self.demand = demand  # Objeto
        self.logger = sla.g_logger()

    def __repr__(self):
        return repr([self.sla, self.logger, self.algorithm, self.region_list, self.localcontroller_list, self.demand])

    def describe_availability_zones(self, region):
        pass

    def choose_config(self, virtual_folder):
        # Choose a random virtual file
        virtual_files = os.listdir(virtual_folder)
        return virtual_folder + virtual_files[random.randint(0, len(virtual_files) - 1)]

    def execute_mbfd(self, vi):
        return self.datacenter.mbfd(vi)

    # Interface for any algorithm, must be agnostic
    def run_algorithm_object(self, algorithm_object):
        #self.metrics()
        algorithm_object.set_demand(self.demand)
        algorithm_object.set_localcontroller(self.localcontroller_list)
        algorithm_object.set_region(self.region_list)

        if algorithm_object.run():
            return True
        return False

    def get_list_overb_amount_from_cloud(self):
        pass

    def get_total_energy_consumption_from_cloud(self):
        pass

    def get_total_SLA_violations_from_cloud(self):
        pass

    def run(self, mm):
        pass


#################################################
#######       CLASS LOCAL CONTROLLER      #######
#################################################
class LocalController(Controller):
    def __init__(self, sla, lc_id, az_list):
        Controller.__init__(self, sla, az_list)
        self.lc_id = lc_id
        self.az_list = az_list
        self.algorithm = sla.g_algorithm()
        #self.vm_dict = sla.all_vms_dict['']
        # self. =

    def __repr__(self):
        return repr([self.lc_id, self.az_list, self.algorithm])

    def get_az(self, azid):
        for az in self.az_list:
            if az.az_id == azid:
                #print 'Found azid', azid
                return az
        self.logger.error("Not found azid: %s" % (azid))
        return False

    def get_vms_dict_from_az(self, azid):
        az = self.get_az(azid)
        if az:
            return az.vms_dict
        self.logger.error("Not found az: %s" % (azid))
        return False

    def get_vm_object_from_az(self, vmid, azid):
        for vm in self.get_vms_dict_from_az(azid):
            if vm.id == vmid:
                return vm
        self.logger.error("Not found vm %s in az: %s" % (vmid, azid))
        return False
        #return (vm[vmid] for vm in self.get_vms_dict_from_az(azid) if vm.has_key(vmid))

    def execute_euca(self):
        pass

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

