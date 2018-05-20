#!/usr/bin/python
# -*- coding: utf-8 -*-

from random import randint
import time
import math
from Architecture.Resources.Virtual import *
from Users.SLAHelper import *


class Chave(object):
    def __init__(self, api):
        self.api = api
        self.sla = api.sla
        self.logger = api.sla.g_logger()
        self.nit = api.sla.g_nit()
        self.trigger_to_migrate = api.sla.g_trigger_to_migrate()
        self.frag_percent = api.sla.g_frag_class()
        self.pm_mode = api.sla.g_pm()
        self.ff_mode = api.sla.g_ff()
        self.window_time = api.sla.g_window_time()
        self.window_size = api.sla.g_window_size()
        self.last_number_of_migrations = 0
        self.demand = None
        self.localcontroller_list = []
        self.region_list = None
        self.all_vms_dict = dict()
        self.all_op_dict = dict()
        self.all_ha_dict = dict()
        self.az_list = []
        self.global_hour = 0
        self.global_time = 0
        self.global_energy = 0
        self.exceptions = False
        self.has_operation_this_time = dict()
        self.replicas_execution_d = dict()
        """d['lc_id']['pool_id'] = obj"""
        self.replication_pool_d = dict()
        """d['lc_id']['lcid_azid_vmid'] = {'critical':[AZc, VMc], 'replicas':[[AZr1,VMr1],[...], [AZrn,VMrn]]}"""
        self.req_size_d = dict()
        self.energy_global_d = dict()
        self.max_host_on_d = dict()
        self.vms_in_execution_d = dict()
        self.op_dict_temp_d = dict()  # az.op_dict
        self.is_init_d = self.__init_dicts()

    def __repr__(self):
        return repr([self.logger, self.nit, self.trigger_to_migrate,
                     self.frag_percent, self.pm_mode, self.ff_mode,
                     self.window_size, self.window_time, self.all_vms_dict,
                     self.all_op_dict, self.all_ha_dict, self.sla])

    #############################################
    ### Initial and basics
    #############################################
    def __init_dicts(self):
        self.az_list = self.api.get_az_list()
        for az in self.az_list:
            self.req_size_d[az.az_id] = 0
            self.energy_global_d[az.az_id] = 0.0
            self.max_host_on_d[az.az_id] = 0
            self.vms_in_execution_d[az.az_id] = dict()
            self.op_dict_temp_d[az.az_id] = dict(az.op_dict)
            self.has_operation_this_time[az.az_id] = False

        for lc_id, lc_obj in self.api.get_localcontroller_d().items():
            self.localcontroller_list.append(lc_obj)
            self.replicas_execution_d[lc_id] = dict()
            self.replication_pool_d[lc_id] = dict()
        return True

    def run(self):
        """
        Interface for all algorithms, the name must be agnostic for all them
        In this version, we use Threads for running infrastructures in parallel
        :return: Void
        """
        start = time.time()
        while self.global_time <= self.api.demand.max_timestamp:
            for az in self.api.get_az_list():
                self.initial_placement(az)

            for lc_id, lc_obj in self.api.get_localcontroller_d().items():
                self.region_replication(lc_obj)
            self.global_time += self.window_time

            if self.global_time % 10000 == 0:
                elapsed = time.time() - start
                self.logger.critical("gt: {} , time:{} , it toke: {}s".format(
                    self.global_time, time.strftime("%H:%M:%S"), elapsed))
                start = time.time()

    #############################################
    ### Consolidation: Placement + Migration
    #############################################
    def initial_placement(self, az):
        az_id = az.az_id
        FORCE_PLACE = False
        remaning_operations_for_this_az = dict(self.op_dict_temp_d[az_id])

        for op_id, vm in remaning_operations_for_this_az.items():
            if vm.timestamp <= self.global_time:
                self.has_operation_this_time[az_id] = True
                this_state = op_id.split(K_SEP)[1]

                if self.can_consolidate(az):
                    self.do_consolidation(az)
                    self.sla.metrics(az.az_id, 'add', 'consolidations_i', 1)

                if this_state == "START":
                    # Let's PLACE
                    #if (self.is_time_to_place(self.global_time) or
                    #    self.window_size_is_full(self.req_size_d[az_id])) or \
                    #        FORCE_PLACE is True:
                    ## vm_list.sort(key=lambda e: e.get_vcpu(), reverse=True)  # decrescente
                    # host_ff_mode = az.get_host_list()
                    #  TODO: ver se é necessário: self.order_ff_mode(az.host_list)
                    b_host = self.best_host(vm, az)
                    if b_host is not None:
                        if self.place(vm, b_host, az):
                            new_host_on, off = az.each_cycle_get_hosts_on()
                            # todo: criar função externa para isso:
                            if new_host_on > self.sla.metrics(az.az_id, 'get', 'max_host_on_i', new_host_on):
                            #if new_host_on > self.max_host_on_d[az_id]:
                                max_host_on = new_host_on
                                self.sla.metrics(az.az_id, 'set', 'max_host_on_i', max_host_on)
                                self.logger.info("{}\t New max host on: {} at ts: {} s gt: {}".format(
                                    az_id, max_host_on, vm.timestamp, self.global_time))
                            self.vms_in_execution_d[az_id][vm.vm_id] = vm
                            self.req_size_d[az_id] += 1
                            del self.op_dict_temp_d[az_id][vm.vm_id + "_START"]
                            self.measure_energy(az, this_state+K_SEP+vm.vm_id)
                            # self.sla.metrics(az.get_id(), 'set', "req_size", req_size)
                            FORCE_PLACE = False
                        else:
                            self.logger.error("{}\t Problem on place vm: {}".format(az_id, vm.vm_id))
                    else:
                        self.logger.error("{}\t Problem to find best host for {} t:{} h:{} az:{}".format(
                            az.az_id, vm.vm_id, vm.type, vm.host_id, vm.az_id))

                elif this_state == "STOP":
                    exec_vm = None
                    try:
                        exec_vm = self.vms_in_execution_d[az_id].pop(vm.vm_id)
                    except IndexError:
                        self.logger.error("{}\t Problem INDEX on pop vm {}".format(az_id, vm.vm_id))
                    except KeyError:
                        self.logger.error("{}\t Problem KEY on pop vm {} {}".format(az_id, vm.vm_id, exec_vm))

                    if exec_vm is not None:
                        if az.deallocate_on_host(exec_vm, vm.timestamp):
                            self.measure_energy(az, "remove"+K_SEP+REGULAR)
                            del self.op_dict_temp_d[az_id][op_id]
                        else:
                            self.logger.error("{}\t Problem for deallocate {}".format(az_id, exec_vm.vm_id))

                        if exec_vm.pool_id in self.replicas_execution_d[az.lc_id].keys():
                            pop_repl = self.replicas_execution_d[az.lc_id].pop(exec_vm.pool_id)
                            azid_repl = pop_repl.az_id
                            lc_id = self.api.get_lc_id_from_az_id(pop_repl.az_id)
                            if self.api.localcontroller_d[lc_id].az_dict[azid_repl].deallocate_on_host(
                                    pop_repl, vm.timestamp):
                                self.measure_energy(
                                    self.api.localcontroller_d[lc_id].az_dict[azid_repl], "remove"+K_SEP+REPLICA)
                        else:
                            # self.logger.error("{}\t {} NOT FOUND IN: {}".format(az_id,
                            # self.replicas_execution_d, exec_vm.vm_id))
                            # Pode não ser uma réplica, então não precisamos adiciona no log
                            pass
                    else:
                        self.logger.error("{}\t Problem for deallocate: VM is None. Original {}".format(az_id, vm))
                else:
                    self.logger.error("{}\t OOOps, DIVERGENCE between {} and {} ".format(az_id, this_state, op_id))
                    FORCE_PLACE = True
                    continue
            else:
                """While there are not requisition, wait for the Thread_GVT"""
                self.measure_energy(az, "None")
                break
                # self.logger.debug("Waiting GVT at {}s".format(self.global_time))
        # self.logger.info("{}\t Exit for {}".format(az.az_id, self.global_time))

    def can_consolidate(self, az):
        if self.sla.g_has_consolidation() is True:
            factor = self.sla.fragmentation_classess_dict.get(self.sla.g_frag_class())
            if float(az.fragmentation()) >= float(factor * az.frag_min):
                return True
        return False

    def do_consolidation(self, az):
        all_vms_od, all_hosts_od = OrderedDict(), OrderedDict()
        frag = az.fragmentation()
        # Todo: Equação xx
        objective = math.floor(frag * len(az.host_list))
        self.logger.info("Consolidate {} with {} hosts, let's turn {} host OFF, because AZ has {}% frag".format(
            az.az_id, len(az.get_vms_dict()), objective, frag*100))

        # Objetivo é ter a consolidação com o menor número de migrações considerando tres passos:
        for h in az.host_list:
            # 0) Se o host estiver ligado!
            if h.is_on:  # Todo: and not h.is_full:
                # 1) Se o host estiver cheio, não migre
                if h.cpu > 0:  # Todo: mudar para overcommitting
                    all_hosts_od[h.host_id] = []
                    for vm in h.virtual_machine_list:
                        all_vms_od[vm.vm_id] = {'cpu': vm.vcpu, 'vm': vm, 'host': h.host_id, 'host_obj': h}
                        all_hosts_od[h.host_id].append({'cpu': vm.vcpu, 'vm': vm, 'host_obj': h})

        # 1) fixe hosts pela quantidade
        fixedHost, hosts_to_migrate, fixedVM, vm_to_migrate = self.pin_quantity(all_vms_od, all_hosts_od)
        # 2) Se não foi acançado o objetivo em (1), fixe os que tem as maiores VMs
        if len(hosts_to_migrate) > objective * 2:
            fixedHost2, hosts_to_migrate2, fixedVM2, vm_to_migrate2 = self.pin_biggers(vm_to_migrate, hosts_to_migrate, az.azCores)
            # Atualize os dicionarios
            fixedHost.update(fixedHost2)
            hosts_to_migrate = hosts_to_migrate2
            fixedVM.update(fixedVM2)
            vm_to_migrate = vm_to_migrate2

        self.logger.debug("{}\t\tAll Hosts Dict: {} \n\nAll VMs dict: {}".format(az.az_id, all_hosts_od, all_vms_od))
        # self.logger.info("\n\n\t\tFINAL:\n\nfixedHost: {}\n\n hosts_to_migrate: {}\n\n fixedVM: {}\n\n vm_to_migrate {}".format(fixedHost, hosts_to_migrate, fixedVM, vm_to_migrate))
        self.logger.info("\n\t\tFINAL:\nfixedHost: {}\nvm_to_migrate {}".format(fixedHost, vm_to_migrate))
        if self.migrate(vm_to_migrate, fixedHost, az, objective):
            return True
        return False

    def pin_quantity(self, all_vms, all_hosts):
        max_len = 0
        fixedHost = OrderedDict()  # FIXO
        fixedVM = OrderedDict()  # FIXO
        hosts_to_migrate = OrderedDict(all_hosts)
        vm_to_migrate = OrderedDict(all_vms)

        for k in sorted(all_hosts, key=lambda k: len(all_hosts[k]), reverse=True):
            self.logger.debug("Trying: {} {}".format(k, len(all_hosts[k])))
            if len(all_hosts[k]) >= max_len:
                max_len = len(all_hosts[k])
                self.logger.debug("\tNew Max_len: {}".format(max_len))
                fixedHost[k] = all_hosts[k]
                try:
                    pop_h = hosts_to_migrate.pop(k)
                    self.logger.debug("\t\tpop_h[{}]: {}".format(k, pop_h))
                except KeyError:
                    self.logger.error("KEY ERROR POP_H[{}].....{}".format(k, hosts_to_migrate))
                    pass
                else:
                    for vm in pop_h:
                        try:
                            pop_d = vm_to_migrate.pop(vm['vm'].vm_id)
                            self.logger.debug("\t\t\tpop_d[{}]: {}".format(vm['vm'].vm_id, pop_d))
                            fixedVM[vm['vm'].vm_id] = {'cpu': vm['cpu'], 'vm': vm['vm'], 'host': k}
                        except KeyError:
                            self.logger.error("KEY ERROR POP_D[{}]....{}".format(vm['vm'].vm_id, vm_to_migrate))
                            pass
                if len(hosts_to_migrate) <= float(len(all_hosts) * 1/2.0):
                    self.logger.debug("Saindo filtro fq {} <= {}".format(
                        len(hosts_to_migrate), float(len(all_hosts) * 1/2.0)))
                    break
            else:
                # Daqui pra frente nada mais nos interessa
                break
        return fixedHost, hosts_to_migrate, fixedVM, vm_to_migrate

    def pin_biggers(self, all_vms, all_hosts, azcpu):
        # 1) fixar vms com cpus mais de 1/2 azcpu. Faca isso ate a metade dos hosts
        vm_to_migrate = OrderedDict(all_vms)
        hosts_to_migrate = OrderedDict(all_hosts)
        fixedVM = OrderedDict()
        fixedHost = OrderedDict()

        for vm_id, vm_dict in all_vms.items():
            if vm_dict['cpu'] >= (azcpu * 1 / 2.0):  # pegar VMs com + da metade da CPU de um host
                try:
                    pop_h = hosts_to_migrate.pop(vm_dict['host'])
                    self.logger.info("pop_host[{}]: {}".format(vm_dict['host'], pop_h))
                    fixedHost[vm_dict['host']] = all_hosts[vm_dict['host']]
                except KeyError:
                    self.logger.error("KEY ERROR POP_H[{}]....{}".format(vm_id, vm_dict['host'], hosts_to_migrate))
                    pass
                else:
                    for vm in pop_h:
                        try:
                            pop_v = vm_to_migrate.pop(vm['vm'].vm_id)
                            self.logger.info("\t\tpop_vm[{}]: {}".format(vm['vm'].vm_id, pop_v))
                            fixedVM[vm['vm'].vm_id] = vm_dict
                        except KeyError:
                            self.logger.error("KEY ERROR POP_D.........", vm['vm'].vm_id, vm_to_migrate)
                            pass
                if len(vm_to_migrate) <= float(len(all_hosts) * 1 / 2.0):  # Apenas metade dos hosts fixos
                    self.logger.info("Saindo filtro fm {} <= {}".format(len(vm_to_migrate), float(len(all_hosts) * 1/2.0)))
                    break
        return fixedHost, hosts_to_migrate, fixedVM, vm_to_migrate

    def migrate(self, vm, host, az, max_objective):
        ''' Dicionario de VMs decrescente '''
        for i, k in enumerate(sorted(vm, key=lambda k: len(vm[k]), reverse=True)):

            '''Pega as demais VMs do host desta VM. Tipo 'evacuate' engatilhado pela VM atual'''
            origin_host = az.host_list_d[vm[k]['host']]
            origin_vmlist = origin_host.virtual_machine_list
            # Todo: escolher se crescente ou decrescente
            dest_host_id = sorted(host, key=lambda k: len(host[k]))[0]
            destiny_host = az.host_list_d[dest_host_id]
            '''Para cada VM do host atual:'''
            if origin_host.host_id != destiny_host.host_id:
                for vm_syster in origin_vmlist:
                    origin_host.deallocate(vm_syster)
                    destiny_host.allocate(vm_syster)
                    self.logger.info("Succesful Migrated: {} from {} (state:{}) to {} (cpur:{})".format(
                        vm_syster.vm_id, origin_host.host_id, origin_host.is_on, destiny_host.host_id, destiny_host.cpu))
        return True

    #############################################
    # Used for both Consolidation and Replication
    #############################################
    def best_host(self, vm, az, recursive=False):
        for host in az.host_list:
            # Firtly we'll try make overcommitting
            if host.can_overcommitting(vm):
                self.logger.info("{}\t Overcom for {} (vcpu:{}), is {} (cpu:{}). Overcom cnt:{}, actual:{}, has:{}.".
                                 format(az.az_id, vm.get_id(), vm.get_vcpu(), host.get_id(), host.cpu, host.overcom_count,
                                        host.actual_overcom, host.has_overcommitting))
                host.do_overcommitting(vm)
                return host
            # Secondly we'll select other host
            if host.cpu >= vm.get_vcpu() and host.ram >= vm.get_vram():
                self.logger.info("{}\t Best host for {}-{} (vcpu:{}) is {} (cpu:{}). ovcCount:{}, tax:{} hasOvc? {}."
                                 "".format(az.az_id, vm.get_id(), vm.type, vm.get_vcpu(), host.get_id(), host.cpu,
                                           host.overcom_count, host.actual_overcom, host.has_overcommitting))
                return host
            if self.sla.g_trace_class() != "REAL":
                self.logger.warning("{}\t Not found existing best host in len:{} for place {}. Trying a new host."
                                    " \n {}\n{}".format(az.az_id, len(az.host_list), vm.get_id(), vm, az))
                if self.api.create_new_host(az.az_id, host_state=HOST_ON):
                    for new_host in az.host_list:
                        if new_host.cpu >= vm.get_vcpu() and new_host.ram >= vm.get_vram():
                            self.logger.info("After new host, for {} (vcpu:{}) is {} (cpu:{}). ovcCount:{}, "
                                             "tax:{} hasOvc? {}.".format(vm.get_id(), vm.get_vcpu(), host.get_id(),
                                                                         host.cpu, host.overcom_count, host.actual_overcom,
                                                                         host.has_overcommitting))
                            return host
        # if outsides loop, we have a problem: we can force a consolidation
        if self.can_consolidate(az):
            self.do_consolidation(az)
            self.sla.metrics(az.az_id, 'add', 'sla_violations_i', 1)
            if not recursive:
                self.best_host(vm, az, recursive=True)
        # or if VM is a replica, we can force choose other AZ
        else:
            azlist = self.api.get_localcontroller_from_lcid(az.lc_id).az_list
            last_az = self.best_az_for_replica(vm, azlist, is_forced=True, az_forced=az)
            if last_az is not False:
                # Todo:
                pass
            else:
                self.logger.warning("{}\t Not found best host in {} options for place {}. Trace: {}.\n {}\n{}".format(
                    az.az_id, len(az.host_list), vm.get_id(), self.sla.g_trace_class(), vm, az))
        if recursive:
            self.logger.error("EXIT...")
            exit(1)
        return None

    def place(self, vm, bhost, az, vm_type=None):
        vm.lc_id = az.lc_id

        if self.is_required_replica(vm, az) and vm_type is None:
            self.replicate_vm(vm, az)
        vm.set_host_id(bhost.host_id)
        vm.az_id = az.az_id
        self.logger.debug("Allocating vmid:{} in h:{} t:{} az:{}".format(
            vm.vm_id, vm.host_id, vm.type, vm.az_id))
        if bhost.allocate(vm):
            return True
        else:
            self.logger.error("{}\t Problem on allocate {} t:{} h:{} az:{}".format(
                az.az_id, vm.vm_id, vm.type, vm.host_id, vm.az_id))
        return False

    def measure_energy(self, az, vm_type):
        az_id = az.az_id
        energy = az.get_az_energy_consumption2(append_metrics=False)
        ret1 = self.sla.metrics(az_id, 'set', 'energy_l', energy)
        ret2 = self.sla.metrics(az_id, 'add', 'total_energy_f', energy)
        acum = self.sla.metrics(az_id, 'get', 'total_energy_f')
        ret3 = self.sla.metrics(az_id, 'set', 'energy_acum_l', acum)

        if ret1 and ret2 and ret3:
            self.logger.debug("{}\t Energy at {}t from {} is {}/{} Wh".format(
                az_id, self.global_time, vm_type, energy, acum))
            return True
        self.logger.error("{}\t Metrics problem: tp:{} r1:{} r2:{} r3:{} en:{} gh:{} gt:{}".format(
            az_id, vm_type, ret1, ret2, ret3, energy, self.global_hour, self.global_time))
        return False

    #############################################
    ### Replication
    #############################################
    def region_replication(self, lc_obj):
        lc_id = lc_obj.lc_id
        this_lc_azs = [az.get_id() for az in lc_obj.az_list]

        if len(self.replication_pool_d[lc_id].items()) > 0:
            replicas_for_this_lc = dict(self.replication_pool_d[lc_id])

            for pool_id, pool_d in replicas_for_this_lc.items():
                lc_pool = pool_id.split(K_SEP)[0]
                if lc_pool == lc_obj.lc_id:
                    vm_r = pool_d[REPLICA][0][1]
                    if vm_r.az_id in this_lc_azs:  # Apenas pra confirmar
                        az = self.best_az_for_replica(vm_r, lc_obj.az_list)
                        b_host = self.best_host(vm_r, az)
                        if b_host is not None:
                            if self.place(vm_r, b_host, az, vm_type=REPLICA):
                                self.replicas_execution_d[lc_id][pool_id] = vm_r
                                self.logger.info("{}\t Allocated {} {} on {}".format(
                                    lc_id, REPLICA, vm_r.vm_id, vm_r.az_id))
                                try:
                                    del self.replication_pool_d[lc_id][pool_id]
                                except:  # Exception as e:
                                    # self.logger.error(type(e))
                                    self.logger.error("{}\t Delete REPLICA from pool {} on {}".format(
                                        lc_id, vm_r.vm_id, vm_r.az_id))
                            else:
                                self.logger.error("{}\t On place REPLICA {}".format(lc_id, pool_id))
                        else:
                            self.logger.error("{}\t To find Best Host {}".format(lc_id, pool_id))
                    else:
                        pass
                        # self.logger.error("{}\t pool:{2} az_id {} not in {}".format(
                        # lc_id, pool_id, vm_r.az_id, this_lc_azs))
                else:
                    pass
                    # self.logger.error("pool {} != {} lc_obj.lc_id".format(pool_id, lc_id))
        # self.logger.info("Exit for {} {}".format(self.global_time, lc_id))

    def best_az_for_replica(self, vm, az_list, is_forced=False, az_forced=None):
        temp_az_list = list(az_list)
        atual_az = None
        for az in az_list:
            if vm.az_id == az.get_id():
                atual_az = az
                # break
        try:
            temp_az_list.remove(atual_az)
            if is_forced and az_forced is not None:
                temp_az_list.remove(az_forced)
        except ValueError:
            self.logger.error("{}\t ({}) not in list {}".format(vm.az_id, atual_az, temp_az_list))
            return False
        except Exception as e:
            # self.logger.exception(type(e))
            self.logger.error("{}\t UNKNOWN({}) not in list {} {}".format(vm.az_id, atual_az, temp_az_list, e))
            # raise e
            return False
        # get the max and min azCores:
        min_cpu = [0, None]
        max_cpu = [1024, None]
        other_temp_az_list = list(temp_az_list)
        for az in other_temp_az_list:
            if az.azCores > min_cpu[0]:
                min_cpu[0] = az.azCores
                min_cpu[1] = az
            if az.azCores < max_cpu[0]:
                max_cpu[0] = az.azCores
                max_cpu[1] = az
            # Remove incompatible azs
            if az.azCores < vm.vcpu:
                try:
                    temp_az_list.remove(az)
                except Exception as e:
                    self.logger.error("{}\t ({}) not in list {} {}".format(vm.az_id, az, temp_az_list, e))

        az_selection = self.sla.g_az_selection()
        az_target = 0.0
        best_az = None
        for az in temp_az_list:
            # Todo: ver wf e bf
            if az_selection == "WF":  # aquela que deixa o maior espaço livre
                if vm.vcpu < max_cpu[0]:
                    best_az = max_cpu[1]
                    # best_az.has_overcommitting = True
            elif az_selection == "BF":
                if vm.vcpu >= min_cpu[0]:
                    best_az = max_cpu[1]
                    # best_az.has_overcommitting = True
            elif az_selection == "HA":
                if float(az.availability) > az_target:
                    az_target = float(az.availability)
                    best_az = az
            elif az_selection == "LB":
                usage = az.get_hosts_density()
                if az_target <= usage:
                    az_target = usage
                    best_az = az
            elif az_selection == "RND" or is_forced:
                best_az = temp_az_list[randint(0, len(temp_az_list)-1)]
                break
        if best_az is None:
            best_az = temp_az_list[randint(0, len(temp_az_list) - 1)]
            self.logger.warning("AZ selection '{}' fails, we'll place {} (from {}) RND in {} list:{}".format(
                az_selection, vm.vm_id, vm.az_id, best_az, temp_az_list))
            return False

        self.logger.info("{} from ({}), {}  will be replicated for {}".format(
            vm.vm_id, atual_az.az_id, az_selection, best_az.az_id))
        return best_az

    def is_required_replica(self, vm, az):
        if type(vm.type) is str and type(vm.availab) is float and type(az.availability) is float:
            if vm.availab > az.availability and vm.type != REPLICA:
                self.logger.debug("{}-{} require replication! {}=?{}".format(vm.vm_id, vm.type, vm.az_id, az.az_id))
                return True
            return False
        else:
            self.logger.error("{}\t Types: vm:{}, ha:{}, av:{}".format(
                az.az_id, type(vm.type), type(vm.availab), type(az.availability)))
        return False

    def replicate_vm(self, vm, az):
        pool_id = vm.lc_id + K_SEP + vm.az_id + K_SEP + vm.vm_id
        if pool_id not in self.replication_pool_d[az.lc_id]:
            attr = vm.getattr()
            vm_replica = VirtualMachine(*attr)
            vm_replica.type = REPLICA
            vm.type = CRITICAL
            vm_replica.pool_id = pool_id
            vm.pool_id = pool_id
            self.replication_pool_d[az.lc_id][pool_id] = {CRITICAL: [az, vm], REPLICA: [["", vm_replica]]}
            self.logger.info("Pool {} created for replication. {}".format(
                            pool_id, self.replication_pool_d[az.lc_id].items()))
            return True
        self.logger.error("{}\t Pool {} already in replication_pool_d[{}]!".format(az.az_id, pool_id, az.lc_id))
        return False

    #############################################
    ### Miscelaneous
    #############################################
    def get_last_number_of_migrations(self):
        ret = self.last_number_of_migrations
        self.last_number_of_migrations = 0
        return ret

    def is_time_to_migrate(self, this_time):
        if this_time % self.trigger_to_migrate == 0:
            return True
        return False

    def is_time_to_place(self, cycle):
        if cycle % self.window_time == 0:
            return True
        return False

    def window_size_is_full(self, req_size):
        if req_size >= self.window_size:
            return True
        return False


    '''def set_demand(self, demand):
        self.demand = demand
        self.all_vms_dict = demand.all_vms_dict
        self.all_op_dict = demand.all_op_dict()
        self.all_ha_dict = demand.all_ha_dict()

    def set_localcontroller(self, localcontroller):
        self.localcontroller_list = localcontroller
        for lc in localcontroller:
            self.logger.info(lc.lc_id, lc.az_list)

    def _opdict_to_vmlist(self, id, this_vm_list):
        for vm_temp in this_vm_list:
            if vm_temp.get_id() == id:
                return vm_temp
        return None

    def order_ff_mode(self, host_list):
        if self.ff_mode == "FFD2I":  # crescente
            host_list.sort(key=lambda e: e.cpu)
        elif self.ff_mode == "FF3D":  # decrescente
            host_list.sort(key=lambda e: e.cpu, reverse=True)
        return host_list  # se nenhuma configuração
    
    def energy(self):
        this_energy_wh = 0
        if self.global_hour >= 0:
            for az in self.api.get_az_list():
                this_energy_wh += az.get_az_watt_hour()
            self.global_energy += this_energy_wh
            # self.sla.metrics('global', 'set', 'energy_mon_hour', this_energy_wh)
            # self.sla.metrics('global', 'set', 'energy_mon_total', self.global_energy)
            return this_energy_wh
        return False    
        
    '''
