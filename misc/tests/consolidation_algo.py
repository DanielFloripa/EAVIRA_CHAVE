#!/usr/bin/python
# -*- coding: utf-8 -*-

from collections import OrderedDict
from math import floor
import sys

hosts = 6
vms = 15
azcpu = 8
cpu_total = azcpu * hosts


hid, vmid = [], []

for i in range(hosts):
    hid.append('h'+str(i))

for i in range(vms):
    vmid.append('vm'+str(i))

h = OrderedDict()

for h_id in hid:
    h[h_id] = []

if True:
    h[hid[0]].append([vmid[0],2])
    h[hid[0]].append([vmid[1],2])
    h[hid[0]].append([vmid[13],1])
    h[hid[0]].append([vmid[14],1])

    h[hid[1]].append([vmid[2],2])
    h[hid[1]].append([vmid[3],2])
    h[hid[1]].append([vmid[4],1])

    h[hid[2]].append([vmid[5],4])
    h[hid[2]].append([vmid[6],2])
    h[hid[2]].append([vmid[7],1])

    h[hid[3]].append([vmid[8],2])
    h[hid[3]].append([vmid[9],1])
    h[hid[3]].append([vmid[10],1])

    h[hid[4]].append([vmid[11],4])
    h[hid[4]].append([vmid[12],2])

def get_vm_list(h, cpu_total):
    d, hh, cpud = OrderedDict(), OrderedDict(), OrderedDict()
    for h_id, _ in h.items():
        hh[h_id] = []
        cpud[h_id] = OrderedDict()
        for i in range(azcpu):
            cpud[h_id][i] = []

    cpu_remain = cpu_total
    for h_id, hl in h.items():
        for vml in hl:
            d[vml[0]] = {'cpu': vml[1], 'host': h_id}
            hh[h_id].append({'cpu': vml[1], 'vm': vml[0]})
            cpud[h_id][vml[1]].append(vml)
            cpu_remain = cpu_remain - vml[1]
    return d, hh, cpud, cpu_remain

d, hh, cpud, cpu_remain = get_vm_list(h, cpu_total)

fragmentation = float(cpu_remain) / float(cpu_total)
objective = floor(fragmentation * hosts)

def fixa_maiores(d, h, azcpu):
    # 1) fixar vms com cpus mais de 1/2 azcpu. Faca isso ate a metade dos hosts
    print("\n\nFixa_maiores\n")
    vm_to_migrate = OrderedDict(d)
    hosts_to_migrate = OrderedDict(h)
    fixedVM = OrderedDict()
    fixedHost = OrderedDict()

    for vm_id, vm_dict in d.items():
        if vm_dict['cpu'] >= (azcpu * 1/2.0):  # Fixe:
            try:
                poph = hosts_to_migrate.pop(vm_dict['host'])
                print("pop-h[{}]: {}".format(vm_dict['host'], poph))
                fixedHost[vm_dict['host']] = h[vm_dict['host']]
            except KeyError:
                print("KEY ERROR POP_H.........", vm_id, vm_dict['host'], hosts_to_migrate)
                pass
            for vm in poph:
                try:
                    popd = vm_to_migrate.pop(vm[0])
                    print("\t\tpop-d[{}]: {}".format(vm[0], popd))
                    fixedVM[vm[0]] = vm_dict
                except KeyError:
                    print("KEY ERROR POP_D.........", vm[0], vm_to_migrate)
                    pass
            if len(vm_to_migrate) <= float(len(h) * 1/2.0):
                print("Saindo a força do max_fixo_1")
                break

    print("Return m: \nfixedVM: {}\nfixedHost: {}\n\nvm_to_migrate: {}\n\nhosts_to_migrate: {}".format(fixedVM, fixedHost, vm_to_migrate, hosts_to_migrate))   
    return fixedVM, fixedHost, vm_to_migrate, hosts_to_migrate

def fixa_quantidade(d_t, h_t):
    print("\n\nFixa_Quantidade\n")
    max_len = 0
    max_density = 0
    fixedHost = OrderedDict()   #FIXO
    #fixedVM = OrderedDict()   #FIXO
    hosts_to_migrate = OrderedDict(h_t)  # paraMigrar
    for k in sorted(h_t, key=lambda k: len(h_t[k]), reverse=True):
        print("Trying: ", k, len(h_t[k]),),
        if len(h_t[k]) >= max_len:
            max_len = len(h_t[k])
            print("\tNew Max_len: ", max_len)
            fixedHost[k] = h_t[k]
            try:
                pop_h = hosts_to_migrate.pop(k)
                print("\t\tpop_h[{}]: {}".format(k, pop_h))
            except KeyError:
                print("KEY ERRORRRRRRR POPH.........", k, hosts_to_migrate)
                pass
            for vm in pop_h:
                try:
                    pop_d = d_t.pop(vm[0])
                    print("\t\t\tpop_d[{}]: {}".format(vm[0], pop_d))
                except KeyError:
                    print("KEY ERRORRRRRRR POPD.........", vm[0], d_t)
                    pass
            #if len(hosts_to_migrate) <= float(len(h_t) * 1/2.0):
            #   print("Saindo do max_fixo_2")
            #   break
    print("Return q: \n\nfixedHost: {}\n\nhosts_to_migrate: {}\n\nvm_to_migrate: {}".format(fixedHost, hosts_to_migrate, d_t))
    return fixedHost, hosts_to_migrate, d_t

hosts_to_migrate = OrderedDict(h)
max_iter = 1
finalF = dict()
finalM = dict()
vm_to_migrate = OrderedDict(d)

while (len(hosts_to_migrate) > objective) and (max_iter < 5):
    print("\n\n\t\t\t\t ######### ITER: {} ######### \n\n\n\n".format(max_iter))
    fixedVM, fixedHost, vm_to_migrate, hosts_to_migrate = fixa_maiores(vm_to_migrate, hosts_to_migrate, (azcpu / float(max_iter)))
    finalF.update(fixedHost)

    fixedHost, hosts_to_migrate, vm_to_migrate = fixa_quantidade(vm_to_migrate, hosts_to_migrate)
    finalF.update(fixedHost)
    finalM = OrderedDict(hosts_to_migrate)
    max_iter += 1

#print("max_iter: {}, \n\n hosts_to_migrate: {}, \n\n fixedHost: {}, \n\nd_t:{}, \n\nh_t:{}, \n\nFinalF:{}, \n\nFinalM:{}".format(max_iter, hosts_to_migrate, fixedHost, d_t, h_t, finalF, finalM))


print("\n\n\t\t\t\t ######### THE_END ######### \n\n\n\n") 
print("hosts_to_migrate: {}, \n\n ".format(hosts_to_migrate))
print("fixedHost: {}, \n\n".format(fixedHost))
print("vm_to_migrate:{}, \n\n".format(vm_to_migrate))
print("fixedVM:{}, \n\n".format(fixedVM))
print("FinalF:{}, \n\n".format(finalF))
print("FinalM:{}".format(finalM))

sys.exit(1)
