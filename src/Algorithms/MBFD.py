#!/usr/bin/python
# -*- coding: utf-8 -*-

import threading
from Users.SLAHelper import *


class MBFD(object):
    def __init__(self, api):
        self.api = api
        self.sla = api.sla
        self.logger = api.sla.g_logger()
        self.nit = api.sla.g_nit()
        self.trigger_to_migrate = api.sla.g_trigger_to_migrate()
        self.frag_percent = api.sla.g_frag_percentual()
        self.pm_mode = api.sla.g_pm()
        self.ff_mode = api.sla.g_ff()
        self.window_time = api.sla.g_window_time()
        self.window_size = api.sla.g_window_size()
        self.has_overcommitting = api.sla.g_has_overcommitting()
        self.localcontroller_list = []
        self.region_list = None
        self.all_vms_dict = dict()
        self.all_op_dict = dict()
        self.all_ha_dict = dict()
        self.thread_dict = dict()
        self.replicas_dict = OrderedDict()
        self.az_list = []
        self.global_hour = -1
        self.global_time = -1

    def __repr__(self):
        return repr([self.__get])

    def gvt(self, max):
        self.logger.info("Init GVT in {0} to {1}".format
                         (self.global_time, self.api.demand.max_timestamp))
        while self.global_time < self.api.demand.max_timestamp + 1 and not self.exceptions:
            self.global_time += self.window_time
            if self.global_time % 60 == 0:
                time.sleep(0.1)
            if self.global_time % 3600 == 0:
                self.global_hour += 1
                self.logger.debug("GVT s:%s, h:%s" % (self.global_time, self.global_hour))
                # Todo: try syncronize all threads
                time.sleep(1)
        self.logger.info("End of GVT!")

    def run(self):
        '''
        Interface for all algorithms, the name must be agnostic for all them
        In this version, we use Threads for running infrastructures in parallel
        :return: Void
        '''
        semaph = threading.Semaphore(1)
        self.thread_dict['gvt'] = threading.Thread(
            name="T_gvt",
            target=self.gvt,
            args=[0])
        # Creating Thread list
        for az in self.api.get_az_list():
            self.replicas_execution_d[az.az_id] = dict()
            self.thread_dict[str(az.az_id)] = threading.Thread(
                name="T_" + str(az.az_id),
                target=self.alg1,
                args=[az, semaph])

        for lc_id, lc_obj in self.api.get_localcontroller_d().items():
            self.thread_dict[str(lc_id)] = threading.Thread(
                name="T_" + str(lc_id),
                target=self.alg2,
                args=[lc_obj, semaph])
        # Release Threads
        for t_id, t_obj in self.thread_dict.items():
            self.logger.debug("Executing thread for: {0}".format(
                t_obj.getName()))
            t_obj.start()
            t_obj.join(2)


    def alg1(self, az, semaph):
        while self.global_time < self.api.demand.max_timestamp:
            pass
        self.logger.info("Exit")


    def alg2(self, lc_obj, semaph):
        while self.global_time <= self.api.demand.max_timestamp: # or not self.exceptions:
            pass
        self.logger.info("Exit")
