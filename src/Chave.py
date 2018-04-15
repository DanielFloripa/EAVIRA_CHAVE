#!/usr/bin/python
# -*- coding: utf-8 -*-

from random import randint
import math
from copy import deepcopy
from DistributedInfrastructure import *

class Chave(object):
    def __init__(self, pm_mode, ff_mode, trigger_to_migrate, frag_percentual, window_time, window_size, op_dict, has_ovbkg, logger):
        self.logger = logger
        self.trigger_to_migrate = trigger_to_migrate
        self.frag_percentual = frag_percentual
        self.pm_mode = pm_mode
        self.ff_mode = ff_mode
        self.window_time = window_time
        self.window_size = window_size
        self.dc_has_overbooking = has_ovbkg
        self.last_number_of_migrations = 0
        self.operation_dict = op_dict
        self.dbg = [ ] #  "overb", "migr", "probl", "ok"]

    def run_test_chave(self, dc, helper):
        #chave = Chave(pm, ff, trigger_to_migrate, frag_percentual, window_time, window_size, has_overbooking, logger)
        helper.metrics("init", "ALL", "INIT", nit)
        requisitions_list = []
        this_cycle = self.window_time
        arrival_time = 0
        req_size, req_size2, energy = 0, 0, 0.0
        max_host_on = 0
        req_size_list = []
        op_dict_temp = self.operation_dict
        FORCE_PLACE = False
        # SE O TEMPO DE CHEGADA ESTA NESTE CICLO:
        while arrival_time < this_cycle and len(op_dict_temp.items()) > 0:
            new_host_on, off = dc.each_cycle_get_hosts_on()
            if new_host_on > max_host_on:
                max_host_on = new_host_on
                self.logger.info("New max host on:"+str(max_host_on)+str(off)+\
                                 "at"+str(arrival_time)+"sec.")
            for op_id, op_vm in op_dict_temp.items():
                # MIGRATE FIRST
                #            if pm == "MigrationFirst" and (chave.is_time_to_migrate(this_cycle) or dc.has_fragmentation()):
                #                dc = chave.migrate(dc)
                #                print "migrating at:", this_cycle, "with:", chave.get_last_number_of_migrations(), "migrations"
                arrival_time = op_vm.get_timestamp()
                vm = helper.opdict_to_vmlist(op_vm.get_id())
                if arrival_time < this_cycle:
                    this_state = op_id.split('-')[2]
                    if this_state == "START":
                        requisitions_list.append(vm)
                        req_size += 1
                        req_size2 = len(requisitions_list)
                        # PLACEMENT
                        if (self.is_time_to_place(this_cycle) or self.window_size_is_full(
                                req_size)) or FORCE_PLACE is True:
                            new_host_list = self.place(requisitions_list, dc.get_host_list())
                            if new_host_list is not None:
                                energy = energy + dc.get_total_energy_consumption()

                                # x = metrics('add','energy_ttl',energy, None)
                                dc.set_host_list(new_host_list)
                                requisitions_list = []
                                req_size = 0
                                FORCE_PLACE = False
                            else:
                                self.logger.error("New_host_list problem:" + str(new_host_list))
                            del op_dict_temp[op_id]

                    elif this_state == "STOP" and vm not in requisitions_list:  # adicionado na ultima janela
                        dc.deallocate_on_host(vm)
                        del op_dict_temp[op_id]
                    else:
                        self.logger.info("\n\t\t\t\t" + str(op_id) + "STILL IN REQ_LIST, LETS BREAK.")
                        FORCE_PLACE = True
                        break
                else:
                    # Enquanto não há requisições, incremente o relógio
                    while arrival_time >= this_cycle:
                        this_cycle += self.window_time
                    # print "\nNOVA FILA: ", this_cycle, "[", arrival_time, op_id.split('-')[1], "],[",
                    req_size_list.append(req_size)
                    req_size = 0
                    requisitions_list = []
                    break
            # PLACEMENT FIRST
            #        if pm == "PlacementFirst" and (chave.is_time_to_migrate(this_cycle) or dc.has_fragmentation()):
            #            dc = chave.migrate(dc)
            ##            last_host_list = dc.get_host_list()
            ##            empty_host_list = dc.create_infrastructure()
            ##            new_host_list = chave.migrate(last_host_list, empty_host_list)
            ##            dc.set_host_list(new_host_list)
            #            print "migrating at:", this_cycle, "with:", chave.get_last_number_of_migrations(), "migrations"
            self.logger.debug("Final:" + str(algorithm) + " last arrival:" + str(arrival_time) + ", lastCicle:" + str(
                this_cycle) + ", len(op_dict):" + str(len(op_dict_temp.items())))
        return dc, max_host_on

    def order_ff_mode(self, host_list):
        if self.ff_mode == "FFD2I": # crescente
            host_list.sort(key=lambda e: e.get_cpu())
        elif self.ff_mode == "FF3D": # decrescente
            host_list.sort(key=lambda e: e.get_cpu(), reverse=True)
        return host_list # se nenhuma configuração

    '''
        VM = list()
        VM = self.generateInputVM(randint(2, 5), Configuracao, False)
        # VM = [(4, 8), (4, 8), (4, 8), (2, 4), (2, 4)]
        # VM = [(8, 16), (1, 2), (1, 2)]

        VM.sort(reverse=True)

        Hosts = list()
        Hosts = self.generateInputHost(randint(2, 5), Configuracao, False)
        # Hosts = [[(4, 8)],[(4, 8), (2, 4)],[(8, 16)]]
        # Hosts = [[(4, 8), (2, 4)],[(1, 2)],[(1, 2)]]

        initHosts = len(Hosts)
        totalVMsHosted_t0 = self.verifyVmsHosted(Hosts)


    def isPower(num, base, debug='False'):
        if base == 1 and num != 1: return False
        if base == 1 and num == 1: return True
        if base == 0 and num != 1: return False
        power = int(math.log(num, base) + 0.5)
        return base ** power == num

    def generateInputHost(hostMax, config, debug='False'):
        allHosts = list()

        for h in xrange(0, hostMax):
            oneHost = list()
            resourceFree = config['maxcpu']
            if debug: print "Creating Host: ", h, ", with: ", resourceFree, "CPUs"
            vmsOnThisHost = randint(1, config['maxcpu'])
            if debug: print "I wanna alocate:", vmsOnThisHost, "VMs On This Host"
            while (vmsOnThisHost):
                VM = generateInputVM(1, config)
                if debug: print "\tVM: ", (VM[0][0], VM[0][1])
                resourceFree = resourceFree - VM[0][0]
                if (resourceFree > 0) or (len(oneHost) == 0):
                    oneHost.append((VM[0][0], VM[0][1]))
                    if debug: print "\t\tResource Free: ", resourceFree
                    vmsOnThisHost = vmsOnThisHost - 1
                else:
                    if debug: print "\nFalta de recursos de CPU: ", resourceFree
                    break
            oneHost.sort(reverse=True)  # descrescente
            allHosts.append(oneHost)

        if len(allHosts) == hostMax:
            # if debug: print allHosts
            return allHosts
        else:
            if debug: print "Houve algum erro ao gerar Hosts"
            exit()


    def generateInputVM(vmsMax, config, debug='False'):
        base = 2
        VMs = list()
        control = vmsMax
        while (control):
            rand = randint(1, config['maxcpu'])
            if isPower(rand, base):
                VMs.append((rand, int(rand * (1 / config['ratio']))))
                control = control - 1

        if len(VMs) == vmsMax:
            return VMs
        else:
            if debug: print "Houve algum erro ao gerar VMs"
            exit()


    def consistency(VM, Hosts, config, debug='False'):
        totalVM = [0, 0]

        for (VCPU, VRAM) in VM:
            assert (VCPU <= config['maxcpu']), "VCPU bigger than maxcpu: " + str(VCPU)
            assert (VRAM <= config['maxram']), "VRAM bigger than maxram: " + str(VRAM)
            assert (self.isPower(VCPU, 2)), "VCPU is not a powor of 2: " + str(VCPU)
            assert (self.isPower(VRAM, 2)), "VRAM is not a powor of 2: " + str(VRAM)
            assert (VRAM / VCPU == 1 / config['ratio']), "Ratio uncompatible: " + str([VRAM, VCPU, VRAM / VCPU])
            totalVM[0] = totalVM[0] + VCPU
            totalVM[1] = totalVM[1] + VRAM

        sumHCPU, tAvHosts = self.availableResources(Hosts, config)

        ativar = 0
        if totalVM[0] <= sumHCPU:
            if debug: print "Nao sera necessario ligar novas maquinas"
        else:
            ativar = math.ceil(float(totalVM[0] - sumHCPU) / float(config['maxcpu']))
            it = ativar
            while (it):
                Hosts.append([(0, 0)])
                it = it - 1
        if debug: print "Demanda recursos CPU:", totalVM[
            0], ", CPU disponivel:", tAvHosts, "=", sumHCPU, ", ativando ", ativar, " novas maquinas\n"

        return (Hosts, tAvHosts, ativar)


    def availableResources(Hosts, config, debug='False'):
        sumHCPU = len(Hosts) * config['maxcpu']
        tAvHosts = list()

        for host in Hosts:
            totalAvailableHost = [config['maxcpu'], config['maxram']]
            for (HCPU, HRAM) in host:
                assert (HCPU <= config['maxcpu']), "HCPU bigger than maxcpu"
                assert (HRAM <= config['maxram']), "HRAM bigger than maxram"
                totalAvailableHost[0] = totalAvailableHost[0] - HCPU
                totalAvailableHost[1] = totalAvailableHost[1] - HRAM
                sumHCPU = sumHCPU - HCPU
            tAvHosts.append(totalAvailableHost)
        return sumHCPU, tAvHosts
    
    '''

    def best_host(self, vm, host_list):
        for host in host_list:
            if host.get_cpu() >= vm.get_vcpu() and host.get_ram() >= vm.get_vram(): # TODO: add analise de ram
                self.logger.debug("Yes!, Best host for"+str(vm.get_id())+"("+str(vm.get_vcpu())+"vcpu), is"+str(host.get_id())+\
                                 "("+str(host.get_cpu())+"cpu). OverbCount:"+str(host.overb_count)+"tax:"+str(host.actual_overb)+\
                                 "has?"+str(host.has_overbooking))
                return host, True
            else:
                if self.dc_has_overbooking and host.can_overbooking(vm):
                    if "overb" in self.dbg:  self.logger.debug("Overb. for"+vm.get_id()+"("+str(vm.get_vcpu())+"cpu), is"+\
                        host.get_id()+"("+str(host.get_cpu())+"). Overb:"+str(host.overb_count)+str(host.actual_overb)+str(host.has_overbooking))
                    host.do_overbooking(vm)
                    return host, True
        return host, False

    def place(self, vm_list, host_list):
        vm_list.sort(key=lambda e: e.get_cpu(), reverse=True) # decrescente
        host_ff_mode = host_list # TODO: ver se e necessario: self.order_ff_mode(host_list)
        for vm in vm_list:
            bhost, state = self.best_host(vm, host_ff_mode)
            if state is False:
                self.logger.error("PROBLEM: not found best host for placement.")
            else:
                vm.set_physical_host(bhost.get_id())
                if bhost.allocate(vm):
                    host_ff_mode.append(bhost)
                else:
                    self.logger.error("Problem on allocate at placement")
                    return host_list
        return host_ff_mode


    '''
    def migrate(self, last_host_list, new_host_list):
        vm_list_to_migrate = []
        host_list_to_receive = []
        len_in = len(last_host_list)
        #new_dc = Datacenter(dc.azNodes, dc.azCores, dc.availability, dc.az_id, dc.azRam, dc.algorithm)
        #new_dc = deepcopy(dc)
        #new_dc.set_host_list([])
        #Criando a lista com todas as mvs em execução:
        for eachHost in last_host_list:
            print eachHost.get_id(), len(eachHost.get_virtual_resources())
            for vm in eachHost.get_virtual_resources():
                vm_list_to_migrate.append(vm)

        # Aplicando o ordenação decrescente:
        vm_list_to_migrate.sort(key=lambda e: e.get_vcpu(), reverse=True)
        if self.dbg: print "lendiff", len_in, len(vm_list_to_migrate), "=", len_in - len(vm_list_to_migrate)

        for vm in vm_list_to_migrate:
            print "next vm:", vm.get_id()
            for eachHost in new_host_list:
                if eachHost.allocate(vm):
                    host_list_to_receive.append(eachHost)
                    if self.dbg: print "Migr.", vm.get_id(), "to", eachHost.get_id()
                    if vm.get_physical_host().get_id() == eachHost.get_id:
                        self.last_number_of_migrations -= 1
                    self.last_number_of_migrations += 1
                    break
                else:
                    if eachHost.can_overbooking(vm):
                        if self.dbg: print "Overbook on migr. vm", vm.get_id()
                        eachHost.do_overbooking(vm)
                        if eachHost.allocate(vm):
                            if self.dbg: print "Migr.", vm.get_id(), "to", eachHost.get_id()
                            if vm.get_physical_host().get_id() == eachHost.get_id:
                                self.last_number_of_migrations -= 1
                            self.last_number_of_migrations += 1
                            break
                    else:
                        if self.dbg: print "PROBLEM ON MIGRATE after overbooking", vm.get_id(), len(new_host_list), eachHost.get_id()
        return host_list_to_receive
        #return dc
    '''

    def migrate(self, dc):
        vm_list_to_migrate = []

        new_dc = AvailabilityZone(dc.get_azNodes(), dc.get_azCores(), dc.get_availability(),
                                  dc.get_id(), dc.get_azRam(), dc.get_algorithm(), dc.get_flag_overbooking())
        # Criando a lista com todas as mvs em execução:
        for eachHost in dc.get_host_list():
            for vm in eachHost.get_virtual_resources():
                # TODO porque 'migrate?' Marcacao Transitoria
                vm.set_physical_host("migrate")
                vm_list_to_migrate.append(vm)

        # Aplicando o ordenação decrescente:
        vm_list_to_migrate.sort(key=lambda e: e.get_vcpu(), reverse=True)

        for vm in vm_list_to_migrate:
            if "migr" in self.dbg: self.logger.debug("next vm:"+str(vm.get_id()))
            for eachHost in new_dc.get_host_list():
                if new_dc.allocate_on_host(vm):
                    self.last_number_of_migrations += 1
                    break
                else:
                    self.last_number_of_migrations -= 1
                    self.logger.error("PROBLEM ON MIGRATE after overbooking"+str(vm.get_id())+str(eachHost.get_id())+str(eachHost.overb_count))
        return new_dc

    def get_last_number_of_migrations(self):
        ret = self.last_number_of_migrations
        self.last_number_of_migrations = 0
        return ret

    def is_time_to_migrate(self, time):
        if time % self.trigger_to_migrate == 0:
            return True
        return False

    def is_time_to_place(self, cicle):
        if cicle % self.window_time == 0:
            return True
        return False

    def window_size_is_full(self, req_size):
        if req_size >= self.window_size:
            return True
        return False

    def alocate_vm_list_on_dc(self, vm_list):
        pass

    def dealocate_vm_list_on_dc(self, vm_list):
        pass

    '''

    def printHosts(Hosts):
        i = 0
        for host in Hosts:
            if self.dbg: print "Host[", i, "]:", host
            i = i + 1

    def verifyVmsHosted(Hosts):
        totalVMsHosted = 0
        for host in Hosts:
            totalVMsHosted = totalVMsHosted + len(host)
        return totalVMsHosted




        HostsMigration, VMMigration = migration(Hosts, Configuracao, debug)
        if self.dbg: print "\nResults from migration:\n", HostsMigration, "hosts active", len(HostsMigration), "\n"

        if self.debug: print "Requests for Placement\nVMs:", VM, "\n", printHosts(HostsMigration), "\n"
        lenHostsMigration = len(HostsMigration)

        HostsMigration, _, _ = consistency(VM, HostsMigration, Configuracao, debug)
        HostsMigration.sort(reverse=True)

        HostsPlacement = self.placement(VM, HostsMigration, self.Configuracao, self.debug)
        if self.dbg: print "\nResults from Placement:\n", HostsPlacement, "hosts active", len(HostsPlacement), "\n"

        totalVMsHosted_tf = verifyVmsHosted(HostsPlacement)

        if self.dbg: print "Requested VMs", len(VM), ",total VMs Hosted in t0:", totalVMsHosted_t0, " - t final:", totalVMsHosted_tf
        if (totalVMsHosted_tf - totalVMsHosted_t0 == len(VM)):
            if self.dbg: print "\tThats OK!"
        else:
            if self.dbg: print "Alguem ficou de fora!!"

        if self.dbg: print "Qtdd Hosts inicial:", initHosts, "After migr:", lenHostsMigration, "After placem.:", len(HostsPlacement)
        if self.dbg: print "An overhead of placement: ", (float(len(HostsPlacement)) - float(initHosts)) / float(initHosts) * 100, "%"
        if self.dbg: print "An overhead of migration: ", (float(len(HostsPlacement)) - float(lenHostsMigration)) / float(
            lenHostsMigration) * 100, "%"
        if self.dbg: print "A final overhead: ", (float(initHosts) - float(lenHostsMigration)) / float(lenHostsMigration) * 100, "%"
    '''
