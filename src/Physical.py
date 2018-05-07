#!/usr/bin/python
# -*- coding: utf-8 -*-

import traceback
import re
import math
from itertools import permutations
from EnergyMonitor import *

SWITCH=1
MACHINE=2

S_ON = True
S_OFF = False

class PhysicalMachine(object):
    def __init__(self, host_id, cpu, ram, algorithm, az_id, logger):
        self.logger = logger
        self.az_id = az_id
        self.host_id = host_id
        self.cpu = cpu  # Esse CPU/RAM mudam com overbooking
        self.ram = ram
        self.algorithm = algorithm
        self.virtual_machine_list = []
        self.linked_to = []
        self.sla_violations_list = []
        self.acc = 0
        self.father = 0
        self.is_on = None
        self.default_cpu = cpu #  Esse não muda
        self.default_ram = ram
        self.ram2cpu = float(self.default_ram) / float(self.default_cpu)
        self.has_overbooking = False
        self.overb_max = float(2.0)
        self.overb_count = 0
        self.actual_overb = 0
        # With vms
        self.max_energy = 209.0  # 202.43 from input->energy
        self.min_energy = 118.11
        # Witout vms
        self.max_dom0 = 209.0  # 202.43 from input->energy
        self.min_dom0 = 118.11
        self.energy_table = self.__fetch_energy_info()
        self.emon = EnergyMonitor(self.min_energy, self.logger)
        #
        self.percent_cpu_management = 0.00  # 12.5% from total CPUs
        self.management_cpu = math.ceil(self.percent_cpu_management * self.default_cpu)
        self.management_ram = self.ram2cpu * self.management_cpu
        self.management_cons_dict = self.__get_management_consumption()
        self.is_hypervisor_activated = False
        self.list_energy = []
        self.queue_vms = []
        self.queue_vms.append('base')
        self.energy_cons = 0

    def __repr__(self):
        return repr((self.host_id, self.cpu, self.ram, "vml:", self.virtual_machine_list, self.algorithm, self.az_id,
                     self.sla_violations_list, self.has_overbooking, self.overb_count, self.actual_overb))

    def obj_id(self):  # Return the unique hexadecimal footprint from each object
        return str(self).split(' ')[3].split('>')[0]

    def allocate(self, vm):
        if self.can_allocate(vm):
            if not self.is_on:
                self.force_set_host_on()
            self.cpu -= vm.vcpu
            self.ram -= vm.vram
            vm.host_id = self.host_id
            self.virtual_machine_list.append(vm)
            self.emon.alloc(vm.vm_id,)
            return True
        self.sla_violations_list.append({vm.vm_id: "allocate"})
        return False

    def deallocate(self, vnode):
        try:
            self.virtual_machine_list.remove(vnode)
        except  Exception as e:
            self.logger.exception(type(e))  # ValueError:
            self.sla_violations_list.append({vnode.get_id(): "deallocate"})
            self.logger.error("Error on remove resources for: {0} on {1}".format(vnode.get_id(), self.get_id()))
            self.logger.error(traceback.format_exc())
            return False
        if self.algorithm == "CHAVE":
            self.set_host_off()
        self.cpu += vnode.get_vcpu()
        self.ram += vnode.get_vram()
        if self.has_overbooking:
            self.logger.info("Undo overb:"+self.get_id()+" cpu:"+str(self.cpu)+"...")
            if self.try_undo_overbooking(vnode):
                self.logger.info("DONE! "+self.get_id()+" has no overb.")
            else:
                self.logger.info("Not yet:"+str(self.default_cpu+self.cpu)+" still > "+str(self.default_cpu))
        return True

    def get_host_SLA_violations_total(self):
        return len(self.sla_violations_list)

    def get_host_SLA_violations_list(self):
        return self.sla_violations_list

    def get_one_SLA_violation(self, id):
        for k,v in self.sla_violations_list:
            if k == id:
                return v

    def can_overbooking(self, vm):
        overbCPU = (float(self.get_used_cpu()) + float(vm.get_vcpu())) / float(self.default_cpu)
        overbRAM = (float(self.get_used_ram()) + float(vm.get_vram())) / float(self.default_ram)
        if overbCPU <= self.overb_max and overbRAM <= self.overb_max:
            self.logger.info("WE can do overb on:" + str(self.host_id) + ", cpu:" + str(overbCPU) + " ram:" + str(overbRAM))
            return True
        #else:
            #self.sla_violations_list.append([vm.get_id, vm.get_timestamp()])
            #if self.dbg: print "Denied super-overbooking:", overbCPU, "ID", self.get_id(), vm.get_id()
        return False

    def do_overbooking(self, vm):
        overb = (float(self.default_cpu) - float(self.cpu) + float(vm.get_vcpu())) / float(self.default_cpu)
        self.logger.info("Do Overb on:"+str(self.get_id())+", for: "+vm.get_id()+" with tax:"+str(overb))
        self.has_overbooking = True
        self.cpu += vm.get_vcpu()
        self.ram += vm.get_vram()
        self.overb_count += 1
        self.actual_overb = overb

    def try_undo_overbooking(self, vm):
        overb = (float(self.get_used_cpu()) - float(vm.get_vcpu())) / float(self.default_cpu)
        if overb <= 1.0:
            self.has_overbooking = False
            self.actual_overb = 0
            return True
        else:
            self.actual_overb = overb
            self.overb_count -= 1
        return False

    def force_set_host_on(self):
        if not self.has_virtual_resources():
            self.is_on = True
            self.logger.info("NEW state: %s turned on? %s" % (self.host_id, self.is_on))
            return True
        elif self.has_virtual_resources() and not self.is_on:
            self.logger.error("Logic problem?, state OFF with resources??? Setting this ON...")
            self.is_on = True
            return False
        self.logger.critical("OOOPS: %s Resources: %s is on? %s " %
                             (self.host_id, self.has_virtual_resources(), self.is_on))
        return False

    def set_host_off(self):
        if not self.has_virtual_resources() and self.is_on is True:
            self.is_on = False
            self.logger.info("NEW state in {0}: {1} turned on? {2}".format(self.az_id, self.host_id, self.is_on))
            return True
        if self.has_virtual_resources() and self.is_on is True:
            return False
        self.logger.critical("OOOPS: %s Resources: %s is on? %s " %
                                 (self.host_id, self.has_virtual_resources(), self.is_on))
        return False

    def remove_resources(self, vcpu, vram):
        self.cpu -= vcpu
        self.ram -= vram

    def can_allocate(self, vm):
        if self.cpu >= vm.get_vcpu() and self.ram >= vm.get_vram():
            return True
        return False

    def get_vm_amount_on_host(self):
        return len(self.virtual_machine_list)

    def get_usage(self):
        used_cpu = sum([v.get_vcpu_usage() for v in self.virtual_machine_list])
        used_ram = sum([v.get_vram() for v in self.virtual_machine_list])

        return r'PM %d (%d VMs) - CPU: %.2lf%% | RAM: %.2lf%% ' % (
            self.host_id, len(self.virtual_machine_list), used_cpu / float(used_cpu + self.cpu) * 100, \
            used_ram / float(used_ram + self.ram) * 100)

    def set_debug_level(self, dbg_level):
        assert (dbg_level in [0,1,2]), "Debug Level must be" + str([0,1,2])
        self.dbg = dbg_level

    def get_used_cpu(self):
        return sum([vm.get_vcpu() for vm in self.virtual_machine_list])

    def get_used_ram(self):
        return sum([vm.get_vram() for vm in self.virtual_machine_list])

    def get_id(self):
        return self.host_id

    def get_type(self):
        return self.algorithm

    def get_virtual_resources(self):
        return self.virtual_machine_list

    def has_restricted_resources(self):
        for vnode in self.get_virtual_resources():
            if vnode.get_sla_time() == -1:
                return True
        return False

    def get_cpu_usage(self):
        return sum([vnode.get_vcpu_usage() for vnode in self.get_virtual_resources()])

    def get_total_ram(self):
        return self.ram + self.get_used_ram()

    def get_total_cpu(self):
        return self.cpu + self.get_used_cpu()

    def has_virtual_resources(self):
        if len(self.get_virtual_resources()) > 0:
            return True
        return False

    def get_min_energy(self):
        if self.has_virtual_resources():
            return self.min_energy
        return self.min_dom0

    def get_max_energy(self):
        if self.has_virtual_resources():
            return self.max_energy
        return self.max_dom0

    def activate_hypervisor_dom0(self):
        if not self.is_hypervisor_activated:
            self.cpu = self.cpu - self.management_cpu
            self.ram = self.ram - self.management_ram
            #self.logger.debug("dom0 activated for %s cpu:%s ram%s mang:%s" %
            #                  (self.host_id, self.cpu, self.ram, self.management_cpu))
            self.is_hypervisor_activated = True
            return True
        return False

    def get_energy_consumption(self):
        if (not self.has_virtual_resources()) and (self.is_on is True):
            self.logger.info("PM on empty Energy: Return min energy")
            return self.get_min_energy()
        elif not self.is_on:
            self.logger.info("PM off Energy: Return {}".format(0))
            return 0.0
        else:
            p = (float(self.default_cpu) - float(self.cpu)) / float(self.default_cpu)
            vm_cons = self.get_total_vcpu_energy_usage()
            ret = vm_cons + (self.management_cons_dict['avg'] * p)
            if ret > self.get_max_energy():
                if ret > self.get_max_energy() + 1:
                    self.logger.info("Energy breaking for %s->"
                                     "(%s), vm_cons:%s, mngm_c:%s, p:%s=%s-%s/def" %
                                     (self.get_id(), ret, vm_cons, self.management_cons_dict['avg'],
                                      p, self.default_cpu, self.cpu))
                return self.get_max_energy()
            return ret

    def __get_management_consumption(self):
        energy_list = self.energy_table.values()
        soma_list = []
        for i in range(len(energy_list)):
            soma = 0
            window = []
            for j in range(int(self.management_cpu)):
                k = j + i
                if k < len(energy_list):
                    window.append(energy_list[k])
            for j in range(int(self.management_cpu) - 1):
                try:
                    soma += abs(window[j + 1] - window[j])
                except IndexError:
                    return {'avg': (sum(soma_list) / float(len(soma_list))),
                            'max': max(soma_list),
                            'min': min(soma_list),
                            'list': soma_list
                            }
            soma_list.append(soma)
        return {'avg': (sum(soma_list) / float(len(soma_list))),
                'max': max(soma_list),
                'min': min(soma_list),
                'list': soma_list}

    def get_total_vcpu_energy_usage(self):
        # due to overbooking we can have more vcpus than previously discussed.
        # In this case, I'm assuming the power consumption isn't impacted and returning the max value
        usage = sum([vm.get_vcpu_usage() for vm in self.get_virtual_resources()])
        return self.energy_table[usage]

    @staticmethod
    def __fetch_energy_info(self):
        host_energy = open('../input/energy/processador.dad', 'r')
        host_table = dict()
        temp_list = []
        for line in host_energy:
            info = re.findall(r'[-+]?\d*\.\d+|\d+', line)
            ncpu = int(info[0])
            venergy = float(info[1])
            host_table[ncpu] = venergy
        host_energy.close()

        return host_table  # , 'NET': net_table}


    """
    Method: returns the fraction of energy that's being paid by the
            provider, i.e, what's left of C_g and C_min, which, in this
            model, are shared costs. The other costs are individual.
    """
    '''def get_wasted_energy(self):
        if not self.has_virtual_resources() and not self.is_on:
            self.logger.info("ENERGY: Wasted is 0.00 from %s" % (self.host_id))
            return 0.0  # servidor esta desligado

        if not self.has_virtual_resources() and self.is_on is True:
            self.logger.info("ENERGY: Wasted is minimum from %s" % (self.host_id))
            return self.get_min_energy()

        remaining_vcpu = self.get_total_cpu() - sum([vnode.get_vcpu_usage() for vnode in self.get_virtual_resources()])

        if remaining_vcpu < 0:
            remaining_vcpu = self.get_total_cpu()
        p = float(remaining_vcpu) / float(self.get_total_cpu())
        mangmt = 0
        # management is only calaculated when there is at least one VM running, otherwise 0
        if self.has_virtual_resources():
            mangmt = self.get_management_consumption() * p
        min = self.get_min_energy() * p
        ret = mangmt + min

        if ret > self.get_max_energy():
            self.logger.warning("Wasted energy is breaking our account! Returning max!")
            return self.get_max_energy()
        return ret

    # TODO: From virtual
    def get_energy_consumption_virtual(self, vm):
        p = float(vm.get_vcpu_usage()) / float(self.get_total_cpu())
        u_min = self.get_min_energy() * p
        u_g = self.get_management_consumption() * p
        u_p = vm.get_cpu_energy_usage() - self.get_min_energy()
        v = u_min + u_g + u_p
        if v > self.get_max_energy():
            return self.get_max_energy()
        return v'''
