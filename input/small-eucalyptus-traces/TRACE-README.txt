DS1: 13 nodes, 24 cores/node, RR scheduled
DS2: 7 nodes, 12 cores/node, Greedy scheduled
DS3: 7 nodes, 8 cores/node, RR scheduled
DS4: 12 nodes, 8 cores/node, RR scheduled
DS5: 31 nodes, 32 cores/node, RR scheduled
DS6: 31 nodes, 32 cores/node, RR scheduled

Each file contains a trace of the VM start and stop events recorded by a
Eucalyptus Cluster Controller in a single Availability Zone.  The files
contain both START and STOP records, sorted by timestamp where the timestamp
records the number of seconds since the beginning of the trace.  

The start record format is

START timestamp instance-id node-name core-count

and the stop record format is

STOP timestamp instance-id

Each instance-id should have both a START and STOP record in each file.  

The data contains some anomalies than an analysis must consider.  First,
due to logging errors in the diagnostic logs used to generate these traces, 
there are periods of time in some of the traces where no data is recorded.

The traces correct for these drop out periods in the following way.
Instances that appear before a drop out period begins but do not appear after
it ends are assumed to be terminated at the beginning of the period.
Similarly, instances that were not in the logs before a drop out period but
that appear as running at the end of a drop out, are assumed to start
immediately when the drop out period ends.

Secondly, the Eucalyptus Cluster Controller and Node Controller contained a
bug that would allow the system to over commit nodes.  That is, there are
periods of time during which VMs are assigned to nodes such that the total
number of cores in the assigned VMs exceeds the core count for the node.
In these cases, the hypervisor would simply time slice the VMs using its local
scheduler.   

We wish to thank the institutions that donated their Eucalyptus logs to
our project.  These institutions did so on the condition of anonymity.  Please
respect their wishes in the event the level of anonymization we have used is
insufficient to protect their identities.


