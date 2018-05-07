#!/usr/bin/python
# -*- coding: utf-8 -*-

from collections import OrderedDict

import logging
import threading
import time

logging.basicConfig(level=logging.DEBUG,format='(%(threadName)-2s) %(message)s')

l = []

def consumer(cond):
    """wait for the condition and use the resource"""
    t = threading.currentThread()
    with cond:
        cond.wait()
        logging.debug('Resource is available to consumer {0}'.format(t.getName()))
        if len(l) > 0:
            x=l.pop(0)
            logging.debug("pop:{0} now:{1}".format(x, l))


def producer(cond):
    """set up the resource to be used by the consumer"""
    xx = 0

    while xx < 10:
        if len(l) == 0:
            l.append(xx)
            logging.debug("append:{0} --> xx{1}".format(l, xx))
            logging.debug('Making resource available')
            xx += 1
            with cond:
                cond.notifyAll()


condition = threading.Condition()
c1 = threading.Thread(name='c1', target=consumer, args=(condition,))
c2 = threading.Thread(name='c2', target=consumer, args=(condition,))
p = threading.Thread(name='p', target=producer, args=(condition,))

p.start()
c1.start()
c2.start()
