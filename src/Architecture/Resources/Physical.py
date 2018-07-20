#!/usr/bin/python
# -*- coding: utf-8 -*-

import math
import re
import sys
from collections import OrderedDict

from Architecture.Resources.EnergyMonitor import *
from Users.SLAHelper import *


class PhysicalMachine(object):
    def __init__(self, host_id, cpu, ram, algorithm, az_id, sla, logger):
        self.logger = logger
        self.sla = sla
        self.az_id = az_id
        self.host_id = host_id
        self.cpu = cpu  # Esse CPU/RAM mudam com overcommitting
        self.ram = ram
        self.algorithm = algorithm
        self.virtual_machine_list = []
        self.virtual_machine_dict = dict()
        self.power_state = None
        self.default_cpu = cpu  # Esse não muda
        self.default_ram = ram
        self.ram2cpu = float(self.default_ram) / float(self.default_cpu)
        self.has_overcommitting = False
        self.overcom_max = float(sla.g_vcpu_per_core())
        self.overcom_count = 0
        self.actual_overcom = 0
        self.timestamp_original_d = dict()
        # With vms
        self.max_energy = 209.0  # 202.43 from input->energy
        self.min_energy = 118.11
        # Without vms
        self.max_dom0 = 209.0  # 202.43 from input->energy
        self.min_dom0 = 118.11
        self.energy_table = self.__fetch_energy_info()
        if self.sla.g_enable_emon():
            self.emon = EnergyMonitor(self.min_energy,
                                      'em' + K_SEP + self.az_id + K_SEP + self.host_id,
                                      self.logger)
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
                     self.has_overcommitting, self.overcom_count, self.actual_overcom))

    def obj_id(self):  # Return the unique hexadecimal footprint from each object
        return str(self).split(' ')[3].split('>')[0]

    def allocate(self, vm):
        if self.can_allocate(vm):
            if self.power_state is HOST_OFF:
                self.force_set_host_on()
            self.cpu -= vm.vcpu
            self.ram -= vm.vram
            vm.host_id = self.host_id
            self.virtual_machine_list.append(vm)
            self.virtual_machine_dict[vm.vm_id] = vm
            if self.sla.g_enable_emon():
                this_energy = self.get_cpu_energy_usage()
                self.emon.alloc(vm.vm_id, vm.timestamp, this_energy, log=True)
            return True
        return False

    def deallocate(self, vm, timestamp=None, who_calls='', set_state=HOST_ON):
        try:
            self.virtual_machine_list.remove(vm)
            del self.virtual_machine_dict[vm.vm_id]
        except Exception as e:
            self.logger.exception(e)  # ValueError:
            self.logger.error("Error on remove resources for: {} {} =? {} called by {} {} -> vm:{} -> host:{}".format(
                vm.vm_id, vm.host_id, self.host_id, sys._getframe(1).f_code.co_name, who_calls, vm, self))
            # self.logger.error(traceback.format_exc())
            return False
        if set_state is HOST_OFF:
            self.try_set_host_off()
        self.cpu += vm.get_vcpu()
        self.ram += vm.get_vram()
        if self.has_overcommitting:
            if self.try_undo_overcommitting(vm):
                self.logger.info("Done! Overcom:{} cpu: {}".format(self.get_id(), self.cpu))
            else:
                self.logger.info("Not yet: {} still > {} ".format(self.default_cpu+self.cpu, self.default_cpu))
        if self.sla.g_enable_emon():
            this_energy = self.get_cpu_energy_usage()
            self.emon.dealloc(vm.vm_id, timestamp, this_energy, log=True)
        return True

    def can_allocate(self, vm):
        if self.cpu >= vm.get_vcpu() and self.ram >= vm.get_vram():
            return True
        else:
            self.logger.debug("{}\tCan't allocate v:{} on h:{} -> h.cpu:{} < v.cpu:{} and h.ram:{} < v.ram:{}".format(
                self.az_id, vm.vm_id, self.host_id, self.cpu, vm.get_vcpu(), self.ram, vm.get_vram()))
        return False

    def refresh_all_vms_for_overcom(self, menos_esta, tax, global_time):
        if tax > 1.0:
            time = 0
            velocidade = 1.0 / tax  # sempre maior que 50km/h
            for vmid, vmobj in self.virtual_machine_dict.items():
                old_ts = vmobj.lifetime
                vmobj.running_time += (global_time - vmobj.last_ovcm_time) / vmobj.velocidade
                #if self.overcom_count == 0:
                #    self.timestamp_original_d[vmid] = old_ts
                #if vmid == menos_esta:
                #    pass
                vmobj.last_ovcm_time = global_time
                vmobj.velocidade = velocidade
                vmobj.lifetime += vmobj.running_time  # int(old_ts * tax)
                vmobj.in_overcomm_host = True
                time += abs(old_ts-vmobj.lifetime)
                self.logger.info("{}\tChanging ts:{} from {} to {}, increment {}t".format(
                    self.az_id, old_ts, vmid, vmobj.lifetime, time))
            return True
        self.logger.warning("Tax must be grather than 1.0. Is {} for {}".format(tax, menos_esta))
        return False

    def check_overcom(self):
        # Todo: in future test and remove redundancy: has and actual
        if self.sla.g_can_do_overcommitting() is True and (self.actual_overcom > 1 or self.has_overcommitting):
            return self.actual_overcom
        return 0

    def can_overcommitting(self, vm):
        if self.sla.g_can_do_overcommitting() is True:
            used = self.get_used_cpu()
            overcom_cpu = (float(used) + float(vm.get_vcpu())) / float(self.default_cpu)
            # overcom_ram = (float(self.get_used_ram()) + float(vm.get_vram())) / float(self.default_ram)
            if overcom_cpu <= self.overcom_max:  # and overcom_ram <= self.overcom_max:
                self.logger.info("Yes, we can overcommit on: {}, will be: ov_cpu: {}".format(self.host_id, overcom_cpu))
                return True
            self.logger.debug("{} Pass: overcomCPU ((Ucpu:{} + Vcpu:{}) / Dcpu:{} = {} > overcom_max {}".format(
                self.host_id, used, vm.get_vcpu(), self.default_cpu, overcom_cpu, self.overcom_max, self.overcom_max))
        # elif self.can_allocate(vm):
        #    return True
        else:
            return False

    # todo: review this code
    def do_overcommitting(self, vm):
        used = self.get_used_cpu()
        overcom = (float(used) + float(vm.get_vcpu())) / float(self.default_cpu)
        metric_ovc = {'gvt': vm.timestamp,
                      'val_0': overcom,
                      'info': "Do: {}".format(self.host_id)}
        self.sla.metrics.set(self.az_id, 'overc_l', tuple(metric_ovc.values()))

        self.has_overcommitting = True
        # Add just the amount required for this VM, so the allocate() will not claim
        self.cpu += vm.get_vcpu()
        self.ram += vm.get_vram()
        self.overcom_count += 1
        self.actual_overcom = overcom
        self.refresh_all_vms_for_overcom(vm.vm_id, overcom)
        vm.in_overcomm_host = True
        self.logger.info("Done! on: {}, for: {}, tax: (Ucpu:{}+Vcpu:{})/Dcpu:{} = {}".format(
            self.get_id(), vm.get_id(), used, vm.get_vcpu(), self.default_cpu, overcom))

    def try_undo_overcommitting(self, vm):
        used = self.get_used_cpu()
        ret = False
        overcom = (float(used) - float(vm.get_vcpu())) / float(self.default_cpu)
        self.actual_overcom = overcom
        # self.overcom_count -= 1
        if overcom <= 1.0:
            self.has_overcommitting = False
            times = self.refresh_all_vms_for_undo_overcom(overcom, reset=True)
            ret = True
        else:
            times = self.refresh_all_vms_for_undo_overcom(overcom)
        metric_ovc = {'gvt': vm.timestamp,
                      'val_0': overcom,
                      'info': "Undo: {}".format(self.host_id)}
        self.sla.metrics.set(self.az_id, 'overc_l', tuple(metric_ovc.values()))
        self.logger.info("Undo overcommit for {} time:{}t".format(self.host_id, times))
        return ret

    def refresh_all_vms_for_undo_overcom(self, old_tax, new_tax, global_time, reset=False):
        times = 0
        tax = 1 - (new_tax / old_tax)
        velocidade = 1.0 / new_tax

        for vmid, vmobj in self.virtual_machine_dict.items():
            old_ts = vmobj.lifetime
            vmobj.running_time += (global_time - vmobj.last_ovcm_time) / vmobj.velocidade
            if reset is False:
                vmobj.lifetime = int(old_ts * tax)
            else:
                vmobj.lifetime += vmobj.running_time

            times += abs(old_ts - vmobj.lifetime)
            vmobj.in_overcomm_host = False
            self.logger.info("{}\tUndo Overcom, changing ts:{} from {} to {}, saving {}t".format(
                self.az_id, old_ts, vmid, vmobj.lifetime, times))
        return times

    def has_available_resources(self):
        if self.sla.g_can_do_overcommitting() and self.actual_overcom < self.overcom_max:
            return True
        elif not self.sla.g_can_do_overcommitting() and self.cpu > 0:
            return True
        else:
            pass
        return False

    def force_set_host_on(self):
        if not self.has_virtual_resources():

            if self.power_state == HOST_OFF:
                self.logger.info("Change state in {}: {} turned ON".format(self.az_id, self.host_id))
            self.power_state = HOST_ON
            self.activate_hypervisor_dom0(log=True)
            return True
        elif self.has_virtual_resources() and not self.power_state:
            self.logger.error("Logic problem?, state OFF with resources??? Setting this ON...")
            self.power_state = HOST_ON
            return False
        self.logger.error("OOOPS: {} Resources: {} is on? {} ".format(
                             self.host_id, self.has_virtual_resources(), self.power_state))
        return False

    def try_set_host_off(self):
        if not self.has_virtual_resources() and self.power_state is HOST_ON:
            self.power_state = HOST_OFF
            self.logger.info("Change state in {}: {} turned OFF".format(self.az_id, self.host_id))
            return True
        if self.has_virtual_resources() and self.power_state is HOST_ON:
            return False
        self.logger.error("OOOPS: {} Resources: {} is on? {} ".format(
                             self.host_id, self.has_virtual_resources(), self.power_state))
        return False

    def remove_resources(self, vcpu, vram):
        self.cpu -= vcpu
        self.ram -= vram

    def get_used_cpu(self):
        return sum([vm.get_vcpu() for vm in self.virtual_machine_list])

    def get_used_ram(self):
        return sum([vm.get_vram() for vm in self.virtual_machine_list])

    def get_id(self):
        return self.host_id

    def get_type(self):
        return self.algorithm

    def has_restricted_resources(self):
        for vm in self.virtual_machine_list:
            if vm.is_locked:
                return True
        return False

    def get_cpu_usage(self):
        return sum([vm.get_vcpu_usage() for vm in self.virtual_machine_list])

    def get_total_ram(self):
        return self.ram + self.get_used_ram()

    def get_total_cpu(self):
        return self.cpu + self.get_used_cpu()

    def has_virtual_resources(self):
        if len(self.virtual_machine_list) > 0:
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

    def activate_hypervisor_dom0(self, log=False):
        if not self.is_hypervisor_activated:
            self.cpu = self.cpu - self.management_cpu
            self.ram = self.ram - self.management_ram
            if log:
                self.logger.debug("dom0 activated for {} cpu:{} ram:{} mngMT:{}".format(
                              self.host_id, self.cpu, self.ram, self.management_cpu))
            self.is_hypervisor_activated = True
            return True
        return False

    def get_emon_hour(self):
        if self.power_state and self.sla.g_enable_emon():
            return self.emon.get_watt_hour()
        else:
            return 0

    def get_emon_partial(self):
        if self.sla.g_enable_emon():
            return self.emon.get_watt_partial()
        return False

    def get_emon_consumption_list(self):
        if self.sla.g_enable_emon():
            return self.emon.get_consumption_list()
        return False

    def get_emon_total_consumption(self):
        if self.sla.g_enable_emon():
            return self.emon.get_total_consumption()

    def get_energy_consumption(self):
        if (not self.has_virtual_resources()) and (self.power_state is HOST_ON):
            #self.logger.debug("Host on but empty. Return min energy")
            return self.get_min_energy()
        elif not self.power_state:
            #self.logger.info("Host off. Return {}".format(0))
            return 0.0
        else:
            p = (float(self.default_cpu) - float(self.cpu)) / float(self.default_cpu)
            vm_cons = self.get_total_vcpu_energy_usage()
            ret = vm_cons + (self.management_cons_dict['avg'] * p)

            if ret > self.get_max_energy():
                if ret > self.get_max_energy() + 1:
                    self.logger.warning("Energy breaking for {}->({}), vm_cons:{}, mngm_c:{}, p:{}={}-{}/def".format(
                                      self.get_id(), ret, vm_cons, self.management_cons_dict['avg'],
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

    def get_cpu_energy_usage(self):
        if self.cpu > self.default_cpu:
            usage = self.default_cpu
        else:
            usage = int(self.default_cpu - self.cpu)
            if usage == 0:  # state is off
                return 0
        self.logger.debug("USAGE in {}: {}".format(self.host_id, usage))
        return self.energy_table[usage]

    def get_total_vcpu_energy_usage(self):
        # due to overcommitting we can have more vcpus than previously discussed.
        # In this case, I'm assuming the power consumption isn't impacted and returning the max value
        usage = sum([vm.get_vcpu_usage() for vm in self.virtual_machine_list])
        if usage > next(reversed(self.energy_table)):
            usage = next(reversed(self.energy_table))
        return self.energy_table[usage]

    def __fetch_energy_info(self):
        host_energy = open(self.sla.g_energy_model_src(), 'r')
        host_table = OrderedDict()
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
        if not self.has_virtual_resources() and not self.power_state:
            self.logger.info("ENERGY: Wasted is 0.00 from %s" % (self.host_id))
            return 0.0  # servidor esta desligado

        if not self.has_virtual_resources() and self.power_state is True:
            self.logger.info("ENERGY: Wasted is minimum from %s" % (self.host_id))
            return self.get_min_energy()

        remaining_vcpu = self.get_total_cpu() - sum([vm.get_vcpu_usage() for vm in self.get_virtual_resources()])

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
