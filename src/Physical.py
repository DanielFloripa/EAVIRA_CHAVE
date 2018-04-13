#!/usr/bin/python
# -*- coding: utf-8 -*-

import traceback

SWITCH=1
MACHINE=2

class PhysicalMachine(object):
    def __init__(self, id, cpu, ram, algorithm, logger):
        self.logger = logger
        self.id = id
        self.cpu = cpu
        self.ram = ram
        self.algorithm = algorithm
        self.virtual_machine_list = []
        self.linked_to = []
        self.sla_violations_list = []
        self.acc = 0
        self.father = 0

        if self.algorithm == "CHAVE":
            self.state = "OFF"
            self.dbg = True
        else:
            self.state = "ON"
            self.dbg = False

        self.default_cpu = cpu
        self.default_ram = ram
        self.has_overbooking = False
        self.overb_max = float(2.0)
        self.overb_count = 0
        self.actual_overb = 0

        # With vms
        self.max_energy = 202.43
        self.min_energy = 118.11

        # Witout vms
        self.max_dom0 = 202.43
        self.min_dom0 = 118.11
        #self.dbg = False

    def __repr__(self):
        return repr((self.id, self.cpu, self.ram,"vl:", self.virtual_machine_list, self.algorithm,
                     self.sla_violations_list, self.has_overbooking, self.overb_count, self.actual_overb))

    def allocate(self, vnode):
        if self.can_allocate(vnode):
            if self.get_state() == "OFF":
                self.force_set_host_on()
            self.cpu -= vnode.get_vcpu()
            self.ram -= vnode.get_vram()
            vnode.set_physical_host(self.get_id())
            self.virtual_machine_list.append(vnode)
            return True

        self.sla_violations_list.append({vnode.get_id():"allocate"})
        return False

    def deallocate(self, vnode):
        try:
            self.virtual_machine_list.remove(vnode)
        except:
            self.sla_violations_list.append({vnode.get_id(): "deallocate"})
            self.logger.error("Error on remove resources for:\n"+str(vnode.get_id())+" on "+str(self.get_id()))
            self.logger.error(traceback.format_exc())
            return False

        if self.algorithm == "CHAVE":
            self.set_host_off()
        self.cpu += vnode.get_vcpu()
        self.ram += vnode.get_vram()
        if self.has_overbooking:
            self.logger.debug("Undo overb:"+self.get_id()+" cpu:"+str(self.cpu)+"...")
            if self.try_undo_overbooking(vnode):
                self.logger.debug("\t\tDONE! "+self.get_id()+" has no overb.")
            else:
                self.logger.debug("\t\tNot yet:"+str(self.default_cpu+self.get_cpu())+" still > "+str(self.default_cpu))
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
            self.logger.debug("WE can do overb on:"+str(self.id)+", cpu:"+str(overbCPU)+" ram:"+str(overbRAM))
            return True
        #else:
            #self.sla_violations_list.append([vm.get_id, vm.get_timestamp()])
            #if self.dbg: print "Denied super-overbooking:", overbCPU, "ID", self.get_id(), vm.get_id()
        return False

    def do_overbooking(self, vm):
        overb = (float(self.default_cpu) - float(self.cpu) + float(vm.get_vcpu())) / float(self.default_cpu)
        self.logger.debug("Do Overb on:"+str(self.get_id())+", for: "+vm.get_id()+" with tax:"+str(overb))
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
            self.state = "ON"
            self.logger.debug("NEW state:"+self.id+" turned "+self.state)
            return True
        elif self.has_virtual_resources() and self.state is "OFF":
            self.logger.error(" no logic, state OFF with resources???")
            self.state = "ON"
            return False
        self.logger.error("[force_set_host_on()], resources:"+str(self.has_virtual_resources())+" state:"+self.state)
        return False

    def set_host_off(self):
        if not self.has_virtual_resources() and self.state is "ON":
            self.state = "OFF"
            self.logger.debug("\t\tNEW STATE:"+self.id+" turned:"+self.state)
            return True
        if self.has_virtual_resources() and self.state is "ON":
            return False
        self.logger.debug("[set_host_off()], resources:"+str(self.has_virtual_resources())+" state:"+self.state)
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

    def get_config(self):
        return '%d %d %d %d' % (self.get_id(), self.get_cpu(), self.get_ram(),  self.get_type())

    def get_usage(self):
        used_cpu = sum([v.get_vcpu_usage() for v in self.virtual_machine_list])
        used_ram = sum([v.get_vram() for v in self.virtual_machine_list])

        return r'PM %d (%d VMs) - CPU: %.2lf%% | RAM: %.2lf%% ' % (
            self.id, len(self.virtual_machine_list), used_cpu / float(used_cpu + self.cpu) * 100, \
            used_ram / float(used_ram + self.ram) * 100)

    def set_debug_level(self, dbg_level):
        assert (dbg_level in [0,1,2]), "Debug Level must be" + str([0,1,2])
        self.dbg = dbg_level

    def get_used_cpu(self):
        return sum([vm.get_vcpu() for vm in self.virtual_machine_list])

    def get_used_ram(self):
        return sum([vm.get_vram() for vm in self.virtual_machine_list])

    def get_id(self):
        return self.id

    def get_type(self):
        return self.algorithm

    def get_state(self):
        return self.state

    def set_type(self, type):
        self.algorithm = type

    def get_virtual_resources(self):
        return self.virtual_machine_list

    def has_restricted_resources(self):
        for vnode in self.get_virtual_resources():
            if vnode.get_sla_time() == -1:
                return True
        return False

    def get_ram(self):
        return self.ram

    def get_cpu_usage(self):
        return sum([vnode.get_vcpu_usage() for vnode in self.get_virtual_resources()])

    def get_cpu(self):
        return self.cpu

    def get_total_ram(self):
        return self.get_ram() + self.get_used_ram()

    def get_total_cpu(self):
        return self.get_cpu() + self.get_used_cpu()

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

    def get_energy_consumption(self):
        #if len(self.get_virtual_resources()) == 0:
        #    return 0  # esta desligado
        if (not self.has_virtual_resources()) and (self.state is "ON"):
            self.logger.debug("PM Energy: Return min energy")
            return self.get_min_energy()
        elif self.state is "OFF":
            self.logger.debug("PM Energy: Return 0.0")
            return 0.0
        else:
            #m_vcpu = self.get_total_cpu() - sum([vnode.get_vcpu_usage() for vnode in self.get_virtual_resources()])
            #p = float(m_vcpu) / float(self.get_total_cpu())
            '''percentual de uso'''
            p = (float(self.default_cpu) - float(self.get_cpu())) / float(self.default_cpu)

            ret = sum([vnode.get_energy_consumption_virtual() for vnode in self.virtual_machine_list]) + (
            self.get_min_energy() * p) + (self.get_management_consumption() * p)

            if ret > self.get_max_energy():
                self.logger.info("Due to overbooking, energy is breaking our account! Returning just max! ("+str(ret)+")")
                return self.get_max_energy()
            return ret

    """
    Method: get the management consumption on a given moment,
            which we get using the formula:
                C_g(u) = C_t(u) - C_min(u) - sum(Cr(vm) for vm in the machine)
    """

    def get_management_consumption(self):
        C_t = sum([vnode.get_cpu_energy_usage() for vnode in self.get_virtual_resources()])
        C_min = self.get_min_energy()

        return C_t - C_min

    """
    Method: returns the fraction of energy that's being paid by the
            provider, i.e, what's left of C_g and C_min, which, in this
            model, are shared costs. The other costs are individual.
    """

    def get_wasted_energy(self):
        if not self.has_virtual_resources() and self.state is "OFF":
            #len(self.get_virtual_resources()) == 0 and self.state == "OFF":
            return 0.0 # servidor esta desligado
        if not self.has_virtual_resources() and self.state is "on":
            return self.get_min_energy()
        if self.actual_overb > 0:
            m_vcpu = 0
        else:
            m_vcpu = self.get_total_cpu() - sum([vnode.get_vcpu_usage() for vnode in self.get_virtual_resources()])
            #if self.dbg == 2: print "\n\n\t\t", m_vcpu, self.get_total_cpu(), "\n\n"
        p = float(m_vcpu) / float(self.get_total_cpu())
        myC_g = 0
        # management is only calaculated when there is at least one VM running, otherwise 0
        if self.has_virtual_resources(): #len(self.get_virtual_resources()) > 0:
            myC_g = self.get_management_consumption() * p
        myC_min = self.get_min_energy() * p

        ret = myC_g + myC_min

        if ret > self.get_max_energy():
            #if self.dbg == 2: print "Due to overbooking, wasted energy is breaking our account! Returning just max!"
            return self.get_max_energy()
        return ret


########################################
# Used inheritance otherwiser i'd need to
#	write the same methods again. Don't
#	know if it's right, my OOP sucks
########################################
#class PhysicalMachine(PhysicalResource):
#    def __init__(self, id, cpu, ram, type=None):
#        PhysicalResource.__init__(self, id, cpu, ram, type)
