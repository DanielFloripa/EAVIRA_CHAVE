#!/usr/bin/python
# -*- coding: utf-8 -*-

from random import randint
import time
import math
import pickle
from Architecture.Resources.Virtual import *
from Architecture.Infra import AvailabilityZone
from Users.SLAHelper import *


class Chave(object):

    @staticmethod
    def key_from_item(func):
        return lambda item: func(*item)

    def __init__(self, api):
        """
        CHAVE class
        :rtype: object
        """
        self.api = api
        self.sla = api.sla
        self.logger = api.sla.g_logger()
        self.nit = api.sla.g_nit()
        self.trigger_to_migrate = api.sla.g_trigger_to_migrate()
        self.frag_percent = api.sla.g_frag_class()
        self.window_time = api.sla.g_window_time()
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
                     self.frag_percent, self.window_time, self.all_vms_dict,
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
                az.take_snapshot_for(['energy_acum_l'], global_time=self.global_time)

            for lc_id, lc_obj in self.api.get_localcontroller_d().items():
                self.region_replication(lc_obj)

            self.global_time += self.window_time

            if self.global_time % 10000 == 0:
                elapsed = time.time() - start
                self.logger.critical("gt: {} , time:{} , it toke: {:.3f}s".format(
                    self.global_time, time.strftime("%H:%M:%S"), elapsed))
                start = time.time()

    #############################################
    ### Consolidation: Placement + Migration
    #############################################
    def initial_placement(self, az):
        az_id = az.az_id
        remaning_operations_for_this_az = dict(self.op_dict_temp_d[az_id])

        for op_id, vm in remaning_operations_for_this_az.items():
            if vm.timestamp <= self.global_time:
                this_state = op_id.split(K_SEP)[1]

                if self.can_consolidate(az):
                    self.do_consolidation(az)

                if this_state == "START":
                    ''' Let's PLACE!'''
                    b_host = self.best_host(vm, az)
                    if b_host is not None:
                        if self.place(vm, b_host, az):
                            new_host_on, _ = az.each_cycle_get_hosts_on()
                            # todo: criar função externa para isso:
                            if len(new_host_on) > self.sla.metrics.get(az.az_id, 'max_host_on_i'):
                                max_host_on = len(new_host_on)
                                self.sla.metrics.set(az.az_id, 'max_host_on_i', max_host_on)
                                self.logger.info("{}\t New max hosts on: {} at ts: {} s gt: {}".format(
                                    az_id, max_host_on, vm.timestamp, self.global_time))
                            self.vms_in_execution_d[az_id][vm.vm_id] = vm
                            self.req_size_d[az_id] += 1
                            del self.op_dict_temp_d[az_id][vm.vm_id + "_START"]
                            break
                        else:
                            self.logger.error("{}\t Problem on place vm: {}".format(az_id, vm.vm_id))
                    else:
                        # Após ocorrer a rejeição, remova a start e a stop do dicionário
                        del self.op_dict_temp_d[az_id][vm.vm_id + "_START"]
                        del self.op_dict_temp_d[az_id][vm.vm_id + "_STOP"]
                        temp_str = ''
                        if vm.pool_id in self.replicas_execution_d[az.lc_id].keys():
                            del self.replicas_execution_d[az.lc_id][vm.pool_id]
                            temp_str = '_r'

                        this_reject = self.sla.metrics.get(az.az_id, 'reject_i')
                        self.sla.metrics.add(az.az_id, 'reject_i', 1)
                        this_d = {'time': self.global_time,
                                  'vm_id': vm.vm_id,
                                  'reject': this_reject,
                                  'pool': vm.pool_id,
                                  'type': vm.type+temp_str}
                        az.take_snapshot_for(['reject_l'], metric_d=this_d)
                        self.logger.warning("{}\t Problem to find best host for {} t:{} h:{} az:{} at {}, d: {}".format(
                            az.az_id, vm.vm_id, vm.type, vm.host_id, vm.az_id, self.global_time, this_d.items()))
                        break

                elif this_state == "STOP":
                    exec_vm = None
                    try:
                        exec_vm = self.vms_in_execution_d[az_id].pop(vm.vm_id)
                    except IndexError:
                        self.logger.error("{}\t Problem INDEX on pop vm {}".format(az_id, vm.vm_id))
                    except KeyError:
                        self.logger.error("{}\t Problem KEY on pop vm {} {}".format(az_id, vm.vm_id, exec_vm))

                    if exec_vm is not None:
                        if az.deallocate_on_host(exec_vm, ts=vm.timestamp):
                            del self.op_dict_temp_d[az_id][op_id]
                        else:
                            self.logger.error("{}\t Problem for deallocate {}".format(az_id, exec_vm.vm_id))
                        if exec_vm.pool_id in self.replicas_execution_d[az.lc_id].keys():
                            del self.replicas_execution_d[az.lc_id][exec_vm.pool_id]
                            # azid_repl = pop_repl.az_id
                            # lc_id = self.api.get_lc_id_from_az_id(pop_repl.az_id)
                            # if self.api.localcontroller_d[lc_id].az_dict[azid_repl].deallocate_on_host(
                            #        pop_repl, ts=vm.timestamp):
                            #    az_replica = self.api.localcontroller_d[lc_id].az_dict[azid_repl]
                            #    self.measure_energy(az_replica, "remove" + K_SEP + REPLICA)
                        else:
                            """Pode não ser uma réplica, então não precisamos adicionar no log"""
                            pass
                    else:
                        self.logger.error("{}\t Problem for deallocate: VM is None. Original {}".format(az_id, vm))
                else:
                    self.logger.error("{}\t OOOps, DIVERGENCE between {} and {} ".format(az_id, this_state, op_id))
                    continue
            else:
                break
        # OUT!

    def can_consolidate(self, az):
        if self.sla.g_has_consolidation() is True:
            factor = self.sla.fragmentation_class_dict.get(self.sla.g_frag_class())
            overcom_max = 1
            if self.sla.g_has_overcommitting():
                overcom_max = float(self.sla.g_vcpu_per_core())
            if float(az.fragmentation()) >= float(factor * az.frag_min) * overcom_max:
                return True
        return False

    def do_consolidation(self, az):
        cons_alg = self.sla.g_consolidation_alg()
        self.logger.debug("{}\tStart consolidation: {}. {}".format(az.az_id, cons_alg, az.print_host_table()))
        if cons_alg == 'MAX':
            self.do_consolidation_max(az)
        elif cons_alg == 'LOCK':
            self.do_consolidation_locked(az)
        elif cons_alg == 'MIN':
            self.do_consolidation_min_mig(az)
        elif cons_alg == 'HA':
            self.do_consolidation_ha(az)
        else:
            self.logger.error("Problem on config file! opt: {}".format(cons_alg))
            exit(1)
        self.logger.debug("End: {} {}".format(az.az_id, az.print_host_table()))

    def do_consolidation_max(self, az):
        ret = True
        migrations = 0
        step = K_SEP + str(self.sla.metrics.get(az.az_id, 'consolidation_i'))
        self.sla.metrics.add(az.az_id, 'consolidation_i', 1)
        frag = az.fragmentation()
        # Todo: Equação xx
        objective = math.floor(frag * len(az.host_list))
        old_host_listd = dict(az.host_list_d)
        old_host_list = list()
        all_vms = az.get_vms_dict()
        _, hosts_on, _ = az.get_hosts_density(just_on=True)

        this_metric = OrderedDict({'step': 'before' + step,
                                   'is_done': "None",
                                   'vms_total': len(all_vms),
                                   'len_hosts': len(az.host_list),
                                   'hosts_on': hosts_on,
                                   'migrations_to': migrations,
                                   'fragmentation': float("{:.3f}".format(frag)),
                                   'objective': objective,
                                   'energy': None,
                                   'time': self.global_time})
        az.take_snapshot_for(['consolidation_l'], this_metric)
        self.logger.info("{}\n with {} hosts, let's turn {} host OFF, because AZ has {:.3f}% frag\nMetrics: {}".format(
            az.az_id, len(az.host_list), objective, frag, this_metric.items()))

        # Ordered from major to minor:
        ordered_vms = sorted(all_vms.items(), key=self.key_from_item(lambda k, v: (v.vcpu, k)), reverse=True)
        az.create_infra(first_time=True, host_state=HOST_OFF)
        # Objetivo é ter a consolidação máxima, então aplicamos FFD puro:
        for vm_id, vm in ordered_vms:
            old_host = vm.host_id
            vm.host_id = S_MIGRATING
            if not az.allocate_on_host(vm, consolidation=True):
                ret = False
            else:
                new_host = vm.host_id
                if new_host is not S_MIGRATING and new_host != old_host:
                    migrations += 1

        if ret is False:
            az.host_list = old_host_list
            az.host_list_d = old_host_listd
        _, hosts_on2, _ = az.get_hosts_density(just_on=True)
        frag2 = az.fragmentation()
        objective2 = math.floor(frag2 * len(az.host_list))

        this_metric2 = OrderedDict({'step': 'after' + step,
                                    'is_done': ret,
                                    'vms_total': len(all_vms),
                                    'len_hosts': len(az.host_list),
                                    'hosts_on': hosts_on2,
                                    'migrations_to': migrations,
                                    'fragmentation': float("{:.3f}".format(frag2)),
                                    'objective': objective2,
                                    'energy': None,
                                    'time': self.global_time})
        az.take_snapshot_for(['consolidation_l'], this_metric2)
        self.logger.info("{}\t Done! Before {} on, now {} on. lenVMS a:{}. Status:{}\nMetrics2: {}".format(
            az.az_id, hosts_on, hosts_on2, len(all_vms), ret, this_metric2.items()))
        return ret

    def do_consolidation_locked(self, az):
        step = K_SEP + str(self.sla.metrics.get(az.az_id, 'consolidation_i'))
        self.sla.metrics.add(az.az_id, 'consolidation_i', 1)
        frag = az.fragmentation()
        # Todo: Equação xx
        objective = math.floor(frag * len(az.host_list))
        hosts_on = 0
        vms_total = az.get_vms_dict()

        all_vms_od, hosts_locked, hosts_2_migrate_after = OrderedDict(), OrderedDict(), OrderedDict()
        temp_vms_d = dict()
        all_vms_updated = dict()
        destiny_hosts = dict()

        ordered_host_list = sorted(az.host_list, key=lambda h: len(h.virtual_machine_list))
        # Objetivo é ter a maxima consolidação considerando os passos:
        for h in ordered_host_list:
            mark_host_locked = False
            # Se o host estiver ligado!
            if h.power_state == HOST_ON:
                hosts_on += 1
                if h.has_available_resources():
                    self.logger.debug("Resources from {} remain_cpu:{} (ovc:{} <? max_ovc:{})".format(
                        h.host_id, h.cpu, h.actual_overcom, h.overcom_max))
                    # Primeiro verifique todas as vms deste host
                    for vm in h.virtual_machine_list:
                        # Ignore vms in locked state e de hosts cheios
                        if vm.is_locked is False:
                            temp_vms_d[vm.vm_id] = vm
                            self.logger.info("\tSelecting {} from {} to migrate (pool: {}) cpu{}>0 lkd?{} ovc{}<movc{}".format(
                                vm.vm_id, vm.host_id, vm.pool_id, h.cpu, vm.is_locked, h.actual_overcom, h.overcom_max))
                        else:
                            self.logger.debug("\tHost {} has locked VM ({}->{}), previous VMs will be removed!".format(
                                h.host_id, vm.vm_id, vm.is_locked))
                            mark_host_locked = True
                            break
                    # Ignore hosts w/ vms in locked state
                    if mark_host_locked:
                        hosts_locked[h.host_id] = h
                        temp_vms_d.clear()
                        pass
                    else:
                        all_vms_updated.update(temp_vms_d)
                        hosts_2_migrate_after[h.host_id] = h
                        # e se este host ainda pode receber algo
                    destiny_hosts[h.host_id] = h
                else:
                    self.logger.debug("Host {} is Full, don't considerate. ovc?:{} (actual_ovc:{} < max:{})".format(
                        h.host_id, h.has_overcommitting, h.actual_overcom, h.overcom_max))
                    pass
            else:
                self.logger.debug("Host {} is OFF".format(h.host_id))

        host_group_2_migrate = OrderedDict()
        host_group_2_migrate.update(hosts_locked)
        host_group_2_migrate.update(destiny_hosts)
        host_group_2_migrate.update(hosts_2_migrate_after)

        self.logger.info("\n\tlock:{}\n\tdest:{}\n\tafter:{}\n\tgroup:{}\n\tvms:{}".format(
            hosts_locked.keys(), destiny_hosts.keys(), hosts_2_migrate_after.keys(), host_group_2_migrate.keys(), all_vms_updated.keys()))
        # old_host_listd = dict(az.host_list_d)
        # old_host_list = list(az.host_list)
        this_metric = OrderedDict({'step': 'before' + step,
                                   'migrations': 0,
                                   'vms_total': len(vms_total),
                                   'vms_2_migrate': len(all_vms_updated), # 'asd': len(all_vms_od),
                                   'len_hosts': len(az.host_list),
                                   'hosts_on': hosts_on,
                                   'hosts_2_migrate': len(hosts_2_migrate_after),
                                   'fragmentation': float("{:.3f}".format(frag)),
                                   'objective': objective,
                                   'energy': None,
                                   'time': self.global_time})
        az.take_snapshot_for(['consolidation_l'], this_metric)
        self.logger.info("Consolidate {} with {} hosts, try turn {} host OFF, because AZ has. "
                         "h2m {} allvms {} VMs.\nMetric:{}".format(az.az_id, len(az.host_list), objective,
                          len(host_group_2_migrate), len(all_vms_updated), this_metric.items()))

        suc, fail = self.send_to_azmigrate(all_vms_updated, host_group_2_migrate, az, order_hosts=True)

        _, hosts_on2_i, _ = az.get_hosts_density(just_on=True)
        frag2 = az.fragmentation()
        objective2 = math.floor(frag2 * len(az.host_list))
        this_metric2 = OrderedDict({'step': 'after' + step,
                                    'migrations': suc,
                                    'vms_total': len(vms_total),
                                    'vms_2_migrate': len(all_vms_updated),
                                    'len_hosts': len(az.host_list),
                                    'hosts_on': hosts_on2_i,
                                    'hosts_2_migrate': len(host_group_2_migrate),
                                    'fragmentation': float("{:.3f}".format(frag2)),
                                    'objective': objective2,
                                    'energy': None,
                                    'time': self.global_time})
        az.take_snapshot_for(['consolidation_l'], this_metric2)
        self.logger.info("Before {} on, now {} on. Migrations:{}\n Metric:{}".format(
             hosts_on, hosts_on2_i, suc, this_metric2.items()))

    def do_consolidation_min_mig(self, az):
        all_vms_od, all_hosts_od = OrderedDict(), OrderedDict()
        frag = az.fragmentation()
        # Todo: Equação xx
        objective = math.floor(frag * len(az.host_list))
        self.logger.info("Consolidate {} with {} hosts, let's turn {} host OFF, because AZ has {:.3f}% frag".format(
            az.az_id, len(az.get_vms_dict()), objective, frag * 100))

        # Objetivo é ter a consolidação com o menor número de migrações considerando tres passos:
        for h in az.host_list:
            # 0) Se o host estiver ligado!
            if h.power_state:  # Todo: and not h.is_full:
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
            fixedHost2, hosts_to_migrate2, fixedVM2, vm_to_migrate2 = self.pin_biggers(vm_to_migrate, hosts_to_migrate,
                                                                                       az.azCores)
            # Atualize os dicionarios
            fixedHost.update(fixedHost2)
            hosts_to_migrate = hosts_to_migrate2
            fixedVM.update(fixedVM2)
            vm_to_migrate = vm_to_migrate2

        self.logger.debug(
            "{}\t\tAll Hosts Dict: {} \n\nAll VMs dict: {}".format(az.az_id, len(all_hosts_od), len(all_vms_od)))
        self.logger.info("\n\t\tFINAL:\nfixedHost: {}\nvm_to_migrate {}".format(fixedHost.keys(), vm_to_migrate.keys()))
        # self.logger.info("\n\t\tFINAL:\nfixedHost: {}\nvm_to_migrate {}".format(fixedHost, vm_to_migrate))
        # if self.migrate(vm_to_migrate, fixedHost, az, objective):
        #    return True
        return False

    def pin_quantity(self, all_vms, all_hosts):
        max_len = 0
        fixedHost = OrderedDict()  # FIXO
        fixedVM = OrderedDict()  # FIXO
        hosts_to_migrate = OrderedDict(all_hosts)
        vm_to_migrate = OrderedDict(all_vms)

        for k, v in all_hosts.items():
            self.logger.debug("Trying: {} {}".format(k, len(v)))
            if len(v) >= max_len:
                max_len = len(v)
                self.logger.debug("\tNew Max_len: {}".format(max_len))
                fixedHost[k] = v
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
                if len(hosts_to_migrate) <= float(len(all_hosts) * 0.5):
                    self.logger.debug("Saindo filtro fq {} <= {}".format(
                        len(hosts_to_migrate), float(len(all_hosts) * 0.5)))
                    break
            else:
                # Daqui pra frente nada mais nos interessa
                break
        return fixedHost, hosts_to_migrate, fixedVM, vm_to_migrate

    def pin_biggers(self, all_vms, all_hosts, azcpu):
        # 1) fixar vms com cpus mais de 1/2 da azcpu. Faca isso ate a metade dos hosts
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
                    self.logger.info(
                        "Saindo filtro fm {} <= {}".format(len(vm_to_migrate), float(len(all_hosts) * 1 / 2.0)))
                    break
        return fixedHost, hosts_to_migrate, fixedVM, vm_to_migrate

    def do_consolidation_ha(self, az):
        pass

    def send_to_azmigrate(self, vm_d, host_destiny, az, order_hosts=False):
        suc = 0
        fail = 0
        """Dicionario de VMs em ordem decrescente"""
        if order_hosts:
            host_destiny = OrderedDict(sorted(host_destiny.items(), key=self.key_from_item(lambda k, v: (v.cpu, k))))
        for i, v in sorted(vm_d.items(), key=self.key_from_item(lambda k, v: (v.vcpu, k)), reverse=True):
            origin = v.host_id
            for j, h in host_destiny.items():
                self.logger.info("{}\tTrying match h:{} v:{}({})".format(az.az_id, j, i, v.host_id))
                if az.migrate(v, h):
                    self.logger.info("{}\tSuccesful Migrated: {} from {} to {} (cpu-remain:{})".format(
                        az.az_id, v.vm_id, origin, h.host_id, h.cpu))
                    suc += 1
                    break
                else:
                    fail += 1
            if az.host_list_d.get(origin).power_state is HOST_OFF:
                self.logger.debug("Deleting {}, len:{} remain".format(origin, len(host_destiny.keys())))
                del host_destiny[origin]
                self.logger.info("Deleted {}, now {}".format(origin, host_destiny.keys()))
        return suc, fail

    #############################################
    # Used for both Consolidation and Replication
    #############################################
    def best_host(self, vm, az, recursive=False):
        for host in az.host_list:
            # 1st, select regular host
            if host.cpu >= vm.get_vcpu() and host.ram >= vm.get_vram():
                self.logger.info("{}\t Best host for {}-{} (vcpu:{}) is {} (cpu:{}). ovcCount:{}, tax:{} hasOvc? {}."
                                 "".format(az.az_id, vm.get_id(), vm.type, vm.get_vcpu(), host.get_id(), host.cpu,
                                           host.overcom_count, host.actual_overcom, host.has_overcommitting))
                return host
            # 2nd, try make overcommitting
            if host.can_overcommitting(vm):
                self.logger.info("{}\t Overcom for {} (vcpu:{}), is {} (cpu:{}). Overcom cnt:{}, actual:{}, has:{}.".
                                 format(az.az_id, vm.get_id(), vm.get_vcpu(), host.get_id(), host.cpu,
                                        host.overcom_count,
                                        host.actual_overcom, host.has_overcommitting))
                host.do_overcommitting(vm)
                return host
            # 3rd, If our trace is not real, we can create hosts on demand
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
        # if outsides loop, we can have a problem, but we can force a consolidation to find a best host
        if self.can_consolidate(az) and recursive == False:
            self.do_consolidation(az)
            if not recursive:
                self.best_host(vm, az, recursive=True)
        # or if VM is a replica, we can force choose other AZ
        elif vm.type is REPLICA and recursive == False:
            azlist = self.api.get_localcontroller_from_lcid(az.lc_id).az_list
            other_az = self.best_az_for_replica(vm, azlist, is_forced=True, az_forced=az)
            if other_az is not None:
                if not recursive:
                    self.best_host(vm, other_az, recursive=True)
                pass
            else:
                self.logger.warning("{}\t Not found best host in (d, on, off): {} for place {}. Trace: {}.\n {}\n{}".format(
                    az.az_id, az.get_hosts_density(), vm.get_id(), self.sla.g_trace_class(), vm, az))
        if recursive == True:
            self.logger.error("EXIT... We can't do nothing!!!")
            exit(1)
        return None

    def place(self, vm, bhost, az, vm_type=None):
        vm.lc_id = az.lc_id

        # if it'd the first time, put VM in replica_pool and continue:
        if self.is_required_replica(vm, az) and vm_type is None:
            self.replicate_vm(vm, az)
        vm.set_host_id(bhost.host_id)
        vm.az_id = az.az_id
        self.logger.debug("Allocating vmid:{} in h:{} t:{} az:{}".format(
            vm.vm_id, vm.host_id, vm.type, vm.az_id))
        if az.allocate_on_host(vm, defined_host=bhost):
            return True
        else:
            self.logger.error("{}\t Problem on allocate {} t:{} h:{} az:{}".format(
                az.az_id, vm.vm_id, vm.type, vm.host_id, vm.az_id))
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
                        if az is not None:
                            step = K_SEP + str(self.sla.metrics.get(az.az_id, 'replication_i'))
                            self.sla.metrics.add(az.az_id, 'replication_i', 1)
                            metric1 = {'step': 't0' + step,
                                       'pool_id': pool_id,
                                       'host_replica': 0,
                                       'replicas_execution': len(self.replicas_execution_d[lc_id]),
                                       'dict_remaining': len(self.replication_pool_d[lc_id]),
                                       'energy': None,
                                       'time': self.global_time}
                            az.take_snapshot_for(['replication_l'], metric1)

                            b_host = self.best_host(vm_r, az)
                            if b_host is not None:
                                if self.place(vm_r, b_host, az, vm_type=REPLICA):
                                    self.replicas_execution_d[lc_id][pool_id] = vm_r
                                    self.logger.info("{}\t Successful Allocated {} {} on {}".format(
                                        lc_id, REPLICA, vm_r.vm_id, vm_r.az_id))
                                    try:
                                        del self.replication_pool_d[lc_id][pool_id]
                                    except Exception as e:
                                        self.logger.error(type(e))
                                        self.logger.error("{}\t Delete REPLICA from pool {} on {}".format(
                                            lc_id, vm_r.vm_id, vm_r.az_id))

                                    metric2 = {'step': 't1' + step,
                                               'pool_id': pool_id,
                                               'host_replica': b_host.host_id,
                                               'len_replicas_exec': len(self.replicas_execution_d[lc_id]),
                                               'len_replication_remaining': len(self.replication_pool_d[lc_id]),
                                               'energy': None,
                                               'time': self.global_time}
                                    az.take_snapshot_for(['replication_l'], metric2)

                                else:
                                    self.logger.error("{}\t On place REPLICA {}".format(lc_id, pool_id))
                            else:
                                self.logger.error("{}\t NONE To find Best Host on {}".format(lc_id, pool_id))
                        else:
                            pass  # Best az for replica is None
                    else:
                        pass  # vm_replica not in this LC azs
                else:
                    pass  # self.logger.error("pool {} != {} lc_obj.lc_id".format(pool_id, lc_id))
        # self.logger.info("Exit for {} {}".format(self.global_time, lc_id))

    def best_az_for_replica(self, vm, az_list, is_forced=False, az_forced=None):
        """
        Choose the best az for instanciate a given replica
        :param vm:
        :param az_list:
        :param is_forced:
        :param az_forced:
        :return: object AvailabilityZone
        """
        temp_az_list = list(az_list)
        actual_az = None
        for az in az_list:
            if vm.az_id == az.get_id():
                actual_az = az
                # break
        try:
            temp_az_list.remove(actual_az)
        except ValueError:
            self.logger.error("{}\t ACTUAL_AZ: ({}) not in list {} ValueError".format(vm.az_id, actual_az.az_id, temp_az_list))
            return None
        except Exception as e:
            # self.logger.exception(type(e))
            self.logger.error("{}\t UNKNOWN: ({}) not in list {} {}".format(vm.az_id, actual_az, temp_az_list, e))
            # raise e
            return None

        if is_forced and az_forced is not None:
            try:
                temp_az_list.remove(az_forced)
            except ValueError:
                self.logger.error("{}\t AZ_FORCED: ({}) not in list {} ValueError".format(vm.az_id, actual_az.az_id, temp_az_list))
                return None
            except Exception as e:
                self.logger.error("{}\t UNKNOWN AZ_FORCED ({}) not in list {} {}".format(vm.az_id, actual_az, temp_az_list, e))
                return None
            else:
                if len(temp_az_list) == 1:
                    return temp_az_list[0]

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
                    self.logger.error("{}\t ({}) not in temp-list {} ERROR:{}".format(vm.az_id, az, temp_az_list, e))

        az_selection = self.sla.g_az_selection()
        this_target_lb = 1.0
        this_target_ha = 0.0
        best_az = None  # temp_az_list[0]
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
                if float(az.availability) > this_target_ha:
                    self.logger.debug("{}\tNew BestHost HA: av:{}%".format(az.az_id, az.availability*100))
                    this_target_ha = float(az.availability)
                    best_az = az
            elif az_selection == "LB":
                new_usage, _, _ = az.get_hosts_density()
                if new_usage < this_target_lb:
                    self.logger.debug("{}\tNew BestHost LB: usg:{}%".format(az.az_id, new_usage*100))
                    this_target_lb = new_usage
                    best_az = az
            elif az_selection == "RND" or is_forced:
                best_az = temp_az_list[randint(0, len(temp_az_list) - 1)]
                break  # '''Do this once one time'''
            else:
                self.logger.error("We must define the 'az selection' method, but have {}".format(self.sla.g_az_selection()))

        if best_az is None:
            best_az = temp_az_list[randint(0, len(temp_az_list) - 1)]
            self.logger.warning("AZ selection '{}' fails, we'll place {} (from {}) RND in {} list:{}".format(
                az_selection, vm.vm_id, vm.az_id, best_az, temp_az_list))
            return None

        self.logger.info("{} from ({}), {}  will be replicated for {}".format(
            vm.vm_id, actual_az.az_id, az_selection, best_az.az_id))
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
        lc_id = az.lc_id
        pool_id = vm.lc_id + K_SEP + vm.az_id + K_SEP + vm.vm_id
        if pool_id not in self.replication_pool_d[lc_id]:
            attr = vm.getattr()
            # print(attr)
            vm_replica = VirtualMachine(*attr)
            vm_replica.type = REPLICA
            vm.type = CRITICAL
            vm_replica.pool_id = pool_id
            vm.pool_id = pool_id
            self.replication_pool_d[lc_id][pool_id] = {CRITICAL: [az, vm], REPLICA: [["Undefined_AZ", vm_replica]]}
            self.logger.info("Pool {} created for replication:\n\t\tCritical:{}\n\t\tReplicas:{}\n".format(
                pool_id, self.replication_pool_d[lc_id][pool_id][CRITICAL],
                self.replication_pool_d[lc_id][pool_id][REPLICA]))
            return True
        self.logger.error("{}\t Pool {} already in replication_pool_d[{}]!".format(az.az_id, pool_id, lc_id))
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
