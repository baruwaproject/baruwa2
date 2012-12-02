
==================
Batteries included
==================

Baruwa provides custom paster commands to enable scripting of house
keeping tasks such as quarantine management and Database maintenance.

Command options and help
------------------------

These commands may take options to get details on the supported options run::

	paster baruwa

Quarantine management
---------------------
::

	paster prunequarantine /etc/baruwa/production.ini

Deletes quarantined files older than ``ms.quarantine.days_to_keep``.
This is set in the ``/etc/baruwa/production.ini`` file

Quarantine reports
------------------
::

	paster send-quarantine-reports /etc/baruwa/production.ini

Generates an email report of the quarantined messages for the past 24 hours,
for each user that has quarantine report enabled.

Database maintenance
--------------------
::

	paster prunedb /etc/baruwa/production.ini

Deletes records older than 30 days from the messages table of the database, and
archives them to the archive table.

Spamassassin rule description updates
-------------------------------------
::

	paster update-sa-rules /etc/baruwa/production.ini

Updates the Spamassassin rule descriptions in the database.

PDF reports
-----------
::

	paster send-pdf-reports /etc/baruwa/production.ini

Sends PDF reports by email.

Mail queue Stats updates
------------------------
::

	paster update-queue-stats /etc/baruwa/production.ini

Query the inbound and outbound queues and write stats to the database.

Delta search index updates
--------------------------
::

	paster update-delta-index --index messages --realtime /etc/baruwa/production.ini
	paster update-delta-index --index archive /etc/baruwa/production.ini

The ``messages`` and ``archive`` index have deltas to ensure that indexing is efficient
the above commands merge the delta index with the main index and remove id's from
the realtime index that have been indexed to disk indexes.

The ``messages`` index has a real time index while ``archive`` does not.
