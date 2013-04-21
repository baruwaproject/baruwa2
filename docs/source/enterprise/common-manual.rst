Step 4: Setup Baruwa
=====================

Step 4a: Create configuration files
-----------------------------------

Create the configuration file::

	paster make-config baruwa /etc/baruwa/production.ini

Set the sqlalchemy database url::

	sed -i -e 's|baruwa:@127.0.0.1:5432/baruwa|baruwa:verysecretpw@127.0.0.1:5432/baruwa|' \
		/etc/baruwa/production.ini

Set the broker password and enable the queues::

	sed -i -e 's:broker.password =:broker.password = mysecretpwd:' \
		-e "s:snowy.local:$(hostname):g" \
		-e 's:^#celery.queues:celery.queues:'/etc/baruwa/production.ini

Check the configuration file and ensure that the ``baruwa.timezone`` option matches
the timezone configured on your server. Take time to review the other options to
ensure that they are correct for your setup.

.. note::
	Don't use the ``@`` and ``:`` characters in the passwords or usernames

Step 4b: Populate the database
------------------------------

Creation of functions written in ``plpythonu`` requires PostgreSQL admin user access.
So we create them in this step using the ``postgres`` admin account::

	psql -U postgres baruwa -f /usr/lib/python2.6/site-packages/baruwa/config/sql/admin-functions.sql

The creation of all database tables, addition of initial data and the creation of an
admin user is taken care of via this Pylons command::

   paster setup-app /etc/baruwa/production.ini


Step 4c: Create the sphinx indexes
----------------------------------

The initial sphinx search indexes need to be created by running the command::

	indexer --all --rotate

Step 4d: Start the celery daemon
--------------------------------

Start the celeryd daemon::

	service baruwa start

Step 4e: Link uwsgi configuration
---------------------------------

Link the Baruwa configuration to the uwsgi configuration directory::

	ln -s /etc/baruwa/production.ini /etc/uwsgi
	service uwsgi restart

Step 5: Finalize configuration
==============================

Now that the installation and setup are complete, you need to finalize the
setup by :ref:`add_scanning_node`, :ref:`add_organization`,
:ref:`add_domain` and :ref:`add_account`.

Review the :ref:`admin_guide` for other configuration and setup options
available.

Step 6: Advanced options
========================

Baruwa Enterprise Edition supports clustering as well as customization using
themes. If you intend on using these features read the following topics

* :ref:`clustering`
* :ref:`themes`

Step 7: Getting help
====================
.. include:: help.rst

