
========
Messages
========

Most Recent Messages
--------------------

When you login the default view you see is the most recent messages
for your account. By default the latest 50 messages are shown.

If you want to change the number of recent messages displayed you can
use the drop down select ``Show: items per page`` to do that.

The selected number will be displayed during your current session, when
you logout the number will reset to 50.

.. _full_message_listing:

Full message listing
--------------------

If you want to see more then the most recent messages you should,

1. Mouse over ``Messages``
2. Click ``Full message list``
3. Use the pagination links to see more messages.

.. _quarantine:

Quarantine
----------

If you want to see only quarantined messages,

1. Mouse over ``Messages``
2. Click ``Quarantine``
3. Use the pagination links to see more messages.

You can carry out message operations on several messages from within
this view. Refer to :ref:`bulk_ops` for details.

.. _archived_messages:

Archived messages
-----------------

If you want to see older archived messages,

1. Mouse over ``Messages``
2. Click ``Archive``
3. Use the pagination links to see more messages.

Message Details
---------------

If you want to see the details of any specific message click the link
to the message.

The following information is available.

* Message ID
* From Address
* To Address
* Subject
* Received date and time (Displayed in your timezone)
* Received by server (The server that received the message)
* Received from (The server that sent the message)
* Received via (Servers that processed this message, includes country information)
* Size
* Message headers
* Quarantined 
* Virus infected
* Prohibited file
* Other infection
* Spam checks information (Spam check results and rules used to make determination)
* Delivery information (Status of mail delivery to final destination)

If the message is quarantined you are able to ``preview``, ``release``, ``learn`` or
``delete`` the message. Refer to :ref:`message_operations` on how to do this.

You are also able to add the sender to an authorized or banned sender list from with
this view using ``email address``, ``domain name`` or ``IP address``. Refer to
:ref:`add_sender_to_list` on how to do this.

.. _message_operations:

Message operations
------------------

The Baruwa interface allows you to ``preview``, ``release``, ``learn`` or
``delete`` quarantined messages and authorize or ban senders of messages
using ``email address``, ``domain name`` or ``IP address``.

Previewing a quarantined message
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To preview a quarantined message,

1. Click the message link
2. Click ``Preview message``
3. Click ``Attachments to download any attachments``
4. Click ``Display images`` to display any remote images (This is not advisable)

Releasing a quarantined message
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To release a quarantined message,

1. Click the message link
2. Click ``Release message``
3. Check ``Release`` checkbox
4. Enter ``Alt recipients`` if you want to send the message to another email address
5. Click the ``Submit`` Button

Bayesian learning a message
~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can update the Bayes system by teaching it if a message is Spam or Not Spam.

1. Click the message link
2. Go to the bottom of the page
3. Check ``Bayesian Learn`` checkbox
4. Select ``Spam`` or ``Clean`` from the drop down
5. Click the ``Submit`` Button

Deleting a quarantined message
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can delete a message from the quarantine.

1. Click the message link
2. Go to the bottom of the page
3. Check ``Delete`` checkbox
4. Click the ``Submit`` Button

.. _add_sender_to_list:

To add the sender to a list
---------------------------

1. Click ``Add sender to list``
2. Select the type of list you want to add them to using the ``List type`` drop down
3. Check ``Add to aliases as well`` if you want it to apply to your aliases as well
4. Check ``Use IP address`` to use the ``IP address``
5. Check ``Use Domain`` to list the whole domain
6. Click the ``Add to list`` button

.. _bulk_ops:

Bulk Message Operations
-----------------------

It is possible to carry out message operations (``release``, ``learn`` or ``delete``)
on multiple messages at ago.

To do this.

1. Select the messages using the check box
2. Select the operations (``release``, ``learn`` or ``delete``) at the top 
3. Click the ``Process`` button
4. View the operations results

Filters
-------

Message filters are available on the :ref:`full_message_listing`, :ref:`quarantine`
and :ref:`archived_messages` pages.

Refer to :ref:`manage_filters` on how to manage these filters.


 