#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
from collections import OrderedDict

class EnergyMonitor():
    def __init__(self, base, logger):
        self.logger = logger
        self.__list = []
        self.__queue = []
        self.next_l = []
        self.next_q = []
        self.base = base
        self.is_init = self.__init_base(all=True)

    def __repr__(self):
        return repr((self.__list, self.__queue, self.next_l, self.next_q, self.base, self.is_init))

    # Return the unique hexadecimal footprint from each object
    def obj_id(self):
        return str(self).split(' ')[3].split('>')[0]
    
    def __init_base(self, all=False):
        self.next_l.append([0, 'base', self.base])
        self.next_q.append('base')
        if all:
            self.alloc('base', 0, self.base)
        return True

    def get_watt_hour(self):
        consumo = 0
        if len(self.__queue) > 1:
            while len(self.__queue) > 1:
                try:
                    active = self.__queue[1]
                    self.next_q.append(active)
                    for subl in self.__list:
                        if active in subl:
                            self.logger.debug("Remaining active {}, subl {}:".format(active, subl))
                            self.next_l.append([0, active, subl[2]])
                            self.dealloc(active, 60, subl[2])
                            break
                except IndexError:
                    pass
        else:
            try:
                base = self.__queue[-1]
                self.next_q.append(base)
                self.dealloc(base, 60, self.base)
            except IndexError:
                pass

        for i, ll in enumerate(self.__list):
            try:
                consumo += ((self.__list[i+1][0] - ll[0])/60) * ll[2]
                self.logger.debug("\n{0} += ({1} - {2})/60 * {3}".format(consumo, self.__list[i + 1][0], ll[0], ll[2]))
                # self.logger.debug("{0} += ({1}) * {2}".format(consumo, (self.__list[i + 1][0] - ll[0])/60, ll[2]))
            except IndexError:
                continue

        self.__list = list(self.next_l)
        self.__queue = list(self.next_q)
        self.logger.debug("AVG hour {}".format(consumo))
        self.logger.debug("To next hour lst:{}, que:{}".format(self.__list, self.__queue))

    def alloc(self, id, time, cons):
        self.__list.append([time, id, cons, '++'])
        self.__queue.append(id)
        self.logger.debug("\nAlc lst:{}: {}\nQue: {}".format(id, self.__list, self.__queue))

    def dealloc(self, id, time, cons):
        templ = self.__list.pop()
        self.__list.append(templ)
        self.__list.append([time, id, cons, '--'])
        top = ''
        try:
            i = self.__queue.index(id)
            self.__queue.pop(i)
            top = self.__queue[-1]
        except IndexError:
            pass
        self.__list.append([time, top, cons, '<<'])
        #l.append([time, templ[1], cons, '<<'])
        self.logger.debug("\nDalc lst:{}: {}\nQue: {}".format(id, self.__list, self.__queue))

    @staticmethod
    def test():
        e = EnergyMonitor(130)
        # add 1
        e.alloc('vm1', 0, 140)
        # add 2
        e.alloc('vm2', 10, 155)
        # add 3
        e.alloc('vm3', 12, 215)
        # rm 2
        e.dealloc('vm2', 20, 200)
        # rm 3
        e.dealloc('vm3', 37, 140)
        # rm 1
        e.dealloc('vm1', 40, 130)
        # add 4
        e.alloc('vm4', 45, 140)
        # rm 4
        e.dealloc('vm4', 55, 130)
        e.alloc('vm5', 56, 140)
        e.alloc('vm6', 58, 155)
        self.logger.debug("\nDONE!!!")
        e.get_watt_hour()

