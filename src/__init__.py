#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CHAVE-Sim: The simulator for research based in clouds architecture
    CHAVE: Consolidation with High Availability on virtualyzed environments
"""

__author__ = "Daniel Camargo and Denivy Ruck"
__license__ = "GPL-v3"
__version__ = "2.0.1"
__maintainer__ = "Daniel Camargo"
__email__ = "daniel@colmeia.udesc.br"
__status__ = "Test"

import argparse
import logging
import time
from datetime import datetime
import csv
import json
from pympler import summary, tracker, muppy

# From packages:
from Chave import *
from Controller import *
from DistInfra import *
from Demand import *
from Eucalyptus import *
from SLAHelper import *


def main():
    # Setting objects demand, az, lc, region, gc
    sla.init_metrics(is_print=False)
    demand = Demand(sla)
    demand.create_vms_from_sources()
    # Get specific values using dict: 'all_xx_dict['DSn']'
    # print len(demand.all_operations_dicts), len(demand.all_vms_dict), len(demand.all_ha_dict)

    az_list, demand_list = [], []
    for i, azid in enumerate(demand.az_id):
        vm_d, op_d, ha_d = demand.get_demand_from_az(azid)
        az = AvailabilityZone(sla, azid, vm_d, op_d, ha_d)
        if az.create_infrastructure(first_time=True, is_on=True):
            az_list.append(az)
        else:
            logger.error("Problem on create infra for AZ#%s: %s" % (i, azid))

    lcontroller_d, region_d = dict(), dict()
    lcontroller_d["lc0"] = LocalController(sla, "lc0", az_list[0:3])
    lcontroller_d["lc1"] = LocalController(sla, "lc1", az_list[3:6])

    # Regiao é dispensável aqui, mas útil para suportar arquiteturas mais complexas
    region_d['rg0'] = Region(sla, "rg0", lcontroller_d['lc0'])
    region_d['rg1'] = Region(sla, "rg1", lcontroller_d['lc1'])

    api = GlobalController(sla, demand, lcontroller_d, region_d)

    ''' Lets test the api: '''
    # print "api response: ", api.localcontroller_d['lc0'].get_vm_object_from_az('i-ABC443B3', 'DS1')
    # print "api_response", api.region_d['rg1'].lcontroller.get_vm_object_from_az('i-2BFF3F02', 'DS4')
    # print "api_response", api.get_az_from_lc('DS4')
    # exit(1)
    # ################### Begin the algorithms ###############
    start = time.time()
    if sla.g_algorithm() == "CHAVE":
        chave = Chave(api)
        chave.run()
    elif sla.g_algorithm() == "EUCA":
        euca = Eucalyptus(api)
        euca.run()
    elif sla.g_algorithm() == "MM":
        mm = 1
        api.run(mm)
    elif sla.algorithm() == "MBFD":
        mbfd = 1
        api.run(mbfd)
    elapsed = time.time() - start
    # ################### End the algorithms ###############

    slav = api.get_total_SLA_violations_from_cloud()
    energy = api.get_total_energy_consumption_from_cloud()
    overb_list = api.get_list_overb_amount_from_cloud()

    if sla.g_output_type() == "CSV":
        w = csv.writer(open(sla.g_data_output()+".csv", "w"))
        for key, val in sla.g_metrics_dict().viewitems():
            logger.info(key, val)
            w.writerow([key, val])
    elif sla.g_output_type() == "JSON":
        json_f = json.dumps(sla.g_metrics_dict(), indent=True, sort_keys=False)
        f = open(sla.g_data_output()+".json", "w")
        f.write(json_f)
        f.close()

    '''all_objects = muppy.get_objects()
    sum1 = summary.summarize(all_objects)
    summary.print_(sum1)'''

    exit(0)



if __name__ == '__main__':
    '''
    Lets get the parameters from args and from Linux environment, 
    create the SLAHelper Object and put them all into object.
    This part we can't need change
    '''
    parser = argparse.ArgumentParser(description='CHAVE Simulator')
    parser.add_argument('-nit', dest='nit', action='store', nargs='+', required=True,
                        help='Number of iterations: N')
    parser.add_argument('-alg', dest='alg', action='store', nargs=1, type=str, required=True,
                        help='algorithm type: CHAVE | EUCA')
    parser.add_argument('-pm', dest='pm', action='store', nargs=1, type=str, required=True,
                        help='placement or migration')
    parser.add_argument('-ff', dest='ff', action='store', nargs=1, type=str, required=True,
                        help='first fit algorithm')
    parser.add_argument('-in', dest='input', action='store', nargs='+', required=True,
                        help='Input file')
    parser.add_argument('-az', dest='az_conf', action='store', nargs='+', required=True,
                        help='AZ configuration')
    parser.add_argument('-ha', dest='ha_input', action='store', nargs='+', required=False,
                        help='High Availability from AZs')
    parser.add_argument('-wt', dest='wt', action='store', nargs=1, type=int, required=True,
                        help='Window time: N')
    parser.add_argument('-ws', dest='ws', action='store', nargs=1, type=int, required=True,
                        help='Window size: N')
    parser.add_argument('-ob', dest='overb', action='store', nargs=1, type=str, required=True,
                        help='Has Overbooking?')  # overprovisioning
    args = parser.parse_args()

    ''' This 'sla' instance will reserve all specifications and parameters'''
    sla = SLAHelper()

    sla.list_of_source_files(args.input)
    s = len(args.input)
    if s == len(args.ha_input) == len(args.az_conf) == len(args.nit):
        sla.number_of_azs(s)
    sla.ha_input(args.ha_input)
    sla.az_conf(sla.set_conf(args.az_conf, 'az_conf'))
    sla.nit(sla.set_conf(args.nit, 'nit'))

    # Values from python args
    sla.pm(args.pm[0])
    sla.ff(args.ff[0])
    sla.has_overbooking(eval(args.overb[0]))
    sla.algorithm(args.alg[0])
    sla.window_time(args.wt[0])
    sla.window_size(args.ws[0])
    # Linux Environment vars
    sla.max_az_per_region(int(os.environ["CS_MAX_AZ_REGION"]))
    sla.date(str(datetime.now().strftime(os.environ.get("CS_DP"))))
    sla.core_2_ram_default(int(os.environ.get('CS_CORE2RAM')))
    sla.data_output(str(eval(os.environ["CS_DATA_OUTPUT"])))
    sla.log_output(str(eval(os.environ["CS_LOG_OUTPUT"])))
    sla.output_type(str(os.environ["CS_OUTPUT_TYPE"]))
    sla.trigger_to_migrate(int(os.environ.get('CS_TRIGGER_MIGRATE')))
    sla.frag_percentual(float(os.environ.get('CS_FRAG_PERCENT')))
    # Para os logs de mensagens:
    logger = logging.getLogger(__name__)
    hdlr = logging.FileHandler(sla.g_log_output())
    hdlr.setFormatter(logging.Formatter(os.environ.get("CS_LOG_FORMATTER")))
    logger.addHandler(hdlr)
    # se primeiro parametro der erro, use o segundo:
    logger.setLevel(int(os.environ.get('CS_LOG_LEVEL', logging.DEBUG)))
    sla.logger(logger)
    sla.define_az_id(str(os.environ.get("CS_DEFINE_AZID")))  # "file" or "auto"
    # From now, we can't change the SLA parameters
    sla.set_sla_lock(True)

    main()
