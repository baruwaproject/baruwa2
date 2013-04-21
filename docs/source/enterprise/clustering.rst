
.. _clustering:

==========
Clustering
==========

Functionality available
=======================

Baruwa is capable of running in a cluster. Full clustering support is only available
in the Enterprise edition.

Full Baruwa functionality is available from any member within a Baruwa cluster
and all cluster members have equal status. This allows you to provide round
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

Shared quarantine
-----------------

Since version 2.0.1 Baruwa supports shared quarantines using shared storage subsystems
like NFS, GlusterFS, OCFS, etc. With a shared quarantine, message operations are still
possible regardless of non availability of the node that processed the message.
To use a shared quarantine you need to:

* Mount the quarantine directory to the shared file subsystem
* Set the Baruwa configuration option ``ms.quarantine.shared`` to true
* Ensure that Exim generates unique message ids by setting the ``localhost_number`` option
* Ensure the ``celeryd`` and ``exim`` user ids are same for all nodes in the cluster 

Limitations
===========

.. note::
	This limitation is not present when using a shared quarantine.

Quarantines are node specific, so messages quarantined on a failed node will
not be accessible until the node is restored.
