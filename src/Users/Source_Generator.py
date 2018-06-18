# GVT = Global Virtual Time


import statistics
from collections import OrderedDict
import numpy as np
import math
import sys
import os
import argparse
import collections

# TODO: perm = permutations([1, 2, 3])
# for i in list(perm): print i

def create_profile(nit, dist, source_file):
    vi_id = 0
    op_log = {}
    vi_list = []

    if dist == 'poisson':
        op_allocations = np.random.poisson(nit / 2, nit).tolist()
    elif dist == 'uniform':
        op_allocations = np.random.random_integers(0, nit, nit / 3).tolist()
    else:
        print("Invalid dist %s" % (dist))
        sys.exit(1)
    lifespan = int(np.random.randint(5, 10))
    return op_log, vi_list

def test_consistency(source_file):
    for_check = []
    consistent_dictionary = OrderedDict()
    consistent_list = []
    with open(source_file, 'r') as source:
        for operation in source:
            operation = operation.split()
            state = operation[0]
            timestamp = int(operation[1])
            vm_id = str(operation[2])
            if state == "START":
                host = str(operation[3])
                vcpu = str(operation[4])
                for_check.append(vm_id)
                consistent_list = [state, timestamp, vm_id, host, vcpu]
                can_save = True
            else:
                if consistent_dictionary.get(vm_id + "_START") is not None:
                    consistent_list = [state, timestamp, vm_id]
                    can_save = True
                else:
                    consistent_dictionary.pop(vm_id + "_START")
                    print("Problem in ", vm_id, source_file)
                    can_save = False
                try:
                    vmindex = for_check.index(vm_id)
                    for_check.pop(vmindex)
                except ValueError:
                    print("Problem in ", vm_id, source_file)
                    can_save = False
                    break
            if can_save:
                consistent_dictionary[vm_id+"_"+state] = consistent_list
    # source.close()
    if for_check:
        print("Some problem on consistency", len(for_check), source_file)
        os.remove(source_file)
        #os.rename(source_file, source_file+"_ERROR")
        out = open(source_file, "w")
        for d_id, d_list in consistent_dictionary.items():
            if for_check.count(d_id.split('_')[0]) == 0:
                line = ''
                for i in range(len(d_list)):
                    line += str(d_list[i])+" "
                line += '\n'
                out.writelines(line)
        out.close()

def statistic(_list):
    mode, mean, median, stdev, varc = None, None, None, None, None
    try:
        mode = statistics.mode(_list)
    except ValueError:
        pass
    try:
        mean = statistics.mean(_list)
        median = statistics.median(_list)
        stdev = statistics.stdev(_list)
        varc = statistics.variance(_list)
    except TypeError:
        pass
    stat = {'max': max(_list),
            'min': min(_list),
            'mean': mean,
            'median': median,
            'stdev': stdev,
            'mode': mode,
            'variance': varc}
    return stat


def export_info(data_dict, once, total):
    export_info_d = dict()
    for did, data in data_dict.items():
        stat = statistic(data)
        export_info_d[did] = stat

    out = source_file.split(".txt")[0] + '-info.txt'
    with open(out, 'w') as f:

        for key, values in export_info_d.items():
            f.write("\n{}:\n".format(key))
            for k, stat in values.items():
                line = "\t{}: {}\n".format(k, stat)
                f.write(line)
        f.write("\nFrequency:\n")
        for e in once:
            for k, v in e.items():
                f.write("\n\t{}:\n\t\t{}, \t({:.3f}%)\n".format(k, v, 100*(v/float(total))))


def create_additional_info_requisitions():
    n = 0
    vm_d_ts = dict()
    ts_start, ts_stop, lifespam, cpu_size, host_usage, av_m, lock_m = [], [], [], [], [], [], []
    avail_az = set_av_for_az(0.999, 0.9999)
    out_file = source_file.split(".txt")[0] + "-plus.txt"
    out = open(out_file, "w")
    out.write(str(avail_az) + "\n")
    out.close()
    with open(source_file, 'r') as source:
        for operation in source:
            n = n + 1
            operation = operation.split()
            state = str(operation[0])
            timestamp = int(operation[1])
            vm_id = str(operation[2])
            if state == "START":
                ts_start.append(timestamp)
                vm_d_ts[vm_id] = timestamp
                host_usage.append(str(operation[3]))
                cpu_size.append(int(operation[4]))
                number_of_replicas = 1
                av_azs = [avail_az]
                if monte_carlo():
                    number_of_replicas = 2
                    av_azs.append(0.9995)
                    if monte_carlo():  # if np.random.randint(2):
                        number_of_replicas = 3
                        av_azs.append(0.9995)

                is_locked = set_lock_for_vm()
                ha = get_required_ha(number_of_replicas, av_azs)
                av_m.append(ha)
                lock_m.append(is_locked)
                # Todo: Rever 0.0 !=1
                #n_replicas = get_required_replicas(avail_az, ha)
                #if n_replicas != number_of_replicas:
                #    print("Problem on replicas {} != {}".format(n_replicas, number_of_replicas))
                #    exit(1)
                line = "{} {} {} {}\n".format(timestamp, vm_id, ha, is_locked)

                with open(out_file, "a") as out:
                    out.write(line)
                out.close()
            else:
                ts_stop.append(timestamp)
                lifespam.append(timestamp - vm_d_ts.get(vm_id))

    av_ms = sorted(av_m)
    lock_ms = sorted(lock_m)
    a = collections.Counter(av_ms)
    l = collections.Counter(lock_ms)

    once = [a, l, {'Len': len(ts_start)}]
    info_d = {'ts_start': ts_start, 'ts_stop': ts_stop, 'lifespam': lifespam, 'cpu_size': cpu_size,
              'host_usage': host_usage}
    export_info(info_d, once, len(ts_start))
    source.close()
    return True

def set_lock_for_vm():
    # av_mean = float((av_min + av_max) / 2.0)
    if lock == "RandomMC":
        return monte_carlo()
    elif lock == "RandomNP":
        if np.random.randint(2):
            return True 
        return False
    elif lock == "False":
        return False
    elif lock == "True":
        return True
    else:
        exit()

def get_required_ha(replicas, av_azs):
    prod = 1.0
    if type(av_azs) is list:
        if replicas == 1:
            return av_azs[0]
        for i in range(0, replicas):
            prod = prod * float(1.0 - av_azs[i])
            #print av_azs[i], i, prod
        ha = 1.0 - prod
        return ha
    elif type(av_azs) is float:
        if replicas == 1:
            return av_azs
        ha = 1.0 - np.power((1.0 - float(av_azs)), replicas)
        return ha
    return False

def truncate(tax):
    n = str(tax).count("9")
    quick_trunc = str(tax).split(".")[:n] # np.round(tax, n)
    if quick_trunc == 1.0:
        truncating = quick_trunc
        while (truncating == 1.0):
            n+=1
            truncating = str(tax)[:n] # np.round(tax, n)
        return truncating
    return quick_trunc

def get_ha_tax(downtime):
    m = 525600.0  # 365 * 24 * 60
    av = 1.0 - float(downtime) / float(m)
    return av

def get_downtime(ha):
    m = 525600.0
    downtime = (1.0 - float(ha)) * float(m)
    return downtime

# Valido apenas quando todas as AZs possuem a mesma taxa A
def get_required_replicas(a, ha=None, downtime=None):
    if ha is None:
        ha = 0.99999

    if downtime is not None:
        ha = get_ha_tax(downtime)
    else:
        downtime = get_downtime(ha)
    #if type(a) is float:

    logA = np.log10(1.0 - a)
    logHA = np.log10(1.0 - ha)
    r = float(float(logHA) / float(logA)) - 1.0
    replicas = np.ceil(r)
    print("For {} mins of Downtime is required {}% and {} replicas".format(downtime, (ha * 100), replicas))
    #else:
    return replicas

def set_av_for_az(av_min, av_max):
    # av_mean = float((av_min + av_max) / 2.0)
    if monte_carlo():
        return np.random.uniform(av_min, av_max)
    return av_min

def monte_carlo():
    radius = 1
    x = np.random.rand(2)
    # Funcao retorna 21% de probabilidade
    # Area externa de 1/4 do circulo
    if (x[0]**2)+(x[1]**2) >= radius:
        return True
    return False

def test_ha_on_demand(iterations, av_min, av_max):
    v = []
    for i in range(iterations):
        v.append(set_av_for_az(av_min, av_max))
    return v
    # print np.mean(v), np.std(v), np.amin(v), np.amax(v)
    # print "prob. nao-ha:", 100 * v.count(np.amin(v)) / float(iterations), "prob. ha grater mean:",100*sum(i > np.mean(v) for i in v)/float(iterations)


def main(dist):
    print("Creating profile with %s distribution" % (dist))


options_lock = ['RandomMC', 'RandomNP', 'False', 'True']
options_dist = ['poisson', 'uniform', 'montecarlo']
options_service = ['trace_plus', 'create_trace']

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Elastic Energy-Aware Virtual Infrastructure Realocation Algoritm')
    parser.add_argument('-source', dest='source', action='store', nargs=1, help='Source Files')
    parser.add_argument('-lock', dest='lock', action='store', nargs=1, type=str, required=True,
                        help='Commands list is: '.format(options_lock))
    parser.add_argument('-service', dest='service', action='store', nargs=1, required=False,
                        help='Service requested: '.format(options_service))
    # parser.add_argument('-virtual', dest='virtual', action='store', nargs=1, help='Virtual infrastructure input folder')
    # parser.add_argument('-output', dest='output', action='store', nargs=1, help='Profile output directory')
    parser.add_argument('-distribution', dest='dist', action='store', nargs=1, type=str, required=False,
                        help='Arrival distribution: '.format(options_dist))

    args = parser.parse_args()
    lock = args.lock[0]
    service = args.service[0]
    source_file = args.source[0]
    dist = args.dist
    print("Source is {0}".format(source_file))

    if lock not in options_lock or service not in options_service:
        print("Problem! parameter: {} not on options: {}".format(lock, options_lock))
        exit(1)

    if service == 'trace_plus':
        test_consistency(source_file)
        create_additional_info_requisitions()
    elif service == 'create_trace':
        create_profile(0, dist, source_file)
        test_consistency(source_file)
    else:
        print("Incorrect parameter")
        exit(1)
    # main(dist)


