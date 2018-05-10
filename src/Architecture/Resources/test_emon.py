
import logging

logging.basicConfig(level=logging.DEBUG, format='(%(funcName)-2s) %(message)s')
logger = logging.getLogger('Teste')

BS=60

e = EnergyMonitor(130, 'em_az1_host2', logger)
# add 1
e.alloc('vm1', 0*BS, 140, log=True)
# add 2
e.alloc('vm2', 10*BS, 155, log=True)
# add 3
e.alloc('vm3', 20*BS, 215, log=True)
# rm 2
e.dealloc('vm2', 25*BS, 200, log=True)
# rm 3
e.dealloc('vm3', 30*BS, 140, log=True)
# rm 1
e.dealloc('vm1', 40*BS, 130, log=True)  # ou zero
# add 4
e.alloc('vm4', 45*BS, 185, log=True)
# rm 4
e.dealloc('vm4', 55*BS, 130, log=True)  # ou zero
e.alloc('vm5', 57*BS, 155, log=True)
logger.debug("\nDONE!!!")
e.get_watt_hour()


"""
(alloc) 
em_az1_host2: (Alloc vm1) l:[[0, 'base', 130, '++'], [0, 'vm1', 140, '++']]
Q:['base', 'vm1']
(alloc) 
em_az1_host2: (Alloc vm2) l:[[0, 'base', 130, '++'], [0, 'vm1', 140, '++'], [600, 'vm2', 155, '++']]
Q:['base', 'vm1', 'vm2']
(alloc) 
em_az1_host2: (Alloc vm3) l:[[0, 'base', 130, '++'], [0, 'vm1', 140, '++'], [600, 'vm2', 155, '++'], [1200, 'vm3', 215, '++']]
Q:['base', 'vm1', 'vm2', 'vm3']
(dealloc) 
em_az1_host2: (Dealloc vm2) l:[[0, 'base', 130, '++'], [0, 'vm1', 140, '++'], [600, 'vm2', 155, '++'], [1200, 'vm3', 215, '++'], [1500, 'vm2', 200, '--'], [1500, 'vm3', 200, '<<']]
Q:['base', 'vm1', 'vm3']
(dealloc) 
em_az1_host2: (Dealloc vm3) l:[[0, 'base', 130, '++'], [0, 'vm1', 140, '++'], [600, 'vm2', 155, '++'], [1200, 'vm3', 215, '++'], [1500, 'vm2', 200, '--'], [1500, 'vm3', 200, '<<'], [1800, 'vm3', 140, '--'], [1800, 'vm1', 140, '<<']]
Q:['base', 'vm1']
(dealloc) 
em_az1_host2: (Dealloc vm1) l:[[0, 'base', 130, '++'], [0, 'vm1', 140, '++'], [600, 'vm2', 155, '++'], [1200, 'vm3', 215, '++'], [1500, 'vm2', 200, '--'], [1500, 'vm3', 200, '<<'], [1800, 'vm3', 140, '--'], [1800, 'vm1', 140, '<<'], [2400, 'vm1', 130, '--'], [2400, 'base', 130, '<<']]
Q:['base']
(alloc) 
em_az1_host2: (Alloc vm4) l:[[0, 'base', 130, '++'], [0, 'vm1', 140, '++'], [600, 'vm2', 155, '++'], [1200, 'vm3', 215, '++'], [1500, 'vm2', 200, '--'], [1500, 'vm3', 200, '<<'], [1800, 'vm3', 140, '--'], [1800, 'vm1', 140, '<<'], [2400, 'vm1', 130, '--'], [2400, 'base', 130, '<<'], [2700, 'vm4', 185, '++']]
Q:['base', 'vm4']
(dealloc) 
em_az1_host2: (Dealloc vm4) l:[[0, 'base', 130, '++'], [0, 'vm1', 140, '++'], [600, 'vm2', 155, '++'], [1200, 'vm3', 215, '++'], [1500, 'vm2', 200, '--'], [1500, 'vm3', 200, '<<'], [1800, 'vm3', 140, '--'], [1800, 'vm1', 140, '<<'], [2400, 'vm1', 130, '--'], [2400, 'base', 130, '<<'], [2700, 'vm4', 185, '++'], [3300, 'vm4', 130, '--'], [3300, 'base', 130, '<<']]
Q:['base']
(alloc) 
em_az1_host2: (Alloc vm5) l:[[0, 'base', 130, '++'], [0, 'vm1', 140, '++'], [600, 'vm2', 155, '++'], [1200, 'vm3', 215, '++'], [1500, 'vm2', 200, '--'], [1500, 'vm3', 200, '<<'], [1800, 'vm3', 140, '--'], [1800, 'vm1', 140, '<<'], [2400, 'vm1', 130, '--'], [2400, 'base', 130, '<<'], [2700, 'vm4', 185, '++'], [3300, 'vm4', 130, '--'], [3300, 'base', 130, '<<'], [3420, 'vm5', 155, '++']]
Q:['base', 'vm5']
(<module>) 
DONE!!!
(get_watt_hour) em_az1_host2 Remaining active vm5, subl [3420, 'vm5', 155, '++']:
(get_watt_hour) em_az1_host2: 0.0+= (0-0)/3600.0 * 130
(get_watt_hour) em_az1_host2: 23.333333333333332+= (600-0)/3600.0 * 140
(get_watt_hour) em_az1_host2: 49.166666666666664+= (1200-600)/3600.0 * 155
(get_watt_hour) em_az1_host2: 67.08333333333333+= (1500-1200)/3600.0 * 215
(get_watt_hour) em_az1_host2: 67.08333333333333+= (1500-1500)/3600.0 * 200
(get_watt_hour) em_az1_host2: 83.75+= (1800-1500)/3600.0 * 200
(get_watt_hour) em_az1_host2: 83.75+= (1800-1800)/3600.0 * 140
(get_watt_hour) em_az1_host2: 107.08333333333333+= (2400-1800)/3600.0 * 140
(get_watt_hour) em_az1_host2: 107.08333333333333+= (2400-2400)/3600.0 * 130
(get_watt_hour) em_az1_host2: 117.91666666666666+= (2700-2400)/3600.0 * 130
(get_watt_hour) em_az1_host2: 148.75+= (3300-2700)/3600.0 * 185
(get_watt_hour) em_az1_host2: 148.75+= (3300-3300)/3600.0 * 130
(get_watt_hour) em_az1_host2: 153.08333333333334+= (3420-3300)/3600.0 * 130
(get_watt_hour) em_az1_host2: 160.83333333333334+= (3600.0-3420)/3600.0 * 155
(get_watt_hour) em_az1_host2: 160.83333333333334+= (3600.0-3600.0)/3600.0 * 155
(get_watt_hour) em_az1_host2: At hour 0: 160.83333333333334 Wh, and total is 160.83333333333334 Wh
(get_watt_hour) em_az1_host2: To next hour l:[[0, 'base', 130], [0, 'vm5', 155]], q:['base', 'vm5']
"""