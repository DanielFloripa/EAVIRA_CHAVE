#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import logging
from datetime import datetime
import time

# From package:
from DistributedInfrastructure import *
from Chave import Chave
from Demand import Demand
from Controller import *


# from Controller import *


def main():
    # Global vars:
    demand = Demand(logger, algorithm)
    demand.get_all_sources(list_of_source_files)
    # Get values using 'all_xx_dict['DSn']'
    print len(demand.all_op_dict), len(demand.all_vms_dict), len(demand.all_ha_dict)
    host_list = 0
    az_args = ['asd1', 'asd2']

    az_list = []
    #if len(demand.azs_id) == len():

    for i, azid in enumerate(demand.azs_id):
        az = AvailabilityZone(az_list[azid]['az_nodes'],
                              az_list[azid]['az_cores'],
                              demand.all_ha_dict[azid]['this_az'],
                              azid,
                              (vm_ram_default * az_list[azid]['az_cores']),
                              algorithm, has_overbooking, logger, *az_args)

        if az.create_infrastructure(first_time=True):
            az_list.append(az)
        else:
            logger.error("Problem on create infra for AZ: %s" % (azid))

    # TODO: ver arranjo entre AZs para atribuir nas Regioes
    #best_az_arrange = helper.best_arrange(az2regions, az_list)

    # ______max_az_per_region = 4___________________________________________________________
    # %0 12/4 -> 3R(4)              -> [0:3][4:7][8:11]
    # %1 13/4 -> 2R(4)+1R(3)+1R(2)  -> [0:3][4:7][8:10][11:12]
    # %2 14/4 -> 3R(4)+1R(2)        -> [0:3][4:7][8:11][11:13]
    # %3 15/4 -> 3R(4)+1R(3)        -> [0:3][4:7][8:11][11:14]
    # ______max_az_per_region = 3___________________________________________________________
    # %0 6/3 -> 2R(3)         -> [0:2][3:5]     | 9/3 ->3R(3)       ~>[0:2][3:5][6:8]
    # %1 7/3 -> 1R(3)+2R(2)   -> [0:2][3:4][5:6]| 10/3->2R(3)+2R(2) ~>[0:2][3:5][6:7][8:9]
    # %2 8/3 -> 2R(3)+1R(2)   -> [0:2][3:5][6:7]| 11/3->3R(3)+1R(2) ~>[0:2][3:5][6:8][9:10]
    # ______max_az_per_region = 2___________________________________________________________
    # %0 6/2 -> 2R(3)         -> [0:2][3:5]     | 9/3 ->3R(3)       ~>[0:2][3:5][6:8]
    # %1 7/2 -> 1R(3)+2R(2)   -> [0:2][3:4][5:6]| 10/3->2R(3)+2R(2) ~>[0:2][3:5][6:7][8:9]
    # %0 8/2 -> 3R(3)         -> [0:2][3:5][6:8]| 11/3->3R(3) ~>[0:2][3:5][6:8][9:10]
    modulus_az_region = number_of_azs % max_az_per_region
    regions_list = []
    if modulus_az_region == 0:
        for r in range(number_of_azs / max_az_per_region):
            idx0 = r * max_az_per_region
            idx1 = ((r + 1) * max_az_per_region) - 1
            local_controller = LocalController(az_list[idx0:idx1])
            regions_list.append(local_controller)
            del local_controller

    elif modulus_az_region == 1:
        for r in range(number_of_azs / max_az_per_region) - 1:
            idx0 = r * max_az_per_region
            idx1 = ((r + 1) * max_az_per_region) - 1
            local_controller = LocalController(az_list[idx0:idx1])
            regions_list.append(local_controller)
            del local_controller
        local_controller1 = LocalController(az_list[number_of_azs - 4: number_of_azs - 3])
        regions_list.append(local_controller1)
        local_controller2 = LocalController(az_list[number_of_azs - 2: number_of_azs - 1])
        regions_list.append(local_controller2)

    elif modulus_az_region == 2:
        for r in range(number_of_azs / max_az_per_region):
            idx0 = r * max_az_per_region
            idx1 = ((r + 1) * max_az_per_region) - 1
            local_controller = LocalController(az_list[idx0:idx1])
            regions_list.append(local_controller)
            del local_controller
        local_controller2 = LocalController(az_list[number_of_azs - 2: number_of_azs - 1])
        regions_list.append(local_controller2)

    else:
        logger.error("Relation between 'number_of_azs' and 'max_az_per_region' must be modulus <= 2!")
        exit(1)

    global_controller = GlobalController(algorithm, demand, regions_list, *args)
    global_controller.this_algorithm = algorithm
    global_controller.availability_zones


    start = time.time()
    chave = Chave(pm, ff, trigger_to_migrate, frag_percentual, window_time, window_size, has_overbooking, logger)
    if algorithm == "CHAVE":
        global_controller.run_chave()
    elif algorithm == "EUCA":
        global_controller.run_euca()
    elapsed = time.time() - start

    slav = global_controller.get_total_SLA_violations_from_datacenter()
    energy = global_controller.get_total_energy_consumption()
    overb_list = global_controller.get_list_overb_amount()

    # TODO:
    max_hosts_on = 0

    logger.warning(
        "SLAV:" + str(slav) + ", Energy:" + str(energy) + ", Overbooked:" + str(len(overb_list)) + ", timelapse:" +
        str(elapsed) + ", maxhost:" + str(max_hosts_on))

    with open(data_output, 'aw') as data:
        data.write('%d\t%f\t%d\n' % (slav, energy, len(overb_list)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='CHAVE Simulator')
    parser.add_argument('-nit', dest='nit',     action='store', nargs='+', type=int, required=True,
                        help='Number of iterations: N')
    parser.add_argument('-alg', dest='alg',     action='store', nargs=1, type=str, required=True,
                        help='algorithm type: CHAVE|EUCA')
    parser.add_argument('-pm', dest='pm',       action='store', nargs=1, type=str, required=True,
                        help='placement or migration')
    parser.add_argument('-ff', dest='ff',       action='store', nargs=1, type=str, required=True,
                        help='first fit algorithm')
    parser.add_argument('-in', dest='input',    action='store', nargs='+', type=str, required=True,
                        help='Input file')
    parser.add_argument('-az', dest='az_conf',   action='store', nargs='+', type=str, required=True,
                        help='AZ configuration')
    parser.add_argument('-ha', dest='ha_input',  action='store', nargs='+', required=False,
                        help='High Availability from AZs')
    parser.add_argument('-wt', dest='wt',       action='store', nargs=1, type=int, required=True,
                        help='Window time: N')
    parser.add_argument('-ws', dest='ws',       action='store', nargs=1, type=int, required=True,
                        help='Window size: N')
    parser.add_argument('-ob', dest='overb',    action='store',nargs=1,type=bool, required=True,
                        help='Has Overbooking?')
    args = parser.parse_args()

    list_of_source_files = args.input #  List
    dc_id = []
    az_list = dict()
    for i, source in enumerate(list_of_source_files):
        ns = str(source).rfind("/")
        ne = str(source).rfind("-")
        id = str(source[ns + 1:ne])
        dc_id.append(id)
        az_list[id] = {'source_files':source,
                  'ha_source_files': args.ha_input[i],
                  'az_nodes': int(args.az_conf[i].split(':')[0]),
                  'az_cores': int(args.az_conf[i].split(':')[1]),
                  'az_nits': args.nit[i]}
    number_of_azs = len(list_of_source_files)

    # Values from args
    pm = args.pm
    ff = args.ff
    has_overbooking = args.overb
    algorithm = args.alg
    window_time = args.wt
    window_size = args.ws

    max_az_per_region = int(os.environ["CS_MAX_AZ_REGION"])
    date = datetime.now().strftime(os.environ["CS_DP"])
    core2ram = os.environ.get('CS_CORE2RAM')
    vm_ram_default = int(core2ram.split(':')[1])
#    azRam = vmRam_default * azCores
    data_output = eval(os.environ["CS_DATAOUTPUT"])
    log_output = eval(os.environ["CS_LOGOUTPUT"])

    # Para os logs de mensagens:
    logger = logging.getLogger(__name__)
    hdlr = logging.FileHandler(log_output)
    hdlr.setFormatter(logging.Formatter(os.environ["CS_LOGFORMATTER"]))
    logger.addHandler(hdlr)
    logger.setLevel(int(os.environ.get('CS_LOGLEVEL', logging.DEBUG)))

    trigger_to_migrate = int(os.environ.get('CS_TRIGGER_MIGRATE'))
    frag_percentual = float(os.environ.get('CS_FRAG_PERCENT'))


    main()
