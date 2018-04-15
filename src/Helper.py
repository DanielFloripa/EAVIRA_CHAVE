from copy import deepcopy
import random
from math import sqrt
from numpy import std, mean, sqrt
import numpy as np

from Virtual import VirtualMachine
from collections import OrderedDict


class Helper(object):
    def __init__(self, algorithm, logger):
        self.metrics_dict = OrderedDict
        self.algorithm = algorithm
        self.logger = logger
        self.azs_id = []
        self.number_of_azs = -1
        self.vmRam_default = 4


    def _define_az_id(self, list_of_souce_files):
        azs_id = []
        for source in list_of_souce_files:
            ns = str(source).rfind("/")
            ne = str(source).rfind("-")
            azs_id.append(str(source[ns + 1:ne]))
        if len(list_of_souce_files) > 1:
            self.azs_id = azs_id
            self.number_of_azs = len(list_of_souce_files)
        else:
            return azs_id

    def define_regions(self, source_list, max_az_per_region):
        if max_az_per_region < 2:
            self.logger.error("Low value config max-ax-per-region, must be > 2")
        n = len(source_list)
        regions_list = []
        for i in range(0, n):
            kv = {"name": 'region_'+str(i),
                  "azs_max": 'max_az_per_region'}
            regions_list.append(kv)
        return regions_list

    def monte_carlo(self):
        radius = 1
        x = np.random.rand(1)
        y = np.random.rand(1)
        # Funcao que retorna 21% de probabilidade
        if x ** 2 + y ** 2 >= radius:
            return True
        return False

    def my_std(data):
        u = mean(data)
        std = sqrt(1.0 / (len(data) - 1) * sum([(e - u) ** 2 for e in data]))
        return 1.96 * std / sqrt(len(data))

    def mean(data):
        return sum(data) / float(len(data))'''
