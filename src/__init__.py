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

#import matplotlib.pyplot as plt
import argparse
from datetime import datetime
import os
import csv
import json
from pympler import summary, muppy

# From our packages:
from Algorithms.Chave import *
from Algorithms.MBFD import *
from Algorithms.MM import *
from Algorithms.Eucalyptus import *
from Architecture.Controller import *
from Architecture.Infra import *
from Users.Demand import *
from Users.SLAHelper import *


def test(api):
    """
    Todo a test in in api
    :param api:
    :return:
    """
    print("\n api response: ", api.localcontroller_d['lc0'].get_vm_object_from_az('i-648A423A', 'AZ1'))
    print("\n api_response: ", api.region_d['rg1'].lcontroller.get_vm_object_from_az('i-2BFF3F02', 'AZ4'))
    print("\n api_response: ", api.get_az_from_lc('AZ4'))
    exit(1)


def output_stream(sla):
    """
    Deal with outputs
    :param sla:
    :return:
    """
    types = sla.g_output_type().split(K_SEP)
    logger.info("Saving results in {0}".format(types))
    if "CSV" in types:
        w = csv.writer(open(sla.g_data_output() + ".csv", "w"))
        for key, val in sla.g_metrics_dict().viewitems():
            logger.info("k:{}, v:{}".format(key, val))
            w.writerow([key, val])

    if "JSON" in types:
        json_f = json.dumps(sla.g_metrics_dict(),
                            indent=True,
                            sort_keys=False)
        f = open(sla.g_data_output() + ".json", "w")
        f.write(json_f)
        f.close()

    if "SQLITE" in types:
        print("Not yet implemented")

    if "TEXT" in types:
        print("Not yet implemented")
        with open(sla.g_log_output() + ".mem", "w") as fp:
            for az, metric in sla.metrics_dict().items():
                fp.write(az)
                for m, v in metric.items():
                    fp.write(m)
                    if type(v) is not list:
                        fp.write(v)
                    else:
                        for e in v:
                            fp.write(e)

    if "MEM" in types:
        with open(sla.g_log_output() + ".mem", "w") as fp:
            all_objects = muppy.get_objects()
            sum1 = summary.summarize(all_objects)
            # summary.print_(sum1)
            for line in summary.format_(sum1):
                fp.write("{0}\n".format(line))
        #fp.close()
    logger.info("Saved in {0}".format(sla.g_log_output()))

'''
def plot_all():
    for k, v in sla.g_metrics_dict().items():
        ene_l = v.get('energy_avg_l')
        x = list(k)  # list() needed for python 3.x
        y = list(ene_l)  # ditto
        if len(x) > 0 and len(y):
            plt.plot(x, y, '-')
            plt.show()
'''

def print_all():
    """
    Just for print :)
    :return:
    """
    for k, v in sla.g_metrics_dict().items():
        print("\n{}: ".format(k))
        for kv, vv in v.items():
            print("\t{}: {}".format(kv, vv))


def main():
    """
    main() decribes all architecture and define the main objects
    :return: None
    """

    demand = Demand(sla)
    demand.create_vms_from_sources()

    az_list, demand_list = [], []
    for i, azid in enumerate(demand.az_id):
        vm_d, op_d, ha_d = demand.get_demand_from_az(azid)
        az = AvailabilityZone(sla, azid, vm_d, op_d, ha_d)
        if az.create_infra(first_time=True, host_state=HOST_OFF):
            az_list.append(az)
            logger.debug("HA Initial {0}: {1}".format(azid, ha_d['this_az']))
        else:
            logger.error("Problem on create infra for AZ#{0}: {1}".format(i, azid))

    lcontroller_d, region_d = dict(), dict()
    lcontroller_d["lc0"] = LocalController(sla, "lc0", az_list[0:3])
    lcontroller_d["lc1"] = LocalController(sla, "lc1", az_list[3:6])

    """Region is useless here, but is useful for a more complex architectures"""
    region_d['rg0'] = Region(sla, "rg0", lcontroller_d['lc0'])
    region_d['rg1'] = Region(sla, "rg1", lcontroller_d['lc1'])

    api = GlobalController(sla, demand, lcontroller_d, region_d)

    ''' Lets test the api? '''
    if sla.g_algorithm() == "TEST":
        test(api)

    # ################### Begin the algorithms ###############
    start = time.time()
    if sla.g_algorithm() == "CHAVE":
        chave = Chave(api)
        chave.run()
    elif sla.g_algorithm() == "EUCA":
        euca = Eucalyptus(api)
        euca.run()
    elif sla.g_algorithm() == "MM":
        mm = MM(api)
        mm.run()
    elif sla.g_algorithm() == "MBFD":
        mbfd = MBFD(api)
        mbfd.run()
    elapsed = time.time() - start
    # ################### End the algorithms ###############

    total_energy = 0
    for az_id in sla.g_az_id_list():
        total_energy += sla.metrics(az_id, 'get', 'total_energy_f')
    sla.metrics('global', 'set', 'total_energy_f', total_energy)
    sla.metrics('global', 'set', 'sla_violations_i', api.get_total_SLA_violations_from_cloud())
    sla.metrics('global', 'set', 'overcommitting_i', api.get_list_overcom_amount_from_cloud())
    sla.metrics('global', 'set', 'elapsed_time_i', elapsed)

    output_stream(sla)
    #plot_all()



if __name__ == '__main__':
    '''
    Get the parameters from args and from Linux environment, 
    create the SLAHelper Object and put them all into object.
    This part we can't need change
    '''
    parser = argparse.ArgumentParser(description='CHAVE Simulator')
    parser.add_argument('-nit', dest='nit', action='store', nargs='+', required=True,
                        help='Number of iterations: N')
    parser.add_argument('-alg', dest='alg', action='store', nargs=1, type=str, required=True,
                        help='algorithm type: CHAVE | EUCA')
    parser.add_argument('-pm', dest='pm', action='store', nargs=1, type=str, required=True,
                        help='placement or migration order')
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
    parser.add_argument('-ovc', dest='overcom', action='store', nargs=1, type=str, required=True,
                        help='Has Overcommitting?')  # overprovisioning
    parser.add_argument('-cons', dest='consolidate', action='store', nargs=1, type=str, required=True,
                        help='Has consolidate?')
    args = parser.parse_args()

    """This 'sla' instance will memoize all specifications and parameters from args and .conf file"""
    sla = SLAHelper()

    """Values from python args"""
    sla.list_of_source_files(args.input)
    s = len(args.input)
    if s == len(args.ha_input) == len(args.az_conf) == len(args.nit):
        sla.number_of_azs(s)
    sla.ha_input(args.ha_input)
    sla.az_conf(sla.set_conf(args.az_conf, 'az_conf'))
    sla.nit(sla.set_conf(args.nit, 'nit'))
    sla.pm(args.pm[0])
    sla.ff(args.ff[0])
    sla.has_overcommitting(eval(args.overcom[0]))
    sla.has_consolidation(eval(args.consolidate[0]))
    sla.algorithm(args.alg[0])
    sla.window_time(args.wt[0])
    sla.window_size(args.ws[0])
    """From Linux environment variables"""
    sla.max_az_per_region(int(os.environ["CS_MAX_AZ_REGION"]))
    sla.date(str(datetime.now().strftime(os.environ.get("CS_DP"))))
    sla.core_2_ram_default(int(os.environ.get('CS_CORE2RAM')))
    sla.data_output(str(eval(os.environ["CS_DATA_OUTPUT"])))
    sla.log_output(str(eval(os.environ["CS_LOG_OUTPUT"])))
    #user = str(os.environ["USER"])
    # Todo: desfazer essa gambi no final
    #if user == "debian":
        #os.symlink(sla.g_log_output(), "../logs" + sla.g_log_output() + "_link.log")
    sla.output_type(str(os.environ["CS_OUTPUT_TYPE"]))
    sla.trace_class(str(os.environ["CS_TRACE_CLASS"]))
    sla.enable_emon(eval(os.environ["CS_ENABLE_EMON"]))
    sla.az_selection(str(os.environ["CS_AZ_SELECTION"]))
    sla.trigger_to_migrate(int(os.environ.get('CS_TRIGGER_MIGRATE')))
    sla.frag_class(str(os.environ.get('CS_FRAGMENTATION_CLASS')))
    """Configurations for logger objects:"""
    logger = logging.getLogger(__name__)
    hdlr = logging.FileHandler(sla.g_log_output())
    hdlr.setFormatter(logging.Formatter(os.environ.get("CS_LOG_FORMATTER")))
    logger.addHandler(hdlr)
    logger.setLevel(int(os.environ.get('CS_LOG_LEVEL')))  # , logging.DEBUG)))
    sla.logger(logger)
    sla.define_az_id(str(os.environ.get("CS_DEFINE_AZID")))  # "file" or "auto"
    sla.init_metrics(is_print=False)

    """From now, we can't change this SLA parameters"""
    sla.set_sla_lock(True)
    sla.debug_sla()
    main()
