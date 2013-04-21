
=====================================================
Centos/RHEL/SL Enterprise Edition Manual installation
=====================================================

.. note::
	Manual installations are for experienced system administrators who would
	like to fully customize their installations and intimately understand the
	various software packages used. Please use the :ref:`auto_install_centos`
	if in depth customization is not what you want or you are not conversant
	with all the packages used to create a fully functional Mail security
	system.

.. include:: overview.rst
.. include:: requirements-centos.rst

Step 2: Install and configure supporting packages
=================================================

Step 2a: PostgreSQL
-------------------

This is the database backend used by Baruwa to store data.
You only have to install the server if you are going to run
the database on the system system as Baruwa::

	yum install postgresql-server postgresql-plpython -y

We now need to set a password on the postgresql ``postgres`` admin account, we use
the password ``strongPgP4ss`` change this for your environment.::

	chown postgres.postgres /var/lib/pgsql
	echo "strongPgP4ss" > /tmp/ps
	su postgres -c "/usr/bin/initdb /var/lib/pgsql/data --auth='password' --pwfile=/tmp/ps -E UTF8"
	rm -rf /tmp/ps

You now need to configure the authentication settings on your postgresql server,
edit your ``pg_hba.conf`` file and change the entries to the following::

	cat > /var/lib/pgsql/data/pg_hba.conf << 'EOF'
	# TYPE  DATABASE    USER        CIDR-ADDRESS          METHOD
	local   all         all                               md5
	host    all         all         127.0.0.1/32          md5
	host    all         all         ::1/128               md5
	EOF

Configure the server to use the ``UTC`` timezone as the default timezone::

	sed -e "s/^#timezone = \(.*\)$/timezone = 'UTC'/" -i /var/lib/pgsql/data/postgresql.conf

Restart the service for the configuration changes to take effect::

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

Run the following commands to install and start RabbitMQ on your system.::

	yum install rabbitmq-server -y
	service rabbitmq-server start

Now create a virtual host and a RabbitMQ user to be used by Baruwa.

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

Run the following commands to install and start sphinx on your system::

	yum install sphinx

Set the required database settings::

	sed -i -e 's:sql_host =:sql_host = 127.0.0.1:' \
		-e 's:sql_user =:sql_user = baruwa:' \
		-e 's:sql_pass =:sql_pass = verysecretpw:' \
		-e 's:sql_db =:sql_db = baruwa:' /etc/sphinx/sphinx.conf

Start the Sphinx server::

	service searchd restart


Step 2d: Memcached
------------------

Memcached is used to cache data and alleviate the load on the database backend
as well as store sessions::

	yum install memcached -y
	service memcached start

Step 2e: MailScanner
--------------------

MailScanner is the integrated engine that performs the various checks used to 
identify and classify spam and various threats.

Baruwa manages the MailScanner configuration by storing the configurations in
the PostgreSQL Database. MailScanner signatures can also be managed using
Baruwa for both domains and individual users.

Install MailScanner::

	yum install mailscanner -y

Sample configuration files for MailScanner and exim are provided in the source
under `extras/config/exim <https://github.com/akissa/baruwa2/tree/2.0.0/extras/config/exim>`_ 
and `extras/config/mailscanner <https://github.com/akissa/baruwa2/tree/2.0.0/extras/config/mailscanner>`_.
Please review and reuse.

Step 2f: Nginx
--------------

Nginx is the web server available in Baruwa Enterprise. Install it by running::

	yum install nginx -y

Create the Baruwa Nginx configuration file ``/etc/nginx/conf.d/baruwa.conf``
with the following contents.

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
command::

	yum install baruwa -y

.. include:: common-manual.rst