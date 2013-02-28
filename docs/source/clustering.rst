
==========
Clustering
==========

Functionality available
=======================

Baruwa is capable of running in a cluster

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

All nodes should be configured to either use a clustered MQ broker or use the
same MQ broker as the other nodes. The nodes should be aware of the other nodes
queues to enable them to submit tasks to those queues.

All the nodes with in a cluster should be configured to write to a single database
and index data to a single or distributed sphinx server.

The full requirements are:

* Shared Memcached server
* Shared PostgreSQL server
* Shared MQ broker or clustered broker
* Shared Sphinx server or distributed sphinx servers

The recommended setup is to have Memcached, PostgreSQL, RabbitMQ, Sphinx running
on a separate server.

The firewall on the server hosting the above shared services needs to be configured
to allow the following connections from the cluster nodes.

* TCP 9312, 9306 - Sphinx
* TCP 5432 - PostgreSQL or 6432 Pgbouncer
* TCP 4369 - RabbitMQ EPMD
* TCP 11211 - Memcached 

Limitations
===========

Quarantines are node specific, so messages quarantined on a failed node will
not be accessible until the node is restored.

The are ways to over come this limitation, contact the
`Developer <http://www.topdog.za.net>`_ if this is a core requirement for you.