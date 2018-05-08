# GVT = Global Virtual Time

import argparse
from Controller import *
from collections import OrderedDict
import numpy as np
import sys
import os

# TODO: perm = permutations([1, 2, 3])
# for i in list(perm): print i

def create_profile(nit, dist):
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

    # saida
    op_realloc = [0 for i in range(nit)]
    op_delete = [0 for i in range(nit)]

    # entrada
    op_operations = randint(nit / 20, nit / 10)  # entre 5% e 10% dos intervalos
    op_operations_delete = randint(nit / 4, nit / 2)  # entre 25% e 50% dos intervalos
    while op_operations > 0:
        # random interval
        it = randint(0, nit - 1)
        if not op_realloc[it]:
            op_realloc[it] = 1
            op_operations = op_operations - 1

    while op_operations_delete > 0:
        # random interval
        it = randint(0, nit - 1)
        if not op_delete[it]:
            op_delete[it] = 1
            op_operations_delete = op_operations_delete - 1

    for i in range(nit):
        op_log[i] = []
        op_log[i].append({'op': DO_NOTHING})
        if len(vi_list) > 1:
            if op_realloc[i]:
                delete_requests, recfg_requests, repl_requests = create_realloc_requests(vi_list)

                if i not in op_log:
                    op_log[i] = []
                op_log[i].append({'op': REALLOC, 'delete_requests': delete_requests, 'recfg_requests': recfg_requests,
                                  'repl_requests': repl_requests})

            if op_delete[i]:
                delete_requests, recfg_requests, repl_requests = create_delete_requests(vi_list)

                if i not in op_log:
                    op_log[i] = []
                op_log[i].append({'op': REALLOC, 'delete_requests': delete_requests, 'recfg_requests': recfg_requests,
                                  'repl_requests': repl_requests})

        for j in range(op_allocations.count(i)):
            cfg = choose_config(virtual_folder)
            vi = [] # VirtualInfrastructure(vi_id, cfg)
            print ("Must allocate Virtual Infrastructure %d at %d" % (vi.get_id(), i))
            vi_list.append(vi)
            vi_id += 1

            lifespan = int(randint(5, 10))
            # lifespan = int(randint(5, 10)/100.0*nit)

            if i not in op_log:
                op_log[i] = []
            if i + lifespan not in op_log:
                op_log[i + lifespan] = []
            op_log[i].append({'op': ALLOC,
                              'cfg': cfg,
                              'vi': vi.get_id()})
            op_log[i + lifespan].insert(0, {'op': DEALLOC,
                                            'vi': vi.get_id()})
    return op_log, vi_list

def test_consistency(source_file):
    for_check = []
    consistent_dictionary = OrderedDict()
    consistent_list = []
    can_save = False
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
                if consistent_dictionary.has_key(vm_id + "_START"):
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
    source.close()
    if for_check:
        print("Some problem on consistency", len(for_check), source_file)
        os.rename(source_file, source_file+"_ERROR")
        out = open(source_file, "w")
        for d_id, d_list in consistent_dictionary.viewitems():
            if for_check.count(d_id.split('_')[0]) == 0:
                line = ''
                for i in range(len(d_list)):
                    line += str(d_list[i])+" "
                line += '\n'
                out.writelines(line)
        out.close()

def createAvailabilityRequisitions(source_file):
    line = 0
    avail_az = set_av_for_az(0.999, 0.9999)
    out_file = source_file.split(".txt")[0] + "-ha.txt"
    out = open(out_file, "w")
    out.write(str(avail_az) + "\n")
    out.close()
    with open(source_file, 'r') as source:
        for operation in source:
            line = line + 1
            operation = operation.split()
            state = str(operation[0])
            timestamp = int(operation[1])
            vm_id = str(operation[2])

            if state == "START":
                host = str(operation[3])
                vcpu = str(operation[4])
                number_of_replicas = 1
                if monte_carlo():
                    number_of_replicas = 2
                # No momento so temos duas AZs: HA da atual varia e a segunda eh fixa
                ha = get_required_ha(number_of_replicas, [avail_az, 0.9995])
                out = open(out_file, "aw")
                out.write(str(timestamp)+" "+str(vm_id)+" "+str(ha)+"\n")
                out.close()
    source.close()
    return True

def get_required_ha(replicas, av_azs):
    prod = 1.0
    if type(av_azs) is list:
        if replicas == 1:
            return av_azs[0]
        for i in range(0, replicas):
            prod = prod * float(1.0 - av_azs[i])
            #print av_azs[i], i, prod
        ha = 1.0 - prod
    elif type(av_azs) is float:
        if replicas == 1:
            return av_azs
        ha = 1.0 - np.power((1.0 - float(av_azs)), replicas)
    return ha

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
    m = 525600.0 # 365 * 24 * 60
    av = 1.0 - float(downtime / m)
    return av

# Valido apenas quando todas as AZs possuem a mesma taxa A
def get_required_replicas(a, ha=None, downtime=None):
    if downtime is not None:
        ha = get_ha_tax(downtime)
    if ha is None:
        ha = 0.99999
    #if type(a) is float:
    logA = np.log10(1.0 - a)
    logHA = np.log10(1.0 - ha)
    r = float(logHA / logA) - 1.0
    replicas = np.ceil(r)
    print("For %s min of Downtime is required %s and %s replicas" % (downtime, (ha * 100), replicas))
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
    #print np.mean(v), np.std(v), np.amin(v), np.amax(v)
    #print "prob. nao-ha:", 100 * v.count(np.amin(v)) / float(iterations), "prob. ha grater mean:",100*sum(i > np.mean(v) for i in v)/float(iterations)

def main(dist):
    print("Creating profile with %s distribution" % (dist))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Elastic Energy-Aware Virtual Infrastructure Realocation Algoritm')
    parser.add_argument('-source', dest='source', action='store', nargs=1, help='Source Files')

    parser.add_argument('-max-gvt', dest='max_gvt', action='store', nargs=1, type=bool, required=False)
#    parser.add_argument('-nit', dest='nit', action='store', nargs=1, type=int, help='Number of iterations: N')
#    parser.add_argument('-pr', dest='pr', action='store', nargs='+', help='%% of restricted VMs in decimal')
#    parser.add_argument('-virtual', dest='virtual', action='store', nargs=1, help='Virtual infrastructure input folder')
#    parser.add_argument('-output', dest='output', action='store', nargs=1, help='Profile output directory')
#    parser.add_argument('-distribution', dest='dist', action='store', nargs=1, help='Arrival distribution: poisson or uniform')

    args = parser.parse_args()

    source_file = args.source[0]
    print("Source is {0}".format(source_file))
    test_consistency(source_file)
    createAvailabilityRequisitions(source_file)
    # main(dist)
