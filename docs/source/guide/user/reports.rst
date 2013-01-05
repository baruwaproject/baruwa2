
=======
Reports
=======

The reports view allows you to run a set of predefined reports.
The following reports are available.

Available reports
-----------------

* Top Senders by Quantity
* Top Senders by Volume
* Top Sender Domains by Quantity
* Top Sender Domains by Volume
* Spam Score Distribution
* Top Mail hosts
* Top Recipients by Quantity
* Top Recipients by Volume
* Message Totals

You can use ``filters`` to filter the results available in your
report. These ``filters`` can be saved for later reuse. Refer to
:ref:`manage_filters` for details.

Reports are exportable, and can be exported as PDF or CSV. Refer
to :ref:`export_report` for details on how to export a report.

.. _export_report:

Export report
-------------

Export report to PDF
~~~~~~~~~~~~~~~~~~~~

1. Click report link
2. Click ``Download PDF``

Export report to CSV
~~~~~~~~~~~~~~~~~~~~

1. Click report link
2. Click ``Download CSV``

.. _manage_filters:

Manage Filters
--------------

A filter rule consists of one message property and one condition.
If the message matches the property and condition it is selected.

Filter properties
~~~~~~~~~~~~~~~~~

The following properties are available to filter messages on.

* Message ID
* Message size
* From Address
* From Domain
* To Address
* To Domain
* Subject
* Received from
* Was scanned
* Is Spam
* Is Definite spam
* Is RBL listed
* Is approved sender
* Is banned sender
* Spam score
* Spam report
* Is virus infected
* Is name infected
* Is other infected
* Date
* Time
* Headers
* Is quarantined
* Processed by host

Filter conditions
~~~~~~~~~~~~~~~~~

Different properties support different conditions. The conditions
supported by a specific property will automatically be selected
when you select the property.

The following conditions are available.

* is equal to
* is not equal to
* is greater than
* is less than
* contains
* does not contain
* matches regex
* does not match regex
* is null
* is not null
* is true
* is false

Setting Up Filter Rules
~~~~~~~~~~~~~~~~~~~~~~~

1. Go to the ``Reports`` page Or within the :ref:`full_message_listing`,
   :ref:`quarantine` and :ref:`archived_messages` pages.
2. Select the property from the first drop down menu
3. Select the condition
4. Enter condition text if the condition requires one
5. Click ``Add filter``

Saving Filter Rules
~~~~~~~~~~~~~~~~~~~

1. Go to the ``Reports`` page
2. Select the filter rule under ``Active Filter(s)``
3. Click ``Save``

Deleting a saved Filter Rule
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Go to the ``Reports`` page
2. Select the filter rule under ``Saved Filter(s)``
3. Click ``Delete``
