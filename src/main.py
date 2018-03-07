#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import logging
from copy import deepcopy
import random
from math import sqrt
from numpy import std, mean, sqrt
import numpy as np
import timeit
import time
from collections import OrderedDict

#from BaseInfrastructure import SLA_BASED, VI_BASED
from Virtual import VirtualMachine
from Datacenter import *
from Chave import Chave
#from Controller import *

def my_std(data):
    u = mean(data)
    std = sqrt(1.0 / (len(data) - 1) * sum([(e - u) ** 2 for e in data]))
    return 1.96 * std / sqrt(len(data))

def mean(data):
    return sum(data) / float(len(data))

def get_vms_from_source(source_file):
    operation_dict = OrderedDict()
    vm_list = []
    vm_allocate = []
    line = 0
    with open(source_file, 'r') as source:
        for operation in source:
            line =      line + 1
            operation = operation.split()
            ha =        ha_on_demand(availability, 0.999999999999937) # 4 replicas em AZs de 0,9995 @TODO: calcular HA para 5 AZs
            state =     str(operation[0])
            timestamp = int(operation[1])
            vm_id =     str(operation[2])
            op_id =     str(vm_id + '-' + state)
            type = "VM"
            if state == "START":
                if algorithm == "CHAVE": # alocaremos depois
                    host = "None"
                if algorithm == "EUCA":
                    host = str(operation[3]) # alocação padrão
                vcpu =  int(operation[4])
                vram =  vmRam_default * vcpu
                lifetime = 0
                #print (vm_id, vcpu, vram, ha, availability, type, host, dcid, timestamp, lifetime)
                vm = VirtualMachine(vm_id, vcpu, vram, ha, availability, type, host, dcid, timestamp, lifetime, logger)
                vm_list.append(vm)
                vm_allocate.append(vm)
                operation_dict[op_id] = vm

            elif state == "STOP":
                last_op_id = str(vm_id + '-START')
                try:
                    lifetime = timestamp - int(operation_dict[last_op_id].get_timestamp())
                except:
                    logger.error("on LIFETIME"+str(lifetime))
                    lifetime = -1
                if algorithm == "CHAVE":
                    host = None
                else:
                    host = operation_dict[last_op_id].get_physical_host() # alocação padrão

                vcpu = operation_dict[last_op_id].get_vcpu()
                ha = operation_dict[last_op_id].get_ha()
                vram = operation_dict[last_op_id].get_vram()

                vm = VirtualMachine(vm_id, vcpu, vram, ha, availability, type, host, dcid, timestamp, lifetime, logger)
                vm_to_pop = operation_dict[last_op_id]
                #vm_list.append(vm)
                operation_dict[op_id] = vm
                #print "vm", line,":", vm.get_parameters(),
                try:
                    vmindex = vm_allocate.index(vm_to_pop)
                    vm_allocate.pop(vmindex)
                except:
                    logger.error("On pop VM"+str(op_id))
        if vm_allocate != []:
            logger.error("On deallocate:"+str(vm_allocate))
    return vm_list, operation_dict

def ha_on_demand(av, max):
    if monte_carlo():
        return np.random.uniform( av, max )
    return av

def monte_carlo():
    x = np.random.rand(1)
    y = np.random.rand(1)
    # Funcao que retorna 21% de probabilidade
    if x ** 2 + y ** 2 >= 1:
        return True
    return False

def test_ha_on_demand(iterations, av, ha):
    v = []
    for i in range(iterations):
        v.append(ha_on_demand(av, ha))
    #print np.mean(v), np.std(v), np.amin(v), np.amax(v)
    #print "prob. non-ha:", 100*v.count(np.amin(v)) / float(iterations), "prob. ha grater mean:",100*sum(i > np.mean(v) for i in v)/float(iterations)

def metrics(command, key, value, n): #metrics_dict{}
    command_list = ['get', 'set', 'add', 'init', 'resume']
    key_list = ['total_alloc', 'accepted_alloc',
    'acc_list', 'acc_means', 'energy_list', 'energy_means', 'nop_list', 'nop_means',
    'sla_break', 'sla_break_steal', 'alloc', 'total_alloc_list', 'dealloc', 'realloc', 'energy_rlc',
    'energy_ttl', 'dc_vm_load', 'dc_load']
    if command in command_list:
        if command is 'init':
            if key is "ALL":
                key1 = key_list[0:2]
                key2 = key_list[2:8]
                key3 = key_list[8:17]
                key = [key1, key2, key3]
            if value == "INIT":
                for kk in key:
                    x=len(kk)
                    for k in kk:
                        if x == 2: metrics_dict[k]= 0.0
                        elif x == 6: metrics_dict[k] = []
                        elif x == 9:  metrics_dict[k] = [0 for i in range(nit)]
        if command is 'set':
            if key in key_list[0:2]:
                metrics_dict[key] = value
                return True
            if key in key_list[2:8]:
                metrics_dict[key].append(value)
                return True

        if command is 'get':
            if key in key_list:
                return metrics_dict[key]

        if command is 'add':
            if key in key_list[2:17]:
                metrics_dict[key] = metrics_dict[key] + value
                return metrics_dict[key]
                #sum([v.get_vram() for v in self.virtual_machine_list])

        if command is 'resume':
            if key in key_list[2:17]:
                return sum(values for values in metrics_dict[key])
            elif key in key_list[0:2]:
                return metrics_dict[key]
    else:
        logger.error("Command ("+str(command)+") not found!!")
    return None

def opdict_to_vmlist(id):
    for vm_temp in vm_list:
        if vm_temp.get_id() == id:
            return vm_temp
    return None

def run_test_chave(dc):
    chave = Chave(pm, ff, trigger_to_migrate, frag_percentual, window_time, window_size, has_overbooking, logger)
    metrics("init","ALL", "INIT", nit)
    requisitions_list = []
    this_cycle = window_time
    arrival_time = 0
    req_size, req_size2, energy = 0, 0, 0.0
    max_host_on = 0
    req_size_list = []
    op_dict_temp = operation_dict
    FORCE_PLACE = False

    while arrival_time < this_cycle and len(op_dict_temp.items()) > 0:
        new_host_on, off = dc.each_cycle_get_hosts_on()
        if new_host_on > max_host_on:
            max_host_on = new_host_on
            logger.info("New max host on: " + str(max_host_on) + str(off) + " at " + str(arrival_time) + " sec.")
        for op_id, op_vm in op_dict_temp.items():
            # MIGRATE FIRST
#            if pm == "MigrationFirst" and (chave.is_time_to_migrate(this_cycle) or dc.has_fragmentation()):
#                dc = chave.migrate(dc)
#                print "migrating at:", this_cycle, "with:", chave.get_last_number_of_migrations(), "migrations"
            arrival_time = op_vm.get_timestamp()
            vm = opdict_to_vmlist(op_vm.get_id())
            if (arrival_time < this_cycle):
                this_state = op_id.split('-')[2]
                if this_state == "START":
                    requisitions_list.append(vm)
                    req_size += 1
                    req_size2 = len(requisitions_list)
                    # PLACEMENT
                    if (chave.is_time_to_place(this_cycle) or chave.window_size_is_full(req_size)) or FORCE_PLACE is True:
                        new_host_list = chave.place(requisitions_list, dc.get_host_list())
                        if new_host_list is not None:
                            energy = energy + dc.get_total_energy_consumption()

                            #x = metrics('add','energy_ttl',energy, None)
                            dc.set_host_list(new_host_list)
                            requisitions_list = []
                            req_size = 0
                            FORCE_PLACE = False
                        else:
                            logger.error("New_host_list problem:"+str(new_host_list))
                        del op_dict_temp[op_id]

                elif this_state == "STOP" and vm not in requisitions_list: #adicionado na ultima janela
                    dc.deallocate_on_host(vm)
                    del op_dict_temp[op_id]
                else:
                    logger.info("\n\t\t\t\t"+str(op_id)+"STILL IN REQ_LIST, LETS BREAK.")
                    FORCE_PLACE=True
                    break
            else:
                # Enquanto não há requisições, incremente o relógio
                while (arrival_time >= this_cycle):
                    this_cycle += window_time
                #print "\nNOVA FILA: ", this_cycle, "[", arrival_time, op_id.split('-')[1], "],[",
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
        logger.debug("Final:"+str(algorithm)+" last arrival:"+str(arrival_time)+", lastCicle:"+str(this_cycle)+", len(op_dict):"+str(len(op_dict_temp.items())))
    return dc, max_host_on

def run_test_euca(dc):
    metrics("init", "ALL", "INIT", -1)
    requisitions_list = []
    this_cycle = window_time
    arrival_time = 0
    req_size = 0
    max_host_on = 0
    req_size_list = []
    op_dict_temp = operation_dict
    while ((arrival_time < this_cycle) and (len(op_dict_temp.items()) > 0 )):
        for op_id, op_vm in op_dict_temp.items():
            arrival_time = op_vm.get_timestamp()
            vm = opdict_to_vmlist(op_vm.get_id())
            if (arrival_time < this_cycle): # @TODO: or (req_size < window_size):
                this_state = op_id.split('-')[2]
                new_host_on, off = dc.each_cycle_get_hosts_on()
                if new_host_on > max_host_on:
                    max_host_on= new_host_on
                    logger.info("New max host on: "+str(max_host_on)+str(off)+" at "+str(arrival_time)+" sec.")
                if this_state == "START":
                    if dc.allocate_on_host(vm):
                        requisitions_list.append(vm)
                        req_size += 1
                elif this_state == "STOP":
                    dc.deallocate_on_host(vm)
                # Remova do dict temporario
                del op_dict_temp[op_id]
            else:
                #Enquanto não há requisições, incremente o relógio
                while (arrival_time >= this_cycle):
                    this_cycle += window_time
                if req_size >= window_size:
                    logger.info("req_size"+str(req_size))
                req_size_list.append(req_size)
                req_size = 0
                requisitions_list = []
                break
#        print "\t\tout: ", arrival_time, thiscycle, len(op_dict_temp.items())
    return dc, max_host_on

def main():

    start = time.time()
    if algorithm == "CHAVE":
        new_dc, maxhost = run_test_chave(dc)
    elif algorithm == "EUCA":
        new_dc, maxhost = run_test_euca(dc)
    elapsed = time.time() - start

    slav = new_dc.get_total_SLA_violations_from_datacenter()
    energy = new_dc.get_total_energy_consumption()
    overb_list = new_dc.get_list_overb_amount()

    logger.warning("SLAV:"+str(slav)+", Energy:"+str(energy)+", Overbooked:"+str(len(overb_list))+", timelapse:"+str(elapsed)+", maxhost:"+str(maxhost))


    with open("FINAL_"+output, 'aw') as log:
        log.write('%s\t%d\t%d\t%d\t%f\t%d\n' % (dcid, window_size, window_time, slav, energy, len(overb_list)))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='CHAVE')
    parser.add_argument('-nit', dest='nit',     action='store', nargs=1,type=int, help='Number of iterations: N',  required=True)
    parser.add_argument('-alg', dest='algorithm',action='store', nargs=1,  help='algorithm type: CHAVE|EUCA',   required=True)
    parser.add_argument('-pm',  dest='pm',      action='store', nargs=1,    help='placement or migration',  required=True)
    parser.add_argument('-ff',  dest='ff',      action='store', nargs=1,    help='first fit algorithm',     required=True)
    parser.add_argument('-in',  dest='input',   action='store', nargs=1,    help='Input file',              required=True)
    parser.add_argument('-az',  dest='azConf',  action='store', nargs='+',  help='AZ configuration',        required=True)
    parser.add_argument('-out', dest='output',  action='store', nargs=1,    help='Results output directory',required=True)
    parser.add_argument('-av',  dest='availab', action='store', nargs=1,    help='Availability from AZ',    required=True)
    parser.add_argument('-wt',  dest='wt',      action='store', nargs=1,type=int, help='Window time: N',    required=True)
    parser.add_argument('-ws',  dest='ws',      action='store', nargs=1,type=int, help='Window size: N',    required=True)
    parser.add_argument('-ovb', dest='overb',   action='store', nargs=1,type=bool, help='Has Overbooking?',  required=True)

    args = parser.parse_args()
    nit = int(args.nit[0]/2)
    pm = args.pm[0]
    ff = args.ff[0]
    has_overbooking=args.overb[0]
    algorithm = str(args.algorithm[0])
    window_time = int(args.wt[0])
    window_size = int(args.ws[0])

    availability = float(args.availab[0])
    source_file = args.input[0]
    n=str(source_file).find("DS")
    dcid = str(source_file[n:n+3])
    #dcid = str(source_file[len(source_file) - 13:len(source_file) - 10])
    output = args.output[0].split('.')[0]+"_"+dcid+".log"
    azNodes = int(args.azConf[0].split(':')[0])
    azCores = int(args.azConf[0].split(':')[1])
    ram2core="1:4"
    vmRam_default = int(ram2core.split(':')[1])
    azRam = vmRam_default * azCores

    #Para os logs de mensagens:
    logging.basicConfig(level=logging.DEBUG)
    #logging.config.fileConfig('logging.ini')
    logger = logging.getLogger(__name__)
    hdlr = logging.FileHandler('logs/'+output)
    formatter = logging.Formatter('[%(levelname)s] \t%(filename)s->%(funcName)s: \t %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    # Especifique o nível de log:
    #logger.setLevel(logging.WARNING)

    # Global vars:
    dc = Datacenter(azNodes, azCores, availability, dcid, azRam, algorithm, has_overbooking,logger)
    host_list = dc.create_infrastructure()
    dc.set_host_list(host_list)
    vm_list, operation_dict = get_vms_from_source(source_file)
    metrics_dict = {}

    trigger_to_migrate = 3600
    frag_percentual = float(0.3)

    main()
    #logger levels: debug, info, warning, error, critical