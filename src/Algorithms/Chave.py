#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
from random import randint
from typing import Union, Tuple
from collections import OrderedDict

from Algorithms import BaseAlgorithm
from Architecture.Infra import AvailabilityZone
from Architecture.Resources.Physical import *
from Architecture.Resources.Virtual import *
from Users.SLAHelper import *


class Chave(BaseAlgorithm):
    def __init__(self, api):
        BaseAlgorithm.__init__(self, api)
        self.api = api
        self.sla = api.sla
        self.logger = api.sla.g_logger()
        self.nit = api.sla.g_nit()
        self.az_list = list(api.get_az_list())
        self.trigger_to_migrate = api.sla.g_trigger_to_migrate()
        self.frag_percent = api.sla.g_frag_class()
        self.window_time = api.sla.g_window_time()
        # Todo: create other opportunities for replication:
        # 0 Reject
        # 1 Accept replicas in same AZ -> calculate final availability
        # 2 Accept replicas in other local_controler
        self.replication_scale = 0  # Todo: get from SLA parameters
        self.last_ts_d = api.demand.last_timestamps_d_ordered()
        self.last_number_of_migrations = 0
        self.localcontroller_list = []
        self.all_vms_dict = dict()
        self.all_op_dict = dict()
        self.all_ha_dict = dict()
        self.global_time = 0
        self.max_host_on = dict()
        self.replicas_execution_d = dict()
        """d['lc_id']['pool_id'] = obj"""
        self.replication_pool_d = dict()
        """d['lc_id']['lcid_azid_vmid'] = {'critical':[AZc, VMc], 'replicas':[[AZr1,VMr1],[...], [AZrn,VMrn]]}"""
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
        for az in self.az_list:
            az_id = az.az_id
            self.max_host_on[az_id] = 0
            self.vms_in_execution_d[az_id] = dict()
            self.op_dict_temp_d[az_id] = dict(az.op_dict)
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
        milestones = int(self.api.demand.max_timestamp / self.sla.g_milestones())
        start = time.time()
        while self.global_time <= self.api.demand.max_timestamp:
            for az in self.az_list:
                self.initial_placement(az)

                values = (self.global_time, az.get_az_energy_consumption2(), "",)
                self.sla.metrics.set(az.az_id, 'energy_l', values)

                azl2 = az.get_az_load()
                values = (self.global_time, azl2, str(),)
                self.sla.metrics.set(az.az_id, 'az_load_l', values)

            for _, local_controller_o in self.api.get_localcontroller_d().items():
                self.region_replication(local_controller_o)

            if self.global_time % milestones == 0:
                memory = self.sla.check_simulator_memory()
                elapsed = time.time() - start
                self.logger.critical("gt: {} , time:{} , it toke: {:.3f}s, {}".format(
                    self.global_time, time.strftime("%H:%M:%S"), elapsed, memory))
                self.sla.metrics.set('global', 'lap_time_l', (self.global_time, elapsed, "Status:{}".format(memory)))
                start = time.time()
            self.remove_finished_azs()
            # Doc: At the end, increment the clock with the window_time:
            self.global_time += self.window_time

    #############################################
    ### Consolidation: Placement + Migration
    #############################################
    def initial_placement(self, az):
        az_id = az.az_id
        remaning_operations_for_this_az = dict(self.op_dict_temp_d[az_id])
        is_deallocated = False
        for op_id, vm in remaning_operations_for_this_az.items():
            if vm.timestamp <= self.global_time:
                this_state = op_id.split(K_SEP)[1]

                if this_state == "START":
                    # Note: Let's PLACE!
                    b_host, info_bh = self.best_host(vm, az)
                    if b_host is not None:
                        if self.place(vm, b_host, az):
                            self.have_new_max_host_on(az)
                            self.vms_in_execution_d[az_id][vm.vm_id] = vm
                            self.sla.metrics.update(az_id, "avm_history", "host_place", b_host.host_id, "vm_id", vm.vm_id)
                            # Todo: Change this to accept overcom
                            # tax = 0  # b_host.check_overcom()
                            # if tax > 1:  # or vm.in_overcomm_host:
                            #    vm_id_future = vm.vm_id + K_SEP + "STOP"
                            #    vm_ovc = self.op_dict_temp_d[az_id][vm_id_future]
                            #    old_ts = vm_ovc.timestamp
                            #    vm_ovc.timestamp = int(old_ts * tax)
                            #    self.logger.info("{}\tChanging ts:{} from {} to {}".format(
                            #        az_id, old_ts, vm_id_future, vm_ovc.timestamp))
                            del self.op_dict_temp_d[az_id][vm.vm_id + "_START"]
                            break
                        else:
                            self.logger.error("{}\t Problem on place vm: {}".format(az_id, vm.vm_id))
                    else:
                        info = "{}, info_bh:{}".format(vm.type, len(info_bh))
                        self.set_rejection_for("placement", 0, info, az.lc_id, vm.pool_id, az_id, vm.vm_id)
                        break

                elif this_state == "STOP":
                    is_deallocated = True
                    exec_vm = None
                    try:
                        exec_vm = self.vms_in_execution_d[az_id].pop(vm.vm_id)
                    except IndexError:
                        self.logger.error("{}\t Problem INDEX on pop vm {}".format(az_id, vm.vm_id))
                    except KeyError:
                        self.logger.error("{}\t Problem KEY on pop vm {} {}".format(az_id, vm.vm_id, exec_vm))
                    except Exception as e:
                        self.logger.exception(e)
                    if exec_vm is not None:
                        if az.deallocate_on_host(exec_vm, ts=vm.timestamp, set_state=HOST_OFF):
                            del self.op_dict_temp_d[az_id][op_id]
                        else:
                            self.logger.error("{}\t Problem for deallocate {}".format(az_id, exec_vm.vm_id))
                        if exec_vm.pool_id in self.replicas_execution_d[az.lc_id].keys():
                            del self.replicas_execution_d[az.lc_id][exec_vm.pool_id]
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
        # Note: We are consolidating after the deallocation,
        # Decision making: because at this momment the AZ can have fragmentation
        if is_deallocated:
            if self.can_consolidate(az):
                self.do_consolidation(az)
        # OUT!

    def have_new_max_host_on(self, az):
        host_on, _, _ = az.each_cycle_get_hosts_on()
        if host_on > self.max_host_on[az.az_id]:
            self.max_host_on[az.az_id] = host_on
            self.sla.metrics.set(az.az_id, 'max_host_on_i', (self.global_time, host_on, az.az_id))
            self.logger.info("{}\t New max host on: {} at gt: {}".format(
                az.az_id, self.max_host_on[az.az_id], self.global_time))

    def can_consolidate(self, az: AvailabilityZone) -> bool:
        """
        Check if can consolidate
        :type az: AvailabilityZone
        :param az:
        :return: bool
        """
        if self.sla.g_can_do_consolidation() is True:
            factor = self.sla.fragmentation_class_dict.get(self.sla.g_frag_class())
            overcom_max = 1
            if self.sla.g_can_do_overcommitting():
                overcom_max = float(self.sla.g_vcpu_per_core())
            if float(az.fragmentation()) >= float(factor * az.frag_min) * overcom_max:
                return True
        return False

    def do_consolidation(self, az, who_call=""):
        cons_alg = self.sla.g_consolidation_alg()
        self.logger.info(
            "{}\tStart consolidation: {}. {}".format(az.az_id, cons_alg, az.print_hosts_distribution(level='Middle')))
        if cons_alg == 'MAX':
            self.do_consolidation_max(az)
        elif cons_alg == 'LOCK':
            self.do_consolidation_locked(az)
        elif cons_alg == 'MIN':
            self.do_consolidation_min_mig(az)
        elif cons_alg == 'HA':
            self.do_consolidation_ha(az)
        else:
            self.logger.error("Problem on config file! Unknown option: {}".format(cons_alg))
            exit(1)
        self.logger.info("End: {} {}".format(az.az_id, az.print_hosts_distribution(level='Middle')))

    def do_consolidation_max(self, az):
        ret = True
        migrations = 0
        frag = az.fragmentation()
        # Todo: Equação xx
        objective = math.floor(frag * len(az.host_list))
        old_host_listd = dict(az.host_list_d)
        old_host_list = list()
        all_vms = az.get_vms_dict()
        # SNAP
        _, hosts_on, _ = az.get_hosts_density(just_on=True)
        energy = az.get_az_energy_consumption2()
        conf_0 = az.print_hosts_distribution()
        self.logger.info("{}\n with {} hosts, let's turn {} host OFF, because AZ has {:.3f}% frag".format(
            az.az_id, len(az.host_list), objective, frag))

        # Doc: Ordered from major to minor:
        ordered_vms = sorted(all_vms.items(), key=self.sla.key_from_item(lambda k, v: (v.vcpu, k)), reverse=True)
        az.create_infra(first_time=True, host_state=HOST_OFF)

        # Doc: Objetivo é ter a consolidação máxima, então aplicamos FFD puro:
        for vm_id, vm in ordered_vms:
            old_host = vm.host_id
            vm.host_id = S_MIGRATING
            if not az.allocate_on_host(vm, consolidation=True):
                ret = False
            else:
                new_host = vm.host_id
                if new_host is not S_MIGRATING and new_host != old_host:
                    migrations += 1
        # Doc: Undo all if something wrong:
        if ret is False:
            az.host_list = old_host_list
            az.host_list_d = old_host_listd
        _, hosts_on2, _ = az.get_hosts_density(just_on=True)
        energy2 = az.get_az_energy_consumption2()
        conf_f = az.print_hosts_distribution()
        info = "obj:{}. {} __ {}".format(objective, conf_0, conf_f)
        val_0 = hosts_on - hosts_on2
        this_metric = {'gvt': self.global_time,
                       'energy_0': energy,
                       'energy_f': energy2,
                       'val_0': val_0,
                       'val_f': migrations,
                       'hosts_0': hosts_on,
                       'hosts_f': hosts_on2,
                       'info': info}
        self.sla.metrics.set(az.az_id, 'consol_d', tuple(this_metric.values()))
        self.logger.info("{}\t Done! Before {} on, now {} on. lenVMS a:{}. Status:{}\nMetrics2: {}".format(
            az.az_id, hosts_on, hosts_on2, len(all_vms), ret, this_metric.items()))
        return ret

    def do_consolidation_locked(self, az):
        hosts_on = 0
        all_vms_od, hosts_locked, hosts_2_migrate_after = OrderedDict(), OrderedDict(), OrderedDict()
        all_vms_updated = dict()
        destiny_hosts = dict()

        # Todo: Equação xx
        frag = az.fragmentation()
        objective = math.floor(frag * len(az.host_list))
        vms_to_order_d = dict()
        ordered_host_list = sorted(az.host_list, key=lambda hh: len(hh.virtual_machine_list))
        # Objetivo é ter a consolidação considerando os passos:
        for h in ordered_host_list:
            this_host_is_locked = False
            # Se o host estiver ligado!
            if h.power_state == HOST_ON:
                hosts_on += 1
                if h.has_available_resources():
                    self.logger.debug("Resources from {} remain_cpu:{} (ovc:{} <? max_ovc:{})".format(
                        h.host_id, h.cpu, h.actual_overcom, h.overcom_max))
                    # Verifique todas as vms deste host
                    vms_to_order_d[h.host_id] = []
                    for vm in h.virtual_machine_list:
                        # Ignore vms in locked state and from full hosts
                        if vm.is_locked is False:
                            vms_to_order_d[h.host_id].append(vm)
                            self.logger.info(
                                "\tSelecting {} from {} to migrate (pool: {}) cpu{}>0 lkd?{} ovc{}<movc{}".format(
                                    vm.vm_id, vm.host_id, vm.pool_id, h.cpu, vm.is_locked, h.actual_overcom, h.overcom_max))
                        else:
                            self.logger.debug("\tHost {} has locked VM ({}->{}), previous VMs will be removed!".format(
                                h.host_id, vm.vm_id, vm.is_locked))
                            this_host_is_locked = True
                            break
                    # Doc: Ignore hosts with vms in locked state
                    if this_host_is_locked:
                        hosts_locked[h.host_id] = h
                        del vms_to_order_d[h.host_id]
                        pass
                    else:
                        hosts_2_migrate_after[h.host_id] = h
                    # if host can receive something:
                    destiny_hosts[h.host_id] = h
                else:
                    self.logger.debug("Host {} is Full, don't considerate. ovc?:{} (actual_ovc:{} < max:{})".format(
                        h.host_id, h.has_overcommitting, h.actual_overcom, h.overcom_max))
                    pass
            else:
                self.logger.debug("Host {} is OFF".format(h.host_id))

        # This approach will minimize the number of migrations
        for host in sorted(vms_to_order_d.values(), key=lambda v: len(v)):
            for vm in host:
                all_vms_updated[vm.vm_id] = vm

        host_group_2_migrate = OrderedDict()  # Dict ordered by 3 criteria:
        host_group_2_migrate.update(hosts_locked)  # 1st) The hosts wich can't migrate
        host_group_2_migrate.update(destiny_hosts)  # 2nd) Any host without restrictions
        host_group_2_migrate.update(hosts_2_migrate_after)  # 3rd) Finnaly, the best hosts to turn off

        self.logger.info("\n\tlock:{}\n\tdest:{}\n\tafter:{}\n\tgroup:{}\n\tvms:{}".format(
            hosts_locked.keys(), destiny_hosts.keys(), hosts_2_migrate_after.keys(), host_group_2_migrate.keys(),
            all_vms_updated.keys()))
        energy0 = az.get_az_energy_consumption2()
        conf_0 = az.print_hosts_distribution()

        self.logger.info("Consolidate {} with {} hosts, try turn {} host OFF, because AZ has. h2m {} allvms {} VMs".format(
            az.az_id, len(az.host_list), objective, len(host_group_2_migrate), len(all_vms_updated)))

        migrations, fail = self.send_to_azmigrate(all_vms_updated, host_group_2_migrate, az, order_hosts=True)

        _, hosts_on2, _ = az.get_hosts_density(just_on=True)
        conf_f = az.print_hosts_distribution()
        info = "obj:{} __ {} {}".format(objective, conf_0, conf_f)
        val_0 = hosts_on - hosts_on2
        this_metric = {'gvt': self.global_time,
                       'energy_0': energy0,
                       'energy_f': az.get_az_energy_consumption2(),
                       'val_0': val_0,
                       'val_f': migrations,
                       'hosts_0': hosts_on,
                       'hosts_f': hosts_on2,
                       'info': info}
        self.sla.metrics.set(az.az_id, 'consol_d', tuple(this_metric.values()))
        self.logger.info("Before {} on, now {} on. Migrations:{}\n Metric:{}".format(
            hosts_on, hosts_on2, migrations, this_metric.items()))
        return True if migrations > 0 else False

    def do_consolidation_min_mig(self, az):
        all_vms_od, all_hosts_od = OrderedDict(), OrderedDict()
        hosts_on = 0
        frag = az.fragmentation()
        # Todo: Equação xx
        objective = math.floor(frag * len(az.host_list))
        self.logger.info("Consolidate {} with {} hosts, let's turn {} host OFF, because AZ has {:.3f}% frag".format(
            az.az_id, len(az.get_vms_dict()), objective, frag * 100))

        # Objetivo é ter a consolidação com o menor número de migrações considerando tres passos:
        for h in az.host_list:
            # 0) Se o host estiver ligado!
            if h.power_state:  # Todo: and not h.is_full:
                hosts_on += 1
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
            fixedVM.update(fixedVM2)
            vm_to_migrate = vm_to_migrate2

        energy0 = az.get_az_energy_consumption2()
        conf_0 = az.print_hosts_distribution()

        self.logger.debug("{}\t\tAll Hosts Dict: {} \n\nAll VMs dict: {}".format(
            az.az_id, len(all_hosts_od), len(all_vms_od)))
        self.logger.info("\n\t\tFINAL:\nfixedHost: {}\nvm_to_migrate {}".format(fixedHost.keys(), vm_to_migrate.keys()))

        migrations, _ = self.send_to_azmigrate(vm_to_migrate, fixedHost, az)

        conf_f = az.print_hosts_distribution()
        _, hosts_on2, _ = az.get_hosts_density(just_on=True)
        info = "obj:{} __ {} {}".format(objective, conf_0, conf_f)
        this_metric = {'gvt': self.global_time,
                       'energy_0': energy0,
                       'energy_f': az.get_az_energy_consumption2(),
                       'val_0': hosts_on - hosts_on2,
                       'val_f': migrations,
                       'hosts_0': hosts_on,
                       'hosts_f': hosts_on2,
                       'info': info}
        self.sla.metrics.set(az.az_id, 'consol_d', tuple(this_metric.values()))
        return True if migrations > 0 else False

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
        migrations = 0
        return True if migrations > 0 else False

    def send_to_azmigrate(self, vm_d, hosts_d, az, order_hosts=False, order_vms=False):
        suc = 0
        fail = 0
        """Dicionario de VMs em ordem decrescente"""
        if order_hosts:
            hosts_d = OrderedDict(sorted(hosts_d.items(), key=self.sla.key_from_item(lambda k, v: (v.cpu, k))))
        if order_vms:
            vm_d = sorted(vm_d.items(), key=self.sla.key_from_item(lambda k, v: (v.vcpu, k)), reverse=True)
        host_to_remove = []
        for i, vm in vm_d.items():
            h_origin = vm.host_id
            for j, host in hosts_d.items():
                if host.power_state is HOST_ON:
                    self.logger.info("{}\tTrying match v:{}(from {}) to h:{} ".format(az.az_id, i, vm.host_id, j))
                    if az.migrate(vm, host, set_state=HOST_OFF):
                        self.logger.info("{}\tSuccesful Migrated: {} from {} to {} (cpu-remain:{})".format(
                            az.az_id, vm.vm_id, h_origin, host.host_id, host.cpu))
                        suc += 1
                        # Todo: change this to `metrics.incr_1()`
                        self.sla.metrics.update(az.az_id, "avm_history", "migrations", 1, "vm_id", vm.vm_id)
                        break
                    else:
                        fail += 1
                else:
                    host_to_remove.append(host)
            try:
                host_origin_obj = az.host_list_d.get(h_origin)
            except AttributeError:
                self.logger.error("{}\t AttributeError for h_origin: {} p:{} t:{} azvm:{}".format(
                    az.az_id, h_origin, vm.pool_id, vm.type, vm.az_id))
            else:
                if host_origin_obj is not None:
                    if az.remove_generated_hosts(host_origin_obj) or host_origin_obj.try_set_host_off():
                        self.logger.debug("Deleting {}, len:{} remain".format(h_origin, len(hosts_d.keys())))
                        del hosts_d[h_origin]
                        self.logger.info("Deleted {}, now {}".format(h_origin, hosts_d.keys()))
                    else:
                        pass
                else:
                    self.logger.error("Host_Object {} is None! {}".format(h_origin, host_origin_obj))
                    del hosts_d[h_origin]
        return suc, fail

    #############################################
    # Used for both Consolidation and Replication
    #############################################
    def best_host(self, vm, az, recursive=False) -> Tuple[Union[PhysicalMachine, None], list]:
        false_motive = []
        # Todo: Tentar ordenar o host_list pelo uso! Comparar com execuções anteriores
        for host in az.host_list:
            # Doc: 1st, select regular host
            if host.cpu >= vm.get_vcpu() and host.ram >= vm.get_vram():
                self.logger.info("{}\t Best host for {}-{} (vcpu:{}) is {} (cpu:{})".format(
                    az.az_id, vm.get_id(), vm.type, vm.get_vcpu(), host.get_id(), host.cpu))
                return host, false_motive
            else:
                false_motive.append("Regular")
            # Doc: 2nd, try make overcommitting on each host
            if host.can_overcommitting(vm):
                host.do_overcommitting(vm)
                self.logger.info("{}\t Overcom for {} (vcpu:{}), is {} (cpu:{}). Overcom cnt:{}, actual:{}, has:{}.".
                                 format(az.az_id, vm.get_id(), vm.get_vcpu(), host.get_id(), host.cpu,
                                        host.overcom_count, host.actual_overcom, host.has_overcommitting))
                return host, false_motive
            else:
                false_motive.append("Cant_Overcom")

        # Doc: When outside the loop, we can have a problem, but we still can:
        # Doc: 3rd, If our trace is marked as not real, we can create hosts on demand
        if self.sla.g_trace_class() != "REAL":
            self.logger.warning("{}\t Not found existing best host in len:{} for place {}. Lets create a new host."
                                " \n {}\n{}".format(az.az_id, len(az.host_list), vm.get_id(), vm, az))
            if self.api.create_new_host(az.az_id, host_state=HOST_ON):
                for new_host in az.host_list:
                    if new_host.cpu >= vm.get_vcpu() and new_host.ram >= vm.get_vram():
                        self.logger.info("OK! After create new host, for {} (vcpu:{}) is {} (cpu:{})".format(
                            vm.get_id(), vm.get_vcpu(), new_host.get_id(), new_host.cpu))
                        info = "add_new_host: {}".format(new_host.get_id())
                        self.set_rejection_for("add_new_host", 5, info, az.lc_id, vm.pool_id, vm.az_id, vm.vm_id)
                        return new_host, false_motive
                # if out of loop:
                false_motive.append("Resource_New_Host")
            else:
                false_motive.append("Create_New_Host")
        else:
            false_motive.append("Trace_Class")
        #  Doc: 4th We can force one consolidation and recursive to find a best host
        if recursive is False:
            if self.can_consolidate(az):
                self.do_consolidation(az, who_call="Best_Host")
                self.best_host(vm, az, recursive=True)
            # Doc: 5th or if VM is a replica, we can choose other AZ
            if vm.type is REPLICA:
                azlist = list(self.api.get_localcontroller_from_lcid(az.lc_id).az_list)
                # Todo: para remover bloco em 'best_az_for..' basta:
                try:
                    azlist.remove(az)
                except Exception as e:
                    self.logger.exception(e)
                other_az = self.best_az_for_replica(vm, azlist, is_forced=True, az_forced=az)
                if other_az is not None:
                    if not recursive:
                        self.best_host(vm, other_az, recursive=True)
                    pass
                else:
                    self.logger.warning(
                        "{}\t Not found best host in (d, on, off): {} for place {}. \n {}\n{}".format(
                            az.az_id, az.get_hosts_density(), vm.get_id(), vm, az))
        else:
            self.logger.warning("Finnaly, we can't do nothing!!!")
            false_motive.append("Finnaly_do_Nothing!")
        return None, false_motive

    def place(self, vm: VirtualMachine, bhost: PhysicalMachine, az: AvailabilityZone, vm_type=None) -> bool:
        vm.lc_id = az.lc_id
        # Doc: if it is the first time, put VM in replica_pool and continue:
        if self.is_required_replica(vm, az) and vm_type is None:
            self.replicate_vm(vm, az)
        vm.az_id = az.az_id
        vm.set_host_id(bhost.host_id)
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
            # Note: copy because I'll `del` dict inside the loop
            replicas_for_this_lc = dict(self.replication_pool_d[lc_id])
            for pool_id, pool_d in replicas_for_this_lc.items():
                az_list_temp = list(lc_obj.az_list)
                lc_pool = pool_id.split(K_SEP)[0]
                if lc_pool == lc_obj.lc_id:
                    # Note: Before found the best AZ for place the replica, lets remove actual AZ from critical VM
                    try:
                        az_list_temp.remove(pool_d[CRITICAL][0])
                    except Exception as e:
                        self.logger.error("Problem for remove az_critical from {} {}".format(pool_d, e))
                    # Note: iterate in replicas pool
                    # Todo: Create loop `for vm_r in replicas_pool_d`
                    vm_r = pool_d[REPLICA][0]
                    if vm_r.az_id in this_lc_azs:  # Apenas pra confirmar
                        tryes = 0
                        az = self.best_az_for_replica(vm_r, az_list_temp)
                        if az is not None:
                            # Note: Ok! we found one AZ, lets remove for the, who knows, another replica:
                            try:
                                az_list_temp.remove(az)
                            except Exception as e:
                                self.logger.error("Problem for remove AZ Replica {} {}".format(az.az_id, e))
                            b_host, info_bh = self.best_host(vm_r, az)
                            if b_host is not None:
                                energy0 = az.get_az_energy_consumption2()
                                _, hosts_on0, _ = az.get_hosts_density(just_on=True)
                                if self.place(vm_r, b_host, az, vm_type=REPLICA):
                                    self.replicas_execution_d[lc_id][pool_id] = vm_r
                                    self.logger.info("{}\t Successful Allocated {} {} on {}".format(
                                        lc_id, REPLICA, vm_r.vm_id, vm_r.az_id))
                                    try:
                                        # del pool_d[REPLICA][0]
                                        del self.replication_pool_d[lc_id][pool_id]
                                    except Exception as e:
                                        self.logger.exception(e)
                                        self.logger.error("{}\t Delete REPLICA from pool {} on {}".format(
                                            lc_id, vm_r.pool_id, vm_r.az_id))
                                    energyf = az.get_az_energy_consumption2()
                                    _, hosts_onf, _ = az.get_hosts_density(just_on=True)
                                    this_metric = {'gvt': self.global_time,
                                                   'energy_0': energy0,
                                                   'energy_f': energyf,
                                                   'val_0': hosts_onf - hosts_on0,
                                                   'val_f': len(self.replicas_execution_d[lc_id]),
                                                   'hosts_0': hosts_on0,
                                                   'hosts_f': hosts_onf,
                                                   'info': "pool_id:{}, info_bh:{}".format(pool_id, len(info_bh))}
                                    self.sla.metrics.set(az.az_id, 'replic_d', tuple(this_metric.values()))
                                    self.logger.info("this_metric: {}".format(this_metric))
                                else:
                                    self.logger.error("{}\t On place REPLICA {}".format(lc_id, pool_id))
                            else:
                                info = "Best Host try:{}, bh:{}".format(tryes, len(info_bh))
                                self.set_rejection_for("replication", 3, info, lc_id, pool_id, az.az_id, vm_r.vm_id)
                                tryes += 1
                        else:  # Best az for replica is None
                            info = "Best AZ try:{}".format(tryes)
                            self.set_rejection_for("replication", 2, info, lc_id, pool_id, vm_r.az_id, vm_r.vm_id)
                    else:  # vm_replica not in this LC azs
                        pass
                    # Todo: create other opportunities for replication:
                    # 0 Reject
                    # 1 Accept replicas in same AZ -> calculate final availability
                    # 2 Accept replicas in other local_controler
                    # if self.replication_scale == 0:
                    #    break
                else:
                    self.logger.error("lc_pool {} != {} lc_obj.lc_id".format(pool_id, lc_id))
        # EXIT!

    def best_az_for_replica(self, vm, az_list, is_forced=False, az_forced=None) -> AvailabilityZone:
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
        # try:
        #    temp_az_list.remove(actual_az)
        # except ValueError:
        # self.logger.error(
        #    "{}\t ACTUAL_AZ: ({}) not in list {} ValueError".format(vm.az_id, actual_az.az_id, temp_az_list))
        # return None
        # except Exception as e:
        #    # self.logger.exception(type(e))
        #    self.logger.error("{}\t UNKNOWN: ({}) not in list {} {}".format(vm.az_id, actual_az, temp_az_list, e))
        #    # raise e
        #    return None

        # Todo: analizar e remover este bloco depois
        if is_forced and az_forced is not None:
            try:
                temp_az_list.remove(az_forced)
            except ValueError:
                self.logger.error(
                    "{}\t AZ_FORCED: ({}) not in list {} ValueError".format(vm.az_id, actual_az.az_id, temp_az_list))
                return None
            except Exception as e:
                self.logger.error(
                    "{}\t UNKNOWN AZ_FORCED ({}) not in list {} {}".format(vm.az_id, actual_az, temp_az_list, e))
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
                    self.logger.debug("{}\tNew BestHost HA: av:{}%".format(az.az_id, az.availability * 100))
                    this_target_ha = float(az.availability)
                    best_az = az
            elif az_selection == "LB":
                new_usage, _, _ = az.get_hosts_density()
                if new_usage < this_target_lb:
                    self.logger.debug("{}\tNew BestHost LB: usg:{}%".format(az.az_id, new_usage * 100))
                    this_target_lb = new_usage
                    best_az = az
            elif az_selection == "RND" or is_forced:
                best_az = temp_az_list[randint(0, len(temp_az_list) - 1)]
                break  # '''Do this once one time'''
            else:
                self.logger.error("We must define the 'az selection' method, but have {}".format(self.sla.g_az_selection()))
        if best_az is None:
            try:
                best_az = temp_az_list.pop()
            except:
                pass
            self.logger.warning("AZ selection '{}' fails, we'll place {} (from {}) RND in {} list:{}".format(
                az_selection, vm.vm_id, vm.az_id, best_az, temp_az_list))
            return best_az
        self.logger.info("{} from ({}), {}  will be replicated for {}".format(
            vm.vm_id, vm.az_id, az_selection, best_az))
        return best_az

    def is_required_replica(self, vm, az):
        if vm.availab > az.availability and vm.type != REPLICA:
            self.logger.debug("{}-{} require replication! {}=?{}".format(vm.vm_id, vm.type, vm.az_id, az.az_id))
            return True
        return False

    def replicate_vm(self, vm, az):
        lc_id = az.lc_id
        pool_id = "{}{}{}{}{}".format(vm.lc_id, K_SEP, vm.az_id, K_SEP, vm.vm_id)
        if pool_id not in self.replication_pool_d[lc_id]:
            vm.pool_id = pool_id
            attr = vm.getattr()
            vm.type = CRITICAL
            vm_replica = VirtualMachine(*attr)
            vm_replica.type = REPLICA
            vm_replica.pool_id = pool_id
            replicas_join = [vm_replica]
            self.replication_pool_d[lc_id][pool_id] = {CRITICAL: [az, vm], REPLICA: replicas_join}
            ''' Todo: Refazer futuramente pra suportat multiplas réplicas
            number_of_replicas = self.sla.get_required_replicas(az.availability, ha=vm.availab)
            # Todo: desfazer isso e arrumar no codigo
            if number_of_replicas > 2:
                number_of_replicas = 2
            replicas_join = []
            for i in range(number_of_replicas):
                vm_replica = VirtualMachine(*attr)
                vm_replica.type = "{}{}{}".format(REPLICA, K_SEP, i)
                vm_replica.pool_id = pool_id
                replicas_join.append(vm_replica)
            self.replication_pool_d[lc_id][pool_id] = {CRITICAL: [az, vm], REPLICA: replicas_join}
            '''
            self.logger.info("Pool {} created for replication:\n\t\tCritical:{}\n\t\tReplicas:{}\n".format(
                pool_id, self.replication_pool_d[lc_id][pool_id][CRITICAL],
                self.replication_pool_d[lc_id][pool_id][REPLICA]))
            return True
        self.logger.error("{}\t Pool {} already in replication_pool_d[{}]!".format(az.az_id, pool_id, lc_id))
        return False

    #############################################
    ### Miscelaneous
    #############################################
    """
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

    def set_demand(self, demand):
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
        """
