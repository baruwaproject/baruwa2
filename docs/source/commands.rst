
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

	paster prunequarantine /path/to/config.ini

Deletes quarantined files older than ``ms.quarantine.days_to_keep``.
This is set in the ``/path/to/config.ini`` file

Quarantine reports
------------------
::

	paster send-quarantine-reports /path/to/config.ini

Generates an email report of the quarantined messages for the past 24 hours,
for each user that has quarantine report enabled.

Database maintenance
--------------------
::

	paster prunedb /path/to/config.ini

Deletes records older than 30 days from the messages table of the database, and
archives them to the archive table.

Spamassassin rule description updates
-------------------------------------
::

	paster update-sa-rules /path/to/config.ini

Updates the Spamassassin rule descriptions in the database.

PDF reports
-----------
::

	paster send-pdf-reports /path/to/config.ini

Sends PDF reports by email.

Mail queue Stats updates
------------------------
::

	paster update-queue-stats /path/to/config.ini

Query the inbound and outbound queues and write stats to the database.