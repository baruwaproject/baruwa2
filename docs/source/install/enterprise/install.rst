
======================================
Manual Enterprise Edition installation
======================================

.. note::
	Manual installations are for experienced system administrators who would
	like to fully customize their installations and intimately understand the
	various software packages used. Please use the :ref:`auto_install` if
	in depth customization is not what you want or you are not conversant with
	all the packages used to create a fully functional Mail security system.

.. include:: overview.rst

.. include:: requirements.rst

.. _install_support_packages:

Step 2: Install and configure supporting packages
=================================================

Step 2a: PostgreSQL
-------------------

This is the database backend used by Baruwa to store data.
You only have to install the server if you are going to run
the database on the system system as Baruwa.

For CentOS/RHEL/SL::

	yum install postgresql-server postgresql-plpython -y

For Debian/Ubuntu::

	sudo apt-get install postgresql postgresql-plpython -y

We now need to set a password on the postgresql ``postgres`` admin account, we use
the password ``strongPgP4ss`` change this for your environment.

For CentOS/RHEL/SL::

	chown postgres.postgres /var/lib/pgsql
	echo "strongPgP4ss" > /tmp/ps
	su postgres -c "/usr/bin/initdb /var/lib/pgsql/data --auth='password' --pwfile=/tmp/ps -E UTF8"
	rm -rf /tmp/ps

For Debian/Ubuntu::

	echo "ALTER USER postgres WITH PASSWORD 'strongPgP4ss';" > /tmp/ps
	su postgres -c 'psql -f /tmp/ps'
	rm -f /tmp/ps

You now need to configure the authentication settings on your postgresql server,
edit your ``pg_hba.conf`` file and change the entries to the following.

.. sourcecode:: bash

	# TYPE  DATABASE    USER        CIDR-ADDRESS          METHOD
	local   all         all                               md5
	host    all         all         127.0.0.1/32          md5
	host    all         all         ::1/128               md5

CentOS/RHEL/SL::

	cat > /var/lib/pgsql/data/pg_hba.conf << 'EOF'
	# TYPE  DATABASE    USER        CIDR-ADDRESS          METHOD
	local   all         all                               md5
	host    all         all         127.0.0.1/32          md5
	host    all         all         ::1/128               md5
	EOF

	sed -e "s/^#timezone = \(.*\)$/timezone = 'UTC'/" -i /var/lib/pgsql/data/postgresql.conf

	# restart the service
	service postgresql restart

Debian/Ubuntu::

	cat > /etc/postgresql/9.1/main/pg_hba.conf << 'EOF'
	# TYPE  DATABASE    USER        CIDR-ADDRESS          METHOD
	local   all         all                               md5
	host    all         all         127.0.0.1/32          md5
	host    all         all         ::1/128               md5
	EOF

	sed -e "s/^#timezone = \(.*\)$/timezone = 'UTC'/" -i /etc/postgresql/9.1/main/postgresql.conf

	# restart the service
	service postgresql restart

With the server now started you can proceed to configuration. Here we will create
a Baruwa postgresql database user account as well as a database to store Baruwa data.

We're going to assume that the database is called ``baruwa``, the postgresql
user is called ``baruwa``, and the password is ``verysecretpw``.


Create the database user::

	psql -Upostgres postgres -c "CREATE ROLE baruwa WITH LOGIN PASSWORD 'verysecretpw';"

Create the database::

	createdb -U postgres -E UTF8 -O baruwa -T template1 baruwa

Baruwa uses functions written in the ``plpgsql`` and ``plpythonu`` procedural languages.
Enable these languages in the db::

	psql -U postgres baruwa -c "CREATE LANGUAGE plpgsql;"
	psql -U postgres baruwa -c "CREATE LANGUAGE plpythonu;"

Step 2b: RabbitMQ
-----------------

The RabbitMQ server is used as the message broker to handle the processing on
backend tasks such as releasing messages, reading queues and providing host
status information.

Run the following commands to install and start RabbitMQ on your system.

CentOS/RHEL/SL::

	yum install rabbitmq-server -y
	service rabbitmq-server start

Debian/Ubuntu::

	apt-get install rabbitmq-server -y

Here will will create a virtual host and a RabbitMQ user to be used by Baruwa.

We're going to assume that the virtual host is called ``baruwa``, the RabbitMQ
user is called ``baruwa``, and the password is ``mysecretpwd``.


Create the user account, the virtual host and give the user permissions on the
virtual host::

	rabbitmqctl add_user baruwa mysecretpwd
	rabbitmqctl add_vhost baruwa
	rabbitmqctl set_permissions -p baruwa baruwa ".*" ".*" ".*"

Remove the guest user::

	rabbitmqctl delete_user guest

Step 2c: Sphinx
---------------

The Sphinx search server provides fast indexed search results to queries submitted
via Baruwa.

Run the following commands to install and start sphinx on your system.

CentOS/RHEL/SL::

	yum install sphinx

Debian/Ubuntu::

	apt-get install sphinxsearch -y

Set the required database settings

CentOS/RHEL/SL::

	sed -i -e 's:sql_host =:sql_host = 127.0.0.1:' \
		-e 's:sql_user =:sql_user = baruwa:' \
		-e 's:sql_pass =:sql_pass = verysecretpw:' \
		-e 's:sql_db =:sql_db = baruwa:' /etc/sphinx/sphinx.conf

Debian/Ubuntu::

	sed -i -e 's:sql_host =:sql_host = 127.0.0.1:' \
		-e 's:sql_user =:sql_user = baruwa:' \
		-e 's:sql_pass =:sql_pass = verysecretpw:' \
		-e 's:sql_db =:sql_db = baruwa:' /etc/sphinxsearch/sphinx.conf
	sed -i -e 's:START=no:START=yes:' /etc/default/sphinxsearch
	sed -i -e 's:/var/log/sphinx:/var/log/sphinxsearch:' \
		-e 's:/var/lib/sphinx:/var/lib/sphinxsearch:' /etc/sphinxsearch/sphinx.conf

Start the Sphinx server.

CentOS/RHEL/SL::

	service searchd restart

Debian/Ubuntu::

	service sphinxsearch restart


Step 2d: Memcached
------------------

Memcached is used to cache data and alleviate the load on the database backend
as well as store sessions.

CentOS/RHEL/SL::

	yum install memcached -y
	service memcached start

Debian/Ubuntu::

	apt-get install memcached -y

Step 2e: MailScanner
--------------------

MailScanner is the integrated engine that performs the various checks used to 
identify and classify spam and various threats.

Baruwa manages the MailScanner configuration by storing the configurations in
the PostgreSQL Database. MailScanner signatures can also be managed using
Baruwa for both domains and individual users.

Install MailScanner

CentOS/RHEL/SL::

	yum install mailscanner -y

Debian/Ubuntu::

	apt-get install mailscanner -y

Sample configuration files for MailScanner and exim are provided in the source
under `extras/config/exim <https://github.com/akissa/baruwa2/tree/2.0.0/extras/config/exim>`_ 
and `extras/config/mailscanner <https://github.com/akissa/baruwa2/tree/2.0.0/extras/config/mailscanner>`_.
Please review and reuse.

Step 2f: Nginx
--------------

Nginx is the web server available in Baruwa Enterprise. To install run

CentOS/RHEL/SL::

	yum install nginx -y

Debian/Ubuntu::

	apt-get install nginx -y

Create the Baruwa Nginx configuration file ``/etc/nginx/sites-available/baruwa`` for
Ubuntu/Debian and ``/etc/nginx/conf.d/baruwa.conf`` with the following contents.

.. sourcecode:: nginx

	# -*- coding: utf-8 -*-
	# Baruwa - Web 2.0 MailScanner front-end.
	# Copyright (C) 2010-2012  Andrew Colin Kissa <andrew@topdog.za.net>
	# vim: ai ts=4 sts=4 et sw=4
	upstream baruwacluster {
	    ip_hash;
	    server unix:///var/run/baruwa/baruwa.sock;
	}

	server {
	        listen [::]:80;
	        server_name _;
	        access_log /var/log/nginx/baruwa-access.log combined;
	        error_log /var/log/nginx/baruwa-error.log;
	        charset utf-8;
	        keepalive_requests    50;
	        keepalive_timeout     300 300;
	        server_tokens off;
	        root /usr/lib/python2.6/site-packages/baruwa/public;
	        index index.html index.htm;
	        client_max_body_size 25M;
	        location ~*/(imgs|js|css)/ {
	          root /usr/lib/python2.6/site-packages/baruwa/public;
	          expires max;
	          add_header Cache-Control "public";
	          break;
	        }
	        location = /favicon.ico {
	          root /usr/lib/python2.6/site-packages/baruwa/public/imgs;
	          expires max;
	          add_header Cache-Control "public";
	          break;
	        }
	        location / {
	          uwsgi_pass baruwacluster;
	          include uwsgi_params;
	          uwsgi_param SCRIPT_NAME '';
	          uwsgi_param UWSGI_SCHEME $scheme;
	        }
	}

Start the Nginx service::

	service nginx restart


Step 3: Install Baruwa
======================

With all the requirements in place you can now install Baruwa by running the following
command.

CentOS/RHEL/SL::

	yum install baruwa -y

Debian/Ubuntu::

	apt-get install baruwa -y

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
So we create them in this step using the ``postgres`` admin account

CentOS/RHEL/SL::

	psql -U postgres baruwa -f /usr/lib/python2.6/site-packages/baruwa/config/sql/admin-functions.sql

Debian/Ubuntu::

	psql -U postgres baruwa -f /usr/share/pyshared/baruwa/config/sql/admin-functions.sql

The creation of all database tables, addition of initial data and the creation of an
admin user is taken care of via this Pylons command::

   paster setup-app /etc/baruwa/production.ini


Step 4c: Create the sphinx indexes
----------------------------------

The initial sphinx search indexes need to be created by running the command::

	indexer --all --rotate

Step 4e: Start the celery daemon
--------------------------------

Start the celeryd daemon::

	service baruwa start

Step 5: Finalize configuration
------------------------------

Now that the installation and setup are complete, you need to finalize the
setup by :ref:`add_scanning_node`, :ref:`add_organization`,
:ref:`add_domain` and :ref:`add_account`.

Review the :ref:`admin_guide` for other configuration and setup options
available.

Step 6: Getting help
====================
.. include:: help.rst