=============
System Status
=============

System status gives you a dash board view of your Baruwa system or cluster.

The following information is provided:

* Global status
* Scanner node status
* Mail Queues
* Audit logs

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

