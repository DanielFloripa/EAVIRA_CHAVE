#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import matplotlib.pyplot as plt
import csv
import json
import argparse

# From our packages:
from Algorithms.Chave import *
from Algorithms.Eucalyptus import *
from Algorithms.MBFD import *
from Algorithms.MM import *
from Architecture.Controller import *
from Architecture.Infra import *
from Users.Demand import *
from Users.SLAHelper import *

__description__ = "CHAVE-Sim: Consolidation with High Availability on Virtualyzed Environments Simulator" \
                  "Must be is used only for research based in clouds architecture"
__author__ = "Daniel Camargo based on EAVIRA (Denivy Ruck)"
__license__ = "GPL-v3"
__version__ = "3.0.0"
__maintainer__ = "Daniel Camargo"
__organization__ = "LabP2D - UDESC"
__email__ = "daniel@colmeia.udesc.br"
__status__ = "Under developement"
doc = [__description__, __author__, __license__, __version__, __maintainer__, __organization__, __email__, __status__]


def parse_arguments_to_sla():
    """
        Get the parameters from args and from Linux environment,
        create the SLAHelper Object and put them all into object.
        This part we can't need change
    """
    parser = argparse.ArgumentParser(description='CHAVE Simulator')
    parser.add_argument('-nit', dest='nit', action='store', nargs='+', required=True,
                        help='Number of iterations: N')
    parser.add_argument('-alg', dest='alg', action='store', nargs=1, type=str, required=True,
                        help='algorithm type: CHAVE | EUCA | ...')
    parser.add_argument('-in', dest='input', action='store', nargs='+', required=True,
                        help='Input file')
    parser.add_argument('-az', dest='az_conf', action='store', nargs='+', required=True,
                        help='AZ configuration')
    parser.add_argument('-wt', dest='wt', action='store', nargs=1, type=int, required=True,
                        help='Window time: N')
    parser.add_argument('-ca', dest='ca', action='store', nargs=1, type=str, required=False,
                        help='Consolidation Algorithm')
    parser.add_argument('-ff', dest='ff', action='store', nargs=1, type=str, required=False,
                        help='first fit algorithm')
    parser.add_argument('-ha', dest='ha_input', action='store', nargs='+', required=False,
                        help='High Availability from AZs')
    parser.add_argument('-lock', dest='lock', action='store', nargs=1, type=str, required=False,
                        help='VM Lock test. Values: <True|False|Random>')
    parser.add_argument('-ovc', dest='overcom', action='store', nargs=1, type=str, required=False,
                        help='Has Overcommitting?')  # overprovisioning
    parser.add_argument('-cons', dest='consol', action='store', nargs=1, type=str, required=False,
                        help='Has consolidate?')
    parser.add_argument('-repl', dest='repl', action='store', nargs=1, type=str, required=False,
                        help='Enable replication? Values: <False | True>')
    args = parser.parse_args()

    """Values from python args"""
    sla.list_of_source_files(args.input)
    s = len(args.input)
    if s == len(args.ha_input) == len(args.az_conf) == len(args.nit):
        sla.number_of_azs(s)
    sla.ha_input(args.ha_input)
    sla.az_conf(sla.set_conf(args.az_conf, 'az_conf'))
    sla.nit(sla.set_conf(args.nit, 'nit'))
    sla.window_time(args.wt[0])
    sla.date(os.environ.get("CS_START"))
    # Note: If add new parameter, this gambiarra must be reviewed
    if args.alg[0] == "EUCA" and not (args.consol[0] == "False" and args.ca[0] == "MAX" and args.lock[0] == "None" and args.overcom[0] == "False" and args.repl[0] == "False"):
        exit(1)
    if (args.consol[0] == "False" and args.ca[0] == "LOCK") or \
            (args.consol[0] == "False" and args.ca[0] == "MAX" and args.lock[0] == "True") or \
            (args.consol[0] == "False" and args.ca[0] == "MAX" and args.lock[0] == "False") or \
            (args.consol[0] == "False" and args.ca[0] == "MAX" and args.lock[0] == "RANDOM") or \
            (args.consol[0] == "True" and args.ca[0] == "MAX" and args.lock[0] == "False") or \
            (args.consol[0] == "True" and args.ca[0] == "MAX" and args.lock[0] == "True") or \
            (args.consol[0] == "True" and args.ca[0] == "MAX" and args.lock[0] == "RANDOM") or \
            (args.consol[0] == "True" and args.ca[0] == "LOCK" and args.lock[0] == "None"):
            exit(1)
    if args.consol[0] == "False":
        args.ca[0] = "CF"
    sla.consolidation_alg(str(args.ca[0]))
    sla.has_consolidation(eval(args.consol[0]))
    sla.ff(args.ff[0])
    sla.has_overcommitting(eval(args.overcom[0]))
    sla.enable_replication(eval(args.repl[0]))
    sla.lock_case(str(args.lock[0]))
    # The algoritm() must be the last of `args` call, because the 'TEST' mode
    sla.algorithm(args.alg[0])
    sla.log_output(str(eval(os.environ["CS_LOG_OUTPUT"])))
    sla.data_output(str(eval(os.environ["CS_DATA_OUTPUT"])))
    sla.default_file_output(str(eval("\"" + os.environ["CS_DEF_TEST_NAME"])))
    """Configurations for logger objects:"""
    logger = logging.getLogger(__name__)
    hdlr = logging.FileHandler(sla.g_log_output())
    hdlr.setFormatter(logging.Formatter(os.environ.get("CS_LOG_FORMATTER")))
    logger.addHandler(hdlr)
    logger.setLevel(int(os.environ.get('CS_LOG_LEVEL')))  # , logging.DEBUG)))
    sla.set_logger(logger)
    """Values from Linux environment variables"""
    # Note: deprecated
    # sla.avg_load_objective(str(os.environ["CS_AVG_LOAD_OBJECTIVE"]))
    sla.max_az_per_region(int(os.environ["CS_MAX_AZ_REGION"]))
    sla.source_folder(str(os.environ.get("CS_SOURCE_FOLDER")))
    sla.core_2_ram_default(int(os.environ.get('CS_CORE2RAM')))
    sla.output_type(str(os.environ["CS_OUTPUT_TYPE"]), str(os.environ["CS_OUTPUT_SEPARATOR"]))
    sla.trace_class(str(os.environ["CS_TRACE_CLASS"]))
    sla.enable_emon(eval(os.environ["CS_ENABLE_EMON"]))
    sla.az_selection(str(os.environ["CS_AZ_SELECTION"]))
    sla.trigger_to_migrate(int(os.environ.get('CS_TRIGGER_MIGRATE')))
    sla.frag_class(str(os.environ.get('CS_FRAGMENTATION_CLASS')))
    sla.vcpu_per_core(float(os.environ.get('CS_VCPUS_PER_CORE')))
    sla.define_az_id(str(os.environ.get("CS_DEFINE_AZID")))
    sla.energy_model_src(str(os.environ.get("CS_ENERGY_MODEL")))
    sla.milestones(int(os.environ.get("CS_MILESTONES")))
    # sla.doc(doc)
    """From now, we can't change this SLA parameters"""
    sla.init_metrics()
    sla.set_sla_lock(True)
    sla.debug_sla()


def test(this_api):
    """
    Todo a test in api
    """
    print("1) api response: ", this_api.localcontroller_d['lc0'].get_vm_object_from_az('i-5521424F', 'DS1'))
    print("2) api_response: ", this_api.region_d['rg1'].lcontroller.get_vm_object_from_az('i-1D5646FD', 'DS4'))
    print("3) api_response: ", this_api.get_az_from_lc('DS4'))
    print("Basic tests is done!")


def output_stream():
    """
    Deal with outputs
    """
    types_list, sep = sla.g_output_type()
    sla.logger.info("Saving results in {0}".format(types_list))
    if "CSV" in types_list:
        # Todo: ver para modificar o parametro 'separator'
        w = csv.writer(open(sla.g_data_output() + ".csv", "w"))
        for key, val in sla.g_metrics_dict().viewitems():
            # logger.info("k:{}, v:{}".format(key, val))
            w.writerow([key, val])
    if "JSON" in types_list:
        with open(sla.g_data_output() + ".json", "w") as fp:
            json.dump(sla.g_metrics_dict(), fp, indent=sep)
    if "SQLITE" in types_list:
        sla.logger.error("Not yet implemented")
    if "TEXT" in types_list:
        with open(sla.g_data_output() + ".txt", "w") as fp:
            for az, metric in sla.g_metrics_dict().items():
                fp.write(az + ':\n')
                for km, vm in metric.items():
                    fp.write('\t' + km + ': ')
                    if type(vm) is not list:
                        fp.write(str(vm) + '\n')
                    else:
                        fp.write('List(len(' + str(len(vm)) + ')\n')
    if "MEM" in types_list:
        pass
    #    get = sla.g_log_output().rsplit(sep='/', maxsplit=1)
    #    mem_out = get[0] + '/mem/' + get[1].rsplit(sep='.txt')[0] + '.mem'
    #    os.makedirs(os.path.dirname(mem_out), exist_ok=True)
    #    with open(mem_out, "w", ) as fp:
    #        all_objects = muppy.get_objects()
    #        sum1 = summary.summarize(all_objects)
    #        for line in summary.format_(sum1):
    #            fp.write("{}\n".format(line))
    sla.logger.info("Saved in {}".format(sla.g_log_output()))


def print_all():
    """
    Just for print :)
    :return: None
    """
    for k, v in sla.g_metrics_dict().items():
        print("\n{}: ".format(k))
        for kv, vv in v.items():
            print("\t{}: {}".format(kv, vv))


if __name__ == '__main__':
    """
    __main__ decribes all architecture and define the main objects
    :return: None
    """

    """This 'sla' instance will memoize all specifications and parameters from args and .conf file"""
    sla = SLAHelper()
    parse_arguments_to_sla()
    demand = Demand(sla)
    demand.create_vms_from_sources()

    if sla.g_algorithm() == "CHAVE":
        state = HOST_OFF
    else:
        state = HOST_ON
    az_list = []
    for i, azid in enumerate(demand.az_id):
        vm_d, op_d, ha_d = demand.get_demand_from_az(azid)
        az = AvailabilityZone(sla, azid, vm_d, op_d, ha_d)
        if az.create_infra(first_time=True, host_state=state):
            az_list.append(az)
            sla.logger.debug("HA Initial {}: {}".format(azid, ha_d['this_az']))
        else:
            sla.logger.error("Problem on create infra for AZ#{}: {}".format(i, azid))

    lcontroller_d, region_d = dict(), dict()
    r_max = sla.g_max_az_per_region()

    for r in range(int(len(az_list) / r_max)):  # 6/3=2
        lc_id = 'lc' + str(r)
        r_id = 'rg' + str(r)
        lcontroller_d[lc_id] = LocalController(sla, lc_id, az_list[r * r_max: (r + 1) * r_max])
        """Region is useless here, but can be useful for a more complex architectures"""
        region_d[r_id] = Region(sla, r_id, lcontroller_d[lc_id])

    api = GlobalController(sla, demand, lcontroller_d, region_d)

    # ################### Begin algorithms ###############
    start = time.time()
    if sla.g_algorithm().rsplit(sep="_")[0] == "CHAVE":
        chave = Chave(api)
        chave.run()
    elif sla.g_algorithm().rsplit(sep="_")[0] == "EUCA":
        euca = Eucalyptus(api)
        euca.run()
    elif sla.g_algorithm().rsplit(sep="_")[0] == "MM":
        mm = MM(api)
        mm.run()
    elif sla.g_algorithm().rsplit(sep="_")[0] == "MBFD":
        mbfd = MBFD(api)
        mbfd.run()
    elif sla.g_algorithm().rsplit(sep="_")[0] == "TEST":
        test(api)
        if sla.g_algorithm().rsplit(sep="_")[1] == "CHAVE":
            chave = Chave(api)
            chave.run()
        if sla.g_algorithm().rsplit(sep="_")[1] == "EUCA":
            euca = Eucalyptus(api)
            euca.run()
        # Todo: after we finish this new algorithms, add to test mode
        #mm = MM(api)
        #mm.run()
        #mbfd = MBFD(api)
        #mbfd.run()
    elapsed = time.time() - start
    # ################### End of algorithms ###############

    # sla.metrics.resume_global(elapsed)
    # output_stream()
    sla.logger.critical("This simulation take {} seconds".format(elapsed))
    sla.metrics.close_all_dbs()
    exit(0)
