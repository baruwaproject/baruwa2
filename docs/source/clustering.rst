
==========
Clustering
==========

Functionality available
=======================

Baruwa is capable of running in a cluster, The only requirement is that the 
nodes share session information and have access to either the same MQ broker
or use a MQ broker that is clustered with the other brokers serving the other
nodes. 

Full Baruwa functionality is available from any member within a Baruwa cluster
and all cluster members have equal status. This allows your to provide round
robin access either using a load balancer or DNS configuration. This makes the
running of a cluster totally transparent to the end users.

Cluster wide as well as node status information is visible via :ref:`global_status`
and :ref:`scanner_node_status`

Requirements
============

Baruwa stores client session information in Memcached, so all the nodes in the
cluster should be configured to use the same Memcached server.

All the nodes with in a cluster should be configured to write to a single database.

Limitations
===========

Quarantines are node specific, so messages quarantined on a failed node will
not be accessible until the node is restored.