#!/usr/bin/python
# -*- coding: utf-8 -*-

class Eucalyptus(object):
    def __init__(self, sla):
        self.sla = sla
        self.logger = sla.logger
        self.algorithm = sla.algorithm
        self.operation_dict = sla.operation_dict
        self.window_time = sla.window_time
        self.window_size = sla.window_size

    def run(self):
        pass

    def run_test_euca(self, dc):
        requisitions_list = []
        this_cycle = self.sla.window_time
        arrival_time = 0
        req_size = 0
        max_host_on = 0
        req_size_list = []
        op_dict_temp = self.operation_dict
        while (arrival_time < this_cycle) and (len(op_dict_temp.items()) > 0):
            for op_id, op_vm in op_dict_temp.items():
                arrival_time = op_vm.timestamp
                vm = self._opdict_to_vmlist(op_vm.get_id())
                if arrival_time < this_cycle:  # TODO: or (req_size < window_size):
                    this_state = op_id.split('-')[2]
                    new_host_on, off = dc.each_cycle_get_hosts_on()
                    if new_host_on > max_host_on:
                        max_host_on = new_host_on
                        self.logger.info(
                            "New max host on: " + str(max_host_on) + str(off) + " at " + str(arrival_time) + " sec.")
                    if this_state == "START":
                        if dc.allocate_on_host(vm):
                            requisitions_list.append(vm)
                            req_size += 1
                    elif this_state == "STOP":
                        dc.deallocate_on_host(vm)
                    # Remova do dict temporario
                    del op_dict_temp[op_id]
                else:
                    # Enquanto não há requisições, incremente o relógio
                    while arrival_time >= this_cycle:
                        this_cycle += self.window_time
                    if req_size >= self.window_size:
                        self.logger.info("req_size" + str(req_size))
                    req_size_list.append(req_size)
                    req_size = 0
                    requisitions_list = []
                    break
        #        print "\t\tout: ", arrival_time, thiscycle, len(op_dict_temp.items())
        return dc, max_host_on

    def _opdict_to_vmlist(id, vm_list):
        for vm_temp in vm_list:
            if vm_temp.get_id() == id:
                return vm_temp
        return None