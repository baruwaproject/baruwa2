==========
Baruwa 2.0
==========

Baruwa (swahili for letter or mail) is a web 2.0 MailScanner front-end.

It provides an easy to use interface for managing a Anti Spam system
built on the best of breed open source packages. It is used to perform
operations such as managing configurations, quarantine management,
bayesian learning, management of approved and banned sender lists,
monitoring the health of the services and a lot more.

Baruwa is implemented using web 2.0 features (AJAX) where deemed fit.
Baruwa has full support for i18n, enabling you to translate it into any
language of your choosing. Baruwa has already been translated into to
over `25 languages <https://www.transifex.com/projects/p/baruwa/>`_.

It includes reporting functionality with an easy to use query builder,
results can be displayed as message lists or graphed as colorful and
pretty interactive graphs.

Baruwa includes full text search functionality that allows you to find
information very fast and easily. Advanced searching options available
in leading web search engines are supported in Baruwa.

A Custom MailScanner module is provided for asynchronous logging of
messages to a PostgreSQL database with SQLite backup as well as
updating of the realtime search index.

Baruwa is open source software, written in Python/Perl using the Pylons
Framework and uses a PostgreSQL backend, it is released under the GPLv3
and is available for free download.

Features
========

	* AJAX support for most operations
	* Ultra fast full text search
	* Reporting with AJAX enabled query builder
	* I18n support, allows use of multiple languages
	* Signature management / Branding
	* Mail queue management and reporting
	* Message delivery/relay information
	* DKIM management
	* Reporting graphs
	* Emailed PDF reports
	* Audit trails
	* Archiving of old message logs
	* SQLite backup prevents data loss when DB is unavailable
	* MTA integration
	* Multi Tenancy
	* User profile aware approved/banned sender management
	* IP / network addresses supported in approved/banned list manager
	* SQL based MailScanner configuration management
	* System status information
	* IPv6 Support
	* Asynchronous MailScanner logging
	* Import and Export of User accounts and Domains
	* AD/Exchange integration to auto populate account and group information
	* Easy plug-in authentication to external authentication systems
	* AD/LDAP, POP3, IMAP, SMTP, RADIUS Authentication support
	* Tools for housekeeping tasks
	* Easy clustering of multiple servers
	* Works both with and without Javascript enabled

Installation
============
Baruwa can be installed using ``pip``, ``easy_install`` or from ``source``.

Using pip
---------
::

	pip install -U baruwa

Using easy_install
------------------
::

	easy_install -U baruwa

Using source
------------

Download the latest version of Baruwa 2.0 from http://pypi.python.org/pypi/baruwa/
::

	tar xjvf baruwa-0.0.0.tar.bz2
	cd baruwa-0.0.0
	python setup.py install

The last command must be executed as a privileged user if you are not currently
using a virtualenv.

Packages
========
Binary packages for Ubuntu/Debian and RHEL/SL/CENTOS are available from
`Baruwa Enterprise <https://www.baruwa.com>`_ 

Documentation
=============
Documentation is included in the docs directory of the tar ball and can also be
accessed `online <http://www.baruwa.org/docs/2.0/>`_

Support
=======

Community support
-----------------

You can get free and friendly support from the `list <http://lists.baruwa.org>`_

Commercial support
------------------

Paid for support from the `Developer <http://www.topdog.za.net>`_ or other
`companies that support baruwa <http://www.baruwa.org/support/>`_.


