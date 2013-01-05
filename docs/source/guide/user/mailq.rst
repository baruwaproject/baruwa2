
===========
Mail queues
===========

Messages that are yet to be processed are kept in the ``inbound queue``,
messages that have been processed but are yet to be delivered are
kept in the ``outbound queue``.

.. include:: ../../includes/mailq.rst

You can access these mail queues by clicking the numbers next to ``In:``
and ``Out:`` at the top of your screen

.. _managing_mailq:

Processing queued messages
===========================

Deliver a message in the outbound queue
---------------------------------------

Delivery only applies to messages that have already been processed by
Baruwa, that is why only messages in the outbound queue can be delivered.

To deliver a message:

1. Click the number next to ``Out:`` at the top of your screen
2. Select the message
3. Scroll to the bottom of the screen
4. Select ``Deliver``
5. Click the ``Process`` button

.. note::
	Delivery is only possible if the destination server is up and accepting
	mail.

Delete a queued message
-----------------------

1. Click the number next to ``In:`` or ``Out:`` at the top of your screen
2. Select the message
3. Scroll to the bottom of the screen
4. Select ``Delete``
5. Click the ``Process`` button

Bounce a queued message
-----------------------

1. Click the number next to ``In:`` or ``Out:`` at the top of your screen
2. Select the message
3. Scroll to the bottom of the screen
4. Select ``Bounce``
5. Click the ``Process`` button

Hold a queued message
---------------------

1. Click the number next to ``Out:`` at the top of your screen
2. Select the message
3. Scroll to the bottom of the screen
4. Select ``Hold``
5. Click the ``Process`` button

Preview a queued message
------------------------

1. Click the number next to ``In:`` or ``Out:`` at the top of your screen
2. Select the message
3. Click ``Preview message``
