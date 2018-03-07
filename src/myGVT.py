import argparse
import cPickle as pickle
from copy import deepcopy
from random import randint, uniform
from timeit import default_timer
import numpy as np
from BaseInfrastructure import SLA_BASED, VI_BASED
from Virtual import VirtualMachine
from Physical import *
from Datacenter import Datacenter
from Algorithms import dijkstra
from Controller import *

ALLOC = 0
#REALLOC = 1
DEALLOC = 2
#DO_NOTHING = 3


def choose_config(virtual_folder):
    # Choose a random virtual file
    virtual_files = os.listdir(virtual_folder)
    return virtual_folder + virtual_files[random.randint(0, len(virtual_files) - 1)]


def print_list(vi_list):
    for vi in vi_list:
        for vnode in vi.get_virtual_resources():
            print ("VI's list: (%d) vnode(%d)" % (vi.get_id(), vnode.get_id()))


def create_delete_requests(vi_list):
    delete_requests = []
    recfg_requests = []
    repl_requests = []

    # Delete
    vi_id = random.randint(0, len(vi_list) - 1)
    vn_id = random.randint(0, len(vi_list[vi_id].get_virtual_resources()) - 1)
    print ("Delete request VI(%d) vnode(%d)" % (
    vi_list[vi_id].get_id(), vi_list[vi_id].get_virtual_resources()[vn_id].get_id()))
    delete_requests.append(
        {'vi': vi_list[vi_id].get_id(), 'vnode': vi_list[vi_id].get_virtual_resources()[vn_id].get_id()})

    return delete_requests, recfg_requests, repl_requests


def create_realloc_requests(vi_list):
    delete_requests = []
    recfg_requests = []
    repl_requests = []

    # Replication
    vi_id = random.randint(0, len(vi_list) - 1)
    vn_id = random.randint(0, len(vi_list[vi_id].get_virtual_resources()) - 1)
    print ("Replication request VI(%d) vnode(%d)" % (
    vi_list[vi_id].get_id(), vi_list[vi_id].get_virtual_resources()[vn_id].get_id()))
    repl_requests.append(
        {'vi': vi_list[vi_id].get_id(), 'vnode': vi_list[vi_id].get_virtual_resources()[vn_id].get_id()})

    # Reconfiguration
    vi_id = random.randint(0, len(vi_list) - 1)
    vn_id = random.randint(0, len(vi_list[vi_id].get_virtual_resources()) - 1)
    print ("Reconfiguration request VI(%d) vnode(%d)" % (
    vi_list[vi_id].get_id(), vi_list[vi_id].get_virtual_resources()[vn_id].get_id()))
    up_down = random.randint(1, 4)
    signal = random.randint(0, 1)
    if signal == 0:
        up_down = up_down * -1
    up_down = up_down / 10

    vnode = vi_list[vi_id].get_virtual_resources()[vn_id]

    new_cfg = {}
    new_cfg['vi'] = vi_list[vi_id].get_id()
    new_cfg['vnode'] = vnode.get_id()
    new_cpu = vnode.get_vcpu() + (vnode.get_vcpu() * up_down)
    new_ram = vnode.get_vram() + (vnode.get_vram() * up_down)
    new_storage = vnode.get_vstorage() + (vnode.get_vstorage() * up_down)
    if new_cpu < 1:
        new_cfg['vcpu'] = 0
    else:
        new_cfg['vcpu'] = new_cpu

    if new_ram < 1:
        new_cfg['vram'] = 0
    else:
        new_cfg['vram'] = new_ram

    if new_storage < 1:
        new_cfg['vstorage'] = 0
    else:
        new_cfg['vstorage'] = new_storage

    recfg_requests.append(new_cfg)

    return delete_requests, recfg_requests, repl_requests


def create_profile(nit, dist):
    vi_id = 0
    op_log = {}
    vi_list = []

    if dist == 'poisson':
        op_allocations = np.random.poisson(nit / 2, nit).tolist()
    elif dist == 'uniform':
        op_allocations = np.random.random_integers(0, nit, nit / 3).tolist()
    else:
        print "Invalid dist %s" % (dist)
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
            vi = VirtualInfrastructure(vi_id, cfg)
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


def main(dist):
    print "Creating profile with %s distribution" % (dist)

    profile, vi_list = create_profile(nit, dist)

    out_fname = output_folder + virtual_folder.split('/')[-2]

    # Set restrictive SLA and pickle it
    for pr in pr_list:
        new_vi_list = deepcopy(vi_list)

        with open(out_fname + '_' + str(pr) + '.pkl', 'wb') as out_vi:
            for vi in new_vi_list:
                vresources = vi.get_virtual_resources()
                # Restricting VI's SLA
                chosen = []
                for i in range(int(pr * len(vresources))):
                    vnode = vresources[randint(0, len(vresources) - 1)]
                    while vnode in chosen:
                        vnode = vresources[randint(0, len(vresources) - 1)]
                    chosen.append(vnode)
                    vnode.sla_time = -1
                # print "VI:",vi,",CHOOSEN:",chosen,",vnode:",vnode
                pickle.dump(vi, out_vi, pickle.HIGHEST_PROTOCOL)

    with open(out_fname + '.log', 'w') as log:
        for i in range(nit):
            for task in profile[i]:
                if task['op'] == DO_NOTHING:
                    log.write('%d\n%s %d\n' % ((DO_NOTHING), -1, -1))
                elif task['op'] == ALLOC:
                    log.write('%d\n%s %d\n' % ((ALLOC, task['cfg'], task['vi'])))
                elif task['op'] == DEALLOC:
                    log.write('%d\n%s\n' % ((DEALLOC, task['vi'])))
                elif task['op'] == REALLOC:
                    log.write('%d\n' % (REALLOC))
                    log.write('%d\n' % (len(task['delete_requests'])))
                    for request in task['delete_requests']:
                        log.write('%d %d\n' % (request['vi'], request['vnode']))
                    log.write('%d\n' % (len(task['recfg_requests'])))
                    for request in task['recfg_requests']:
                        log.write('%d %d %d %d %d\n' % (request['vnode'],
                                                        request['vnode'],
                                                        request['vcpu'],
                                                        request['vram'],
                                                        request['vstorage']))
                    log.write('%d\n' % (len(task['repl_requests'])))
                    for request in task['repl_requests']:
                        log.write('%d %d\n' % (request['vi'], request['vnode']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Elastic Energy-Aware Virtual Infrastructure Realocation Algoritm')
    parser.add_argument('-nit', dest='nit', action='store', nargs=1, type=int, help='Number of iterations: N')
    parser.add_argument('-pr', dest='pr', action='store', nargs='+', help='%% of restricted VMs in decimal')
    parser.add_argument('-virtual', dest='virtual', action='store', nargs=1, help='Virtual infrastructure input folder')
    parser.add_argument('-output', dest='output', action='store', nargs=1, help='Profile output directory')
    parser.add_argument('-distribution', dest='dist', action='store', nargs=1, help='Arrival distribution: poisson or uniform')
    args = parser.parse_args()

    nit = args.nit[0]
    pr_list = [float(e) for e in args.pr]
    virtual_folder = args.virtual[0]
    output_folder = args.output[0]
    dist = args.dist[0]

    main(dist)
