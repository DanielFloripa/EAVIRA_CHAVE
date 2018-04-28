#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from collections import OrderedDict
import random
# From packages:
from Chave import *
from Controller import *
from DistributedInfrastructure import *
from Demand import Demand
from Eucalyptus import *
from SLAHelper import *

"""
Class: Broker
Description: Broker manages metrics
"""


class Broker(object):
    def __init__(self, sla):
        self.sla = sla
        self.logger = sla.g_logger()

    def __repr__(self):
        return repr([self.sla, self.logger])

    def obj_id(self):
        print str(self).split(' ')[3].split('>')[0]