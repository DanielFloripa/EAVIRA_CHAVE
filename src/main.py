#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import logging
from datetime import datetime
import time
from DistributedInfrastructure import *
from Chave import Chave
from Helper import Helper
from Controller import *


# from Controller import *


def main():
    global_controller = GlobalController
    start = time.time()
    chave = Chave(pm, ff, trigger_to_migrate, frag_percentual, window_time, window_size, has_overbooking, logger)
    if algorithm == "CHAVE":
        new_dc, maxhost = chave.run_test_chave(dc)
    elif algorithm == "EUCA":
        new_dc, maxhost = run_test_euca(dc, h)
    elapsed = time.time() - start

    slav = new_dc.get_total_SLA_violations_from_datacenter()
    energy = new_dc.get_total_energy_consumption()
    overb_list = new_dc.get_list_overb_amount()
    # TODO:
    max_hosts_on = 0

    logger.warning(
        "SLAV:" + str(slav) + ", Energy:" + str(energy) + ", Overbooked:" + str(len(overb_list)) + ", timelapse:" + str(
            elapsed) + ", maxhost:" + str(maxhost))

    with open(data_output, 'aw') as data:
        data.write('%d\t%f\t%d\n' % (slav, energy, len(overb_list)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='CHAVE Simulator')
    parser.add_argument('-nit', dest='nit', action='store', nargs=1, help='Number of iterations: N', required=True)
    parser.add_argument('-alg', dest='algorithm', action='store', nargs=1, help='algorithm type: CHAVE|EUCA',
                        required=True)
    parser.add_argument('-pm', dest='pm', action='store', nargs=1, help='placement or migration', required=True)
    parser.add_argument('-ff', dest='ff', action='store', nargs=1, help='first fit algorithm', required=True)
    parser.add_argument('-in', dest='input', action='store', nargs=1, help='Input file', required=True)
    parser.add_argument('-az', dest='azConf', action='store', nargs='+', help='AZ configuration', required=True)
    parser.add_argument('-av', dest='availab', action='store', nargs=1, help='Availability from AZ', required=True)
    parser.add_argument('-wt', dest='wt', action='store', nargs=1, type=int, help='Window time: N', required=True)
    parser.add_argument('-ws', dest='ws', action='store', nargs=1, type=int, help='Window size: N', required=True)
    parser.add_argument('-ovb', dest='overb', action='store', nargs=1, type=bool, help='Has Overbooking?',
                        required=True)

    args = parser.parse_args()
    print args
    nit = int(args.nit[0])
    pm = args.pm[0]
    ff = args.ff[0]
    has_overbooking = args.overb[0]
    algorithm = str(args.algorithm[0])
    window_time = int(args.wt[0])
    window_size = int(args.ws[0])
    date = datetime.now().strftime(os.environ["CS_DP"])
    availability = float(args.availab[0])
    source_file = args.input[0]
    ns = str(source_file).rfind("/")
    ne = str(source_file).rfind("-")
    dcid = str(source_file[ns + 1:ne])
    azNodes = int(args.azConf[0].split(':')[0])
    azCores = int(args.azConf[0].split(':')[1])
    core2ram = os.environ.get('CS_CORE2RAM')
    vmRam_default = int(core2ram.split(':')[0])
    azRam = vmRam_default * azCores

    data_output = eval(os.environ["CS_DATAOUTPUT"])
    log_output = eval(os.environ["CS_LOGOUTPUT"])

    # Para os logs de mensagens:
    logger = logging.getLogger(__name__)
    hdlr = logging.FileHandler(log_output)
    hdlr.setFormatter(logging.Formatter(os.environ["CS_LOGFORMATTER"]))
    logger.addHandler(hdlr)
    # Especifique o nível de log para saida:
    logger.setLevel(int(os.environ.get('CS_LOGLEVEL', logging.DEBUG)))

    # Global vars:
    dc = AvailabilityZone(azNodes, azCores, availability, dcid, azRam, algorithm, has_overbooking, logger)
    host_list = dc.create_infrastructure()
    dc.set_host_list(host_list)

    h = Helper(dc, logger, algorithm)
    vm_list, operation_dict = h.get_vms_from_source(source_file)
    # metrics_dict = {}

    trigger_to_migrate = 3600
    frag_percentual = float(0.3)

    main()
