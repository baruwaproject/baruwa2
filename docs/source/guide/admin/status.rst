=============
System Status
=============

System status gives you a dash board view of your Baruwa system or cluster.

The following information is provided:

* Global status
* Scanner node status
* Mail Queues
* Audit logs

.. _global_status:

Global status
=============

The global status dashboard gives you the status information for the whole
of your Baruwa system/cluster at a glance.

Day's processed message totals
------------------------------

* Number of messages processed
* Number of messages found to be clean
* Number of messages found to be High scoring spam
* Number of messages found to be Low scoring spam
* Number of messages found to be Virus infected
* Number of messages found to be Policy blocked
* Number of messages in the Inbound queues
* Number of messages in the Outbound queues

Graph of Day's processed message totals
---------------------------------------

A graphical view of the above information in a PIE chart graph.

Scanner node status
-------------------

The status of all the scanning nodes in this Baruwa cluster.

.. _scanner_node_status:

Scanner node status
===================

Provides the status of a specific scanning node, and allows you to pull
additional information via select commands.

The following status information is provided.

* Day's stats for the specific node
* Node Hardware status (``CPU``, ``Memory``, ``Disk``, ``Network``)
* System Network stats
* System software status (``Scanners``, ``MTA``, ``Anti Virus engine``)

Mail Queues
===========

.. include:: ../../includes/mailq.rst

Details on how to carry our the above actions can be found in the user
guide's :ref:`managing_mailq` section.

Audit logs
==========

Audit logs are provided for the interactions that users have with the
system. The following information is recorded.

* Date and Time
* Username
* Interaction information
* Baruwa Node hostname or IP address
* Users IP address
* Category

Interactions are classified under the following categories

* Read
* Create
* Auth
* Update

The Audit logs can be exported in both PDF and CSV formats for offline
usage.

The Audit logs are searchable, all full text search options are supported.
Tips on searching are available on the :ref:`search_tips` page.
