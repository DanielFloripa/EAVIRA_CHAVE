#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
from collections import OrderedDict

metrics_dict = OrderedDict()

def metrics(command, key, value=None, n=-1):

    command_list = ['get', 'set', 'add', 'init', 'summ']
    key_list = ['total_alloc', 'accepted_alloc',
                'acc_list', 'acc_means', 'energy_list', 'energy_means', 'nop_list', 'nop_means',
                'sla_break', 'sla_break_steal', 'alloc', 'total_alloc_list', 'dealloc', 'realloc',
                'energy_rlc', 'energy_ttl', 'dc_vm_load', 'dc_load']
    l = len(key_list)
    global l1, l2, l3
    if command is 'init':
        if key is "ALL":
            key1 = key_list[0:2]  # inteiros
            l1 = len(key1)
            key2 = key_list[2:8]  # v listas vazias v
            l2 = len(key2)
            key3 = key_list[8:l]  # z listas inicializadas em 0 z
            l3 = len(key3)
            key = [key1, key2, key3]
            print l1, l2, l3
            if value == "ZEROS" and n > 0:
                for kk in key:
                    x = len(kk)
                    for k in kk:
                        if x == l1:
                            metrics_dict[k] = 0.0
                        elif x == l2:
                            metrics_dict[k] = []
                        elif x == l3:
                            metrics_dict[k] = [0 for i in range(n)]
                return True, metrics_dict
        else:
            print "You must specify 'n'!!"
            return False
        print "Metrics init %s:%s -> %s" % (key, value, metrics_dict.viewitems())
    elif command is 'set':
        if key in key_list[0:l1]:
            metrics_dict[key] = value
            print "Metrics set %s:%s -> %s" % (key, value, metrics_dict.viewitems())
            return True
        elif key in key_list[l1:l1+l2]:
            metrics_dict[key].append(value)
            print "Metrics set %s:%s -> %s" % (key, value, metrics_dict.viewitems())
            return True
        elif key in key_list[l1+l2: l] and n > 0:
            metrics_dict[key][n] = value
            print "Metrics set %s:%s -> %s" % (key, value, metrics_dict.viewitems())
            return True
        else:
            print "Key (%s) not found for Command %s!!" % (key, value)
            return False
    elif command is 'get':
        if key in key_list:
            print "Metrics get %s:%s -> %s" % (key, value, metrics_dict[key])
            return metrics_dict[key]
        else:
            print "Key (%s) not found for Command %s!!" % (key, value)
            return False
    elif command is 'add':
        if key in key_list[0:l1+l2]:
            metrics_dict[key] = metrics_dict[key] + value
            print "Metrics added %s:%s -> %s" % (key, value, metrics_dict[key])
            return metrics_dict[key]
        if key in key_list[l1+l2:l]:
            metrics_dict[key] = metrics_dict[key].append(value)
            print "Metrics added %s:%s -> %s" % (key, value, metrics_dict[key])
            return metrics_dict[key]
        else:
            print "Key (%s) not found for Command %s!!" % (key, value)
            return False
    elif command is 'summ':
        if key in key_list[0:l1]:
            print "Metrics summ %s:%s -> %s" % (key, value, metrics_dict[key])
            return metrics_dict[key]
        elif key in key_list[l1:l1+l2]:
            print "Metrics summ %s:%s -> %s" % (key, value, metrics_dict[key])
            return sum(values for values in metrics_dict[key])
        elif key in key_list[l1+l2: l]:
            print "Metrics summm %s:%s -> %s" % (key, value, metrics_dict[key])
            return sum(val for val in list(metrics_dict[key]))
        else:
            print "Key (%s) not found for Command %s!!" % (key, value)
            return False
    else:
        print "Command (" + str(command) + ") not found!!"
    return False

key_list = ['total_alloc', 'accepted_alloc',
                'acc_list', 'acc_means', 'energy_list', 'energy_means', 'nop_list', 'nop_means',
                'sla_break', 'sla_break_steal', 'alloc', 'total_alloc_list', 'dealloc', 'realloc', 'energy_rlc',
                'energy_ttl', 'dc_vm_load', 'dc_load']

def main():
    pass
    '''print metrics('init', 'ALL', 'ZEROS', 20)
    for i, key in enumerate(key_list):
        print metrics('set', key, i)
    print metrics('set', 'total_alloc', 44)
    print metrics('add', 'total_alloc', 6)
    print metrics('get', 'total_alloc')
    print metrics('get', 'dc_load')
    print metrics('add', 'dc_vm_load', 4)
    print metrics('add', 'dc_load', 63)
    print metrics('get', 'dc_vm_load')
    print metrics('summ', 'total_alloc', 4)
    print metrics('summ', 'dc_load')
    print metrics('get', 'total_alloc')
    print metrics_dict.viewitems()'''


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='CHAVE Simulator')
    parser.add_argument('-in', dest='input', action='store', nargs='+', type=str, help='Input file', required=True)
    parser.add_argument('-out', dest='output', action='store', nargs='?', type=float, help='Output file')
    args = parser.parse_args()

    source_file = args.input





    main()

