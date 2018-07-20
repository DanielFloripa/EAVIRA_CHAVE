#!/usr/bin/python
# -*- coding: utf-8 -*-

FULL = 3600.0


class EnergyMonitor(object):
    def __init__(self, base, em_id, logger):
        self.em_id = em_id
        self.base = base
        self.logger = logger
        self.__hlist = []
        self.__queue = []
        self.__nxt_hlist = []
        self.__nxt_queue = []
        self.general_cons_list = []
        self.is_init = self.__init_base(all=True)
        self.hours = 0
        self.total_consumption = 0

    def __repr__(self):
        return repr((self.__hlist, self.__queue, self.__nxt_hlist,
         self.__nxt_queue, self.base, self.is_init))

    # Return the unique hexadecimal footprint from each object
    def obj_id(self):
        return str(self).split(' ')[3].split('>')[0]
    
    def __init_base(self, all=False):
        self.__nxt_hlist.append([0, 'base', self.base])
        self.__nxt_queue.append('base')
        if all:
            self.alloc('base', 0, self.base, log=False)
        return True

    def get_consumption_list(self):
        return self.general_cons_list

    def get_total_consumption(self):
        return self.total_consumption

    def get_watt_hour(self):
        if len(self.__queue) > 1:
            while len(self.__queue) > 1:
                try:
                    active = self.__queue[1]
                    self.__nxt_queue.append(active)
                    for subl in self.__hlist:
                        if active in subl:
                            self.logger.debug("{0} Remaining active {1}, subl {2}:".format(
                                self.em_id, active, subl))
                            self.__nxt_hlist.append([0, active, subl[2]])
                            self.dealloc(active, FULL, subl[2])
                            break
                except IndexError:
                    pass
        else:
            try:
                base = self.__queue[-1]
                self.__nxt_queue.append(base)
                self.dealloc(base, FULL, self.base)
            except IndexError:
                pass

        consumo = 0
        for i, ll in enumerate(self.__hlist):
            try:
                consumo = consumo + ((float(self.__hlist[i + 1][0]) - float(ll[0])) / FULL) * float(ll[2])
                self.logger.debug("{0}: {1}+= ({2}-{3})/{4} * {5}".format(
                    self.em_id, consumo, self.__hlist[i+1][0], ll[0], FULL, ll[2]))
                # self.logger.debug("{0} += ({1}) * {2}".format(consumo, (
                # self.em_id, self.__hlist[i + 1][0] - ll[0])/FULL, ll[2]))
            except IndexError:
                continue

        self.__hlist = list(self.__nxt_hlist)
        self.__queue = list(self.__nxt_queue)
        self.total_consumption += consumo
        self.general_cons_list.append(consumo)
        self.logger.debug("{0}: At hour {1}: {2} Wh, and total is {3} Wh".format(
            self.em_id, self.hours, consumo, self.total_consumption))
        self.logger.debug("{0}: To next hour l:{1}, q:{2}".format(
            self.em_id, self.__hlist, self.__queue))
        self.hours += 1
        return consumo

    # Todo:
    def get_watt_partial(self):
        pass

    def alloc(self, vm_id, time, cons, log=False):
        if time > FULL:
            time = time % FULL
        self.__hlist.append([time, vm_id, cons, '++'])
        self.__queue.append(vm_id)
        if log:
            self.logger.debug("\n{0}: (Alloc {1}) l:{2}\nQ:{3}".format(self.em_id, vm_id, self.__hlist, self.__queue))

    def dealloc(self, vm_id, time, cons, log=False):
        if time > FULL:
            time = time % FULL
        #templ = self.__hlist.pop()
        #self.__hlist.append(templ)
        self.__hlist.append([time, vm_id, cons, '--'])
        top = ''
        try:
            i = self.__queue.index(vm_id)
            self.__queue.pop(i)
            top = self.__queue[-1]
        except IndexError:
            pass
        except ValueError:
            self.logger.error("{0} ValueError on: {1}".format(self.em_id, self.__queue))
        self.__hlist.append([time, top, cons, '<<'])
        if log:
            self.logger.debug("\n{0}: (Dealloc {1}) l:{2}\nQ:{3}".format(self.em_id, vm_id, self.__hlist, self.__queue))

    @staticmethod
    def test(logger):

        e = EnergyMonitor(130, 'host_test', logger)
        # add 1
        e.alloc('vm1', 0, 140)
        # add 2
        e.alloc('vm2', 10, 155)
        # add 3
        e.alloc('vm3', 20, 215)
        # rm 2
        e.dealloc('vm2', 25, 200)
        # rm 3
        e.dealloc('vm3', 30, 140)
        # rm 1
        e.dealloc('vm1', 40, 130) # ou zero
        # add 4
        e.alloc('vm4', 45, 185
                )
        # rm 4
        e.dealloc('vm4', 55, 130) # ou zero
        e.alloc('vm5', 57, 155)
        logger.debug("\nDONE!!!")
        e.get_watt_hour()

