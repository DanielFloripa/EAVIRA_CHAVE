#!/usr/bin/env python
# -*- coding: utf-8 -*-
import operator
import os
import random

from Architecture.Infra import *

"""
Class: Architecture
Description: Architecture is the class that manages what operations are performed
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

    def obj_id(self):  # Return the unique hexadecimal footprint from each object
        return str(self).split(' ')[3].split('>')[0]

    def get_algorithm(self):
        return self.algorithm

    # Todo: review this code to use later
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
                # del local_controller
            r += 1
            local_controller1 = LocalController(self.sla, r,  az_list[s_noa - 2: s_noa - 1])
            lcontroller_list.append(local_controller1)
            return lcontroller_list
        else:
            self.logger.error("Relation between 'number_of_azs' and 'max_az_per_region' must be modulus <= 2!")
            # exit(1)
            raise ConnectionAbortedError
        return False


#################################################
#      CLASS GLOBAL CONTROLLER
#################################################
class GlobalController(Controller):
    def __init__(self, sla, demand, localcontroller_d, region_d=None):
        Controller.__init__(self, sla, region_d)
        self.sla = sla
        self.algorithm = sla.g_algorithm()
        if region_d is None:
            self.region_d = localcontroller_d
        else:
            self.region_d = region_d
        self.localcontroller_d = localcontroller_d
        self.demand = demand
        self.logger = sla.g_logger()
        self.az_list = self.__discover_az_list()
        self.az_2_lc = self.__set_lc_id_from_az_id()

    def __repr__(self):
        return repr([self.sla, self.logger, self.algorithm, self.region_d, self.localcontroller_d, self.demand])

    def obj_id(self):  # Return the unique hexadecimal footprint from each object
        return str(self).split(' ')[3].split('>')[0]

    def __discover_az_list(self):
        az_list = []
        for lc_id, lc_obj in self.localcontroller_d.items():
            for az in lc_obj.az_list:
                az.lc_id = lc_obj.lc_id
                az_list.append(az)
        return az_list

    def __set_lc_id_from_az_id(self):
        az_2_lc = dict()
        for lci, lco in self.localcontroller_d.items():
            for az in lco.az_list:
                az_2_lc[az.az_id] = lci
        return az_2_lc

    def get_lc_id_from_az_id(self, az_id):
        return self.az_2_lc[az_id]

    def create_new_host(self, az_id, host_state=HOST_ON):
        az = self.get_az(az_id)
        if az.add_new_host_to_list(host_state):
            return True
        return False

    def get_az_list(self):
        return self.az_list

    def get_regions_d(self):
        return self.region_d

    def get_localcontroller_d(self):
        return self.localcontroller_d

    def get_localcontroller_from_lcid(self, lc_id):
        return self.localcontroller_d[lc_id]

    def get_az(self, azid):
        for az in self.az_list:
            if az.az_id == azid:
                return az
        self.logger.error("Not found azid: {}".format(azid))
        return False

    def get_vms_dict_from_az(self, azid):
        az = self.get_az(azid)
        if isinstance(az, AvailabilityZone):
            return az.op_dict
        self.logger.error("Not found az: {}".format(azid))
        return False

    def get_vm_object_from_az(self, vmid, azid):
        for vm in self.get_vms_dict_from_az(azid).values():
            if vm.vm_id == vmid:
                return vm
        self.logger.error("Not found vm {} in az: {}".format(vmid, azid))
        return False

    def get_az_from_lc(self, az_id):
        for lc_id, lc_obj in self.localcontroller_d.items():
            for az in lc_obj.az_list:
                if az.az_id == az_id:
                    return az

    @staticmethod
    def choose_config(virtual_folder):
        # Choose a random virtual file
        virtual_files = os.listdir(virtual_folder)
        return virtual_folder + virtual_files[random.randint(0, len(virtual_files) - 1)]

    # Todo:
    def get_list_overcom_amount_from_cloud(self):
        return 0.3

    def get_total_energy_consumption_from_cloud(self):
        return 0.2

    def get_total_SLA_violations_from_cloud(self):
        return 0.1


#################################################
#       CLASS LOCAL CONTROLLER
#################################################
class LocalController(Controller):
    def __init__(self, sla, lc_id, az_list):
        Controller.__init__(self, sla, az_list)
        self.lc_id = lc_id
        self.az_list = az_list
        self.az_id_list = self.create_az_id_list()
        self.az_dict = self.def_az_dict_from_list()
        self.algorithm = sla.g_algorithm()
        self.replicas_dict = OrderedDict()
        self.ordered_replicas_dict = OrderedDict()
        self.in_execution_replicas_dict = OrderedDict()
        self.is_az_setted_with_lcid = self.__set_lcid_on_az()

    def __repr__(self):
        return repr([self.lc_id, self.az_list, self.algorithm])

    def obj_id(self):
        # Return the unique hexadecimal footprint from each object
        return str(self).split(' ')[3].split('>')[0]

    def def_az_dict_from_list(self):
        az_dict = dict()
        for az in self.az_list:
            az_dict[az.get_id()] = az
        return az_dict

    def __set_lcid_on_az(self):
        for az in self.az_list:
            if az.lc_id is None:
                az.lc_id = self.lc_id
        return True

    def get_az_list(self):
        return self.az_list

    def get_id(self):
        return self.lc_id

    def put_critical_vms_on_replicas_dict(self, vm):
        self.replicas_dict[vm.vm_id] = vm
        # reboot/clean this dict
        self.ordered_replicas_dict.clear()
        for vm in (sorted(self.replicas_dict.values(),
                          key=operator.attrgetter('timestamp'),
                          reverse=True)):
            self.ordered_replicas_dict[vm.get_id()] = vm
        # x = ordered_replicas_dict.popitem()

    def pop_critical_vms_from_replicas_dict(self):
        rem = self.ordered_replicas_dict.popitem()
        self.logger.debug("Removed {} from replicas Dict".format(rem))
        return rem

    def get_oredered_replicas_dict(self):
        return self.ordered_replicas_dict

    def create_az_id_list(self):
        az_ids = []
        for az in self.az_list:
            az_ids.append(az.get_id())
        return az_ids

    def get_az(self, azid):
        for az in self.az_list:
            if az.az_id == azid:
                return az
        self.logger.error("Not found azid: {}".format(azid))
        return False

    def get_vms_dict_from_az(self, azid):
        az = self.get_az(azid)
        if az:
            return az.vms_dict
        self.logger.error("Not found az: {}".format(azid))
        return False

    def get_vm_object_from_az(self, vmid, azid):
        for vm in self.get_vms_dict_from_az(azid):
            if vm.vm_id == vmid:
                return vm
        self.logger.error("Not found vm {} in az: {}".format(vmid, azid))
        return False

    def execute_elasticity(self):
        pass
