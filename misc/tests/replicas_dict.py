
from collections import OrderedDict
import operator

class VM:
    def __init__(self, vmid, timestamp):
        self.vm_id = vmid
        self.timestamp = timestamp

replicas_dict = OrderedDict()
ordered_replicas_dict = OrderedDict()

for vm_id in range(21, 30):
    if vm_id % 3 == 0:
        replicas_dict[vm_id] = VM('a'+str(vm_id),-vm_id ** vm_id)
    else:
        replicas_dict[vm_id] = VM('a' + str(vm_id), vm_id + vm_id)

replicas_dict.popitem()
print "Normal"
for vm in replicas_dict.viewvalues():
    print vm.timestamp

ordered_replicas_dict = OrderedDict()
for vm in (sorted(replicas_dict.values(), key=operator.attrgetter('timestamp'), reverse=True)):
    ordered_replicas_dict[vm.vm_id] = vm

print "In order:"
for vm in ordered_replicas_dict.viewvalues():
    print vm.timestamp

x=ordered_replicas_dict.popitem()
print "pop:", x[1].timestamp