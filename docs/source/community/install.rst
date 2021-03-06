.. _source_install:

==============================
Community Edition installation
==============================
.. include:: ../includes/source-note.rst

This is a full walkthrough of how to get Baruwa up and running.

Experienced `Pylons <http://www.pylonsproject.org/projects/pylons-framework/about>`_
users can check out the :ref:`install_overview` page for a (very) condensed version
of the instructions.

This installation guide assumes a basic familiarity with a \*nix shell. You
should be familiar with the concepts important to web development such as
databases, web servers, and file permissions.

You should be comfortable with running commands in a terminal, and the basics
like ``cd``, ``ls``, ``mkdir``, ``tar``, ``sudo``, etc.

Step 0: Preliminary Requirements
================================

Installation from source requires that you have a build environment as well as
various required libraries installed on your system.

Please refer to :ref:`source_requirements` to install them for your
specific OS.

Step 1: Setup a Python Virtual Environment
==========================================

**NOTE: Past this point, it will be assumed that all packages required in**
`Step 0: Preliminary Requirements`_ **are installed.**

If you haven't heard of them, `Virtual Environments <http://www.virtualenv.org/>`_
are a way to keep installations of multiple Python applications from
interfering with each other.

This means you can install Baruwa and all of its dependencies without
worrying about overwriting any existing versions of Python libraries.

The following commands create a virtual environment in a folder named ``px``
in the ``/home/baruwa`` directory as well as activate the virtual environment.

Create the /home/baruwa directory::

	mkdir -p /home/baruwa
   	cd /home/baruwa

Create a new virtual environment::

   virtualenv --no-site-packages --distribute px

Now, activate that virtual environment::

   source px/bin/activate


Now that you've activated the newly created virtual environment, any packages
you install will only be accessible when you've activated the environment.

**NOTE: Any time you want to work with Baruwa, you should activate the
virtual environment as we just did in the line above.**

Step 2: Install Python dependencies
===================================

A pip requirements file is provided with in the Baruwa source, you will use that
file to install all the required Python packages.

Set this environment variable to allow ``m2crypto`` to build on Linux::

	export SWIG_FEATURES="-cpperraswarn -includeall -D__`uname -m`__ -I/usr/include/openssl"
	
Download the requirements file::

	curl -O https://raw.github.com/akissa/baruwa2/2.0.1/requirements.txt
	
Install the required packages using pip::

	pip install -r requirements.txt

Install the sphinx search api module::

	curl https://sphinxsearch.googlecode.com/svn/trunk/api/sphinxapi.py -o \
		px/lib/python2.6/site-packages/sphinxapi.py

.. _apply_patches:

Apply required patches
----------------------

Download the required patches and apply them to the virtualenv::

	curl -O https://raw.github.com/akissa/baruwa2/2.0.1/extras/patches/repoze.who-friendly-form.patch
	curl -O https://raw.github.com/akissa/baruwa2/2.0.1/extras/patches/repoze-who-fix-auth_tkt-tokens.patch
	cd px/lib/python2.6/site-packages/repoze/who/plugins/
	patch -p3 -i /home/baruwa/repoze.who-friendly-form.patch
	patch -p4 -i /home/baruwa/repoze-who-fix-auth_tkt-tokens.patch
	cd -

If you are running **Centos/RHEL/SL** apply the eventlet subprocess patch which fixes
the :ref:`eventlet_subprocess` issue.

M2Crypto on Debian/Ubuntu issue
-------------------------------

Debian/Ubuntu users need to install ``M2Crypto`` from source because of :ref:`m2crypto_symbol`
issue that comes up when installed using ``pip``.
	

Step 3: Install and configure supporting packages
=================================================

Various packages need to be installed and configured to get a fully working anti spam
system.

Step 3a: PostgreSQL
-------------------

This is the database backend used by Baruwa to store data. The client as well as the
development libraries were already installed as preliminary dependencies to allow the
building of the pyscopy2 python module. You only have to install the server if you
are going to run the database on the system system as Baruwa.

For CentOS/RHEL/SL::

	yum install postgresql-server postgresql-plpython -y

For Debian/Ubuntu::

	sudo apt-get install postgresql postgresql-plpython -y

For FreeBSD::

	TODO:

Now that the PostgreSQL server is installed you need to initialize and start it

Centos/RHEL/SL::

	service postgresql initdb
	service postgresql start

For FreeBSD::

	TODO:

You now need to configure the authentication settings on your postgresql server,
edit your ``pg_hba.conf`` file and change the entries to the following.

.. sourcecode:: bash

	# TYPE  DATABASE    USER        CIDR-ADDRESS          METHOD
	local   all         postgres                          trust
	host    all         all         127.0.0.1/32          md5
	host    all         all         ::1/128               md5

CentOS/RHEL/SL::

	cat > /var/lib/pgsql/data/pg_hba.conf << 'EOF'
	# TYPE  DATABASE    USER        CIDR-ADDRESS          METHOD
	local   all         postgres                          trust
	host    all         all         127.0.0.1/32          md5
	host    all         all         ::1/128               md5
	EOF

Configure the server to use the ``UTC`` timezone as the default timezone::

	sed -e "s/^#timezone = \(.*\)$/timezone = 'UTC'/" -i /var/lib/pgsql/data/postgresql.conf
	
Restart the service for the configuration changes to take effect::

	service postgresql restart

Debian/Ubuntu::

	cat > /etc/postgresql/9.1/main/pg_hba.conf << 'EOF'
	# TYPE  DATABASE    USER        CIDR-ADDRESS          METHOD
	local   all         postgres                          trust
	host    all         all         127.0.0.1/32          md5
	host    all         all         ::1/128               md5
	EOF

Configure the server to use the ``UTC`` timezone as the default timezone::

	sed -e "s/^#timezone = \(.*\)$/timezone = 'UTC'/" -i /etc/postgresql/9.1/main/postgresql.conf

Restart the service for the configuration changes to take effect::

	sudo service postgresql restart

FreeBSD::

	TODO

With the server now started you can proceed to configuration. Here we will create
a database user account as well as a database.

We're going to assume that the database is called ``baruwa``, the postgresql
user is called ``baruwa``, and the password is ``verysecretpw``.


Create the database user::

	su - postgres -c "psql postgres -c \"CREATE ROLE baruwa WITH LOGIN PASSWORD 'verysecretpw';\""

Create the database::

	su - postgres -c 'createdb -E UTF8 -O baruwa -T template1 baruwa'

Baruwa uses functions written in the ``plpgsql`` and ``plpythonu`` procedural languages.
Enable these languages in the db::

	su - postgres -c "psql baruwa -c \"CREATE LANGUAGE plpgsql;\""
	su - postgres -c "psql baruwa -c \"CREATE LANGUAGE plpythonu;\""

Creation of functions written in ``plpythonu`` requires PostgreSQL admin user access.
So we create them in this step using the ``postgres`` admin account::

	curl -O https://raw.github.com/akissa/baruwa2/2.0.0/baruwa/config/sql/admin-functions.sql
	su - postgres -c 'psql baruwa -f /home/baruwa/admin-functions.sql'


Step 3b: RabbitMQ
-----------------

The RabbitMQ server is used as the message broker to handle the processing on
backend tasks such as releasing messages, reading queues and providing host
status information.

Run the following commands to install and start rabbitmq on your system.

CentOS/RHEL/SL::

	yum install rabbitmq-server -y
	service rabbitmq-server start

Debian/Ubuntu::

	sudo apt-get install rabbitmq-server -y

FreeBSD::

	TODO:

Here will will create a virtual host and a rabbitmq user to be used by Baruwa.

We're going to assume that the virtual host is called ``baruwa``, the rabbitmq
user is called ``baruwa``, and the password is ``mysecretpwd``.


Create the user account, the virtual host and give the user permissions on the
virtual host::

	rabbitmqctl add_user baruwa mysecretpwd
	rabbitmqctl add_vhost baruwa
	rabbitmqctl set_permissions -p baruwa baruwa ".*" ".*" ".*"

Remove the guest user::

	rabbitmqctl delete_user guest

Step 3c: Sphinx
---------------

The Sphinx search server provides fast indexed search results to queries submitted
via Baruwa.

Run the following commands to install and start sphinx on your system.

CentOS/RHEL/SL:

**You need to compile sphinx on your own with postgresql support**

Debian/Ubuntu::

	sudo apt-get install sphinxsearch -y

FreeBSD::

	TODO:

Copy the provided Sphinx configuration in place then start the sphinx server.


Download the supplied sample Sphinx configuration file::

	curl -O https://raw.github.com/akissa/baruwa2/2.0.0/extras/config/sphinx/sphinx.conf

Set the required database settings::

	sed -i -e 's:sql_host =:sql_host = 127.0.0.1:' \
		-e 's:sql_user =:sql_user = baruwa:' \
		-e 's:sql_pass =:sql_pass = verysecretpw:' \
		-e 's:sql_db =:sql_db = baruwa:' sphinx.conf

CentOS/RHEL/SL::

	cp sphinx.conf /etc/sphinx/
	service searchd start

Debian/Ubuntu::

	sudo sed -i -e 's:START=no:START=yes:' /etc/default/sphinxsearch
	sudo sed -i -e 's:/var/log/sphinx:/var/log/sphinxsearch:' \
		-e 's:/var/lib/sphinx:/var/lib/sphinxsearch:' sphinx.conf
	sudo cp sphinx.conf /etc/sphinxsearch/
	sudo service sphinxsearch start

FreeBSD::
	
	TODO:

Add a cronjob ``/etc/cron.hourly/baruwa-updateindex`` to update the sphinx indexes
every hour::

	cat > /etc/cron.hourly/baruwa-updateindex << 'EOF'
	#!/bin/bash
	#
	indexer auditlog lists domains accounts organizations --rotate &>/dev/null
	EOF

Make the cronjob executable::

	chmod +x /etc/cron.hourly/baruwa-updateindex

Step 3d: Memcached
------------------

Memcached is used to cache data and alleviate the load on the database backend
as well as store sessions.

CentOS/RHEL/SL::

	yum install memcached -y
	service memcached start

Debian/Ubuntu::

	sudo apt-get install memcached -y

FreeBSD::

	TODO

Step 3e: MailScanner
--------------------

MailScanner is the integrated engine that performs the various checks used to 
identify and classify spam and various threats.

Baruwa manages the MailScanner configuration by storing the configurations in
the PostgreSQL Database. MailScanner signatures can also be managed using
Baruwa for both domains and individual users.

  .. toctree::
    mailscanner

.. _baruwa_install:

Step 4: Install Baruwa
======================

With all the requirements in place you can now install Baruwa by running the following
command.

Install baruwa using pip::

	pip install baruwa

.. _baruwa_setup:

Step 5: Setup Baruwa
====================

You need to create a configuration file, then edit it to set the correct credentials.
The important settings that you need to set are the ``database and broker credentials``.

.. _baruwa_conf:

Step 5a: Create configuration files
-----------------------------------

Create the configuration file::

	paster make-config baruwa production.ini

Set the sqlalchemy database url::

	sed -i -e 's|baruwa:@127.0.0.1:5432/baruwa|baruwa:verysecretpw@127.0.0.1:5432/baruwa|' \
		production.ini

Set the broker password and enable the queues::

	sed -i -e 's:broker.password =:broker.password = mysecretpwd:' \
		-e "s:snowy.local:$(hostname):g" \
		-e 's:^#celery.queues:celery.queues:' production.ini

Create configuration directory and move the configuration files into it

CentOS/RHEL/SL::

	mkdir /etc/baruwa
	mv production.ini /etc/baruwa

Debian/Ubuntu::

	sudo mkdir /etc/baruwa
	sudo mv production.ini /etc/baruwa

FreeBSD::

	TODO

Check the configuration file and ensure that the ``baruwa.timezone`` option matches
the timezone configured on your server. Take time to review the other options to
ensure that they are correct for your setup.

.. _populate_db:

Step 5b: Populate the database
------------------------------

The creation of all database tables, addition of initial data and the creation of an
admin user is taken care of via this Pylons command::

   paster setup-app /etc/baruwa/production.ini

Next create the required directories and start the celeryd daemon.

Step 5c: Create the sphinx indexes
----------------------------------

The initial sphinx search indexes need to be created by running the command::

	indexer --all --rotate

Step 5d: Create the required directories
----------------------------------------

Create log, pid, locks, dkim, signatures, rules and data directories::

	mkdir -p /var/log/baruwa /var/run/baruwa /var/lib/baruwa/data/{cache,sessions,uploads} \
	/var/lock/baruwa /etc/MailScanner/baruwa/signatures /etc/MailScanner/baruwa/dkim \
	/etc/MailScanner/baruwa/rules

.. _start_celeryd:

Step 5e: Start the celery daemon
--------------------------------

Start the celeryd daemon::

	paster celeryd /etc/baruwa/production.ini -f /var/log/baruwa/celeryd.log &

Step 5f: Test using builtin server
----------------------------------

Now that Baruwa itself is installed and the basics are configured,
we can test it out using the Paste server. It's bundled with Pylons
so you have it already, simply run::

   paster serve --reload /etc/baruwa/production.ini

Now open http://localhost:5000/ to see how it works! You can try to login
with the username and password you provided when you populated the database.

If this produces errors then Baruwa or one of its dependencies is not
setup correctly. Please feel free to ask questions and submit solutions
via our `community list <http://lists.baruwa.org>`_. 

If all goes well and you do not have any errors, press ``CTRL-C`` to stop the
builtin server then stop the celeryd server by running ``fg`` the ``CTRL-C``.

With everything tested and working you cannot proceed to the production
deployment below.


Step 6: Production deployment
=============================

Step 6a: Celeryd production deployment
--------------------------------------

In :ref:`start_celeryd` you manually started celeryd on the command line,
in a production deployment you will want celeryd to startup automatically
on boot.

To enable this you need to install a startup script for your OS. 

  .. toctree::
   celeryd

.. _baruwa_deploy:

Step 6b: Baruwa production deployment
-------------------------------------

Baruwa is WSGI-based so there are many possible ways to deploy it.
The built in Paste server does a great job for development, but you
may want to run Baruwa from a more performant webserver.
Below are two methods you can use to deploy Baruwa:


Step 6b option1: Apache & mod_wsgi
----------------------------------
``mod_wsgi`` provides good performance for small deployments.

  .. toctree::
   apache-wsgi

Step 6b option2: NGINX & uwsgi
------------------------------

``uwsgi`` provides significant performance benefits including page speed
and reduced memory usage.

  .. toctree::
   nginx-uwsgi

.. _install_cronjobs:

Step 6c: Install cronjobs and sudo file
---------------------------------------

Baruwa needs to run some commands as the mail server user, like managing the
queue as well as reloading the mail server to pickup configuration changes.

Add the baruwa user to the exim group::

	usermod -G exim baruwa

Then create a custom sudo file ``/etc/sudoers.d/baruwa``

.. sourcecode:: bash

	Defaults:baruwa   !requiretty, visiblepw

	baruwa ALL=(exim) NOPASSWD: /usr/sbin/exim -C /etc/exim/exim_out.conf -M *, \
	        /usr/sbin/exim -C /etc/exim/exim_out.conf -Mf *, \
	        /usr/sbin/exim -C /etc/exim/exim_out.conf -Mrm *, \
	        /usr/sbin/exim -C /etc/exim/exim_out.conf -Mg *, \
	        /usr/sbin/exim -C /etc/exim/exim_out.conf -Mar *, \
	        /usr/sbin/exim -C /etc/exim/exim_out.conf -qff, \
			/usr/sbin/exim -Mrm *, \
			/usr/sbin/exim -Mg *, \
			/usr/sbin/exim -Mar *

	baruwa ALL = NOPASSWD: /bin/kill -s HUP *

Baruwa runs cronjobs to handle some background tasks such as sending reports,
pruning databases, updating indexes etc.

Create the cron file ``/etc/cron.d/baruwa`` with the following contents

.. sourcecode:: bash

	*/3 * * * * exim /home/baruwa/px/bin/paster update-queue-stats \
					/etc/baruwa/production.ini >/dev/null 2>&1
	0 * * * * baruwa /home/baruwa/px/bin/paster update-sa-rules \
					/etc/baruwa/production.ini >/dev/null 2>&1
	0 * * * * root /home/baruwa/px/bin/paster update-delta-index \
					--index messages --realtime /etc/baruwa/production.ini \
					>/dev/null 2>&1
	0 0 * * * baruwa /home/baruwa/px/bin/paster send-quarantine-reports \
					/etc/baruwa/production.ini >/dev/null 2>&1
	0 1 * * * baruwa /home/baruwa/px/bin/paster prune-database \
					/etc/baruwa/production.ini >/dev/null 2>&1
	9 1 * * * root /home/baruwa/px/bin/paster update-delta-index \
					--index archive /etc/baruwa/production.ini \
					>/dev/null 2>&1
	0 2 * * * baruwa /home/baruwa/px/bin/paster prune-quarantine \
					/etc/baruwa/production.ini >/dev/null 2>&1
	0 6 1 * * baruwa /home/baruwa/px/bin/paster send-pdf-reports \
					/etc/baruwa/production.ini >/dev/null 2>&1

Step 7: Getting help
====================
.. include:: ../includes/help.rst

Known Issues
============

.. _m2crypto_symbol:

ImportError: M2Crypto/__m2crypto.so: undefined symbol: SSLv2_method
-------------------------------------------------------------------

If you run across is issue (Ubuntu/Debian) you need to apply the patch
from Debian, then install M2Crypto manually.

The patch is included in the Baruwa patches directory, download, apply,
build and install::

	curl -O https://raw.github.com/akissa/baruwa2/master/extras/patches/0002-Disable-SSLv2_method.patch
	curl -O http://pypi.python.org/packages/source/M/M2Crypto/M2Crypto-0.21.1.tar.gz
	tar xzvf M2Crypto-0.21.1.tar.gz
	cd M2Crypto-0.21.1/
	patch -p1 -i ../0002-Disable-SSLv2_method.patch
	python setup.py install
	cd -

.. _eventlet_subprocess:

TypeError: wait() got an unexpected keyword argument 'timeout'
--------------------------------------------------------------

You need to apply a patch to eventlet to fix this issue::

	curl -O https://raw.github.com/akissa/baruwa2/2.0.0/extras/patches/subprocess_timeout.patch
	cd /home/baruwa/px/lib/python2.6/site-packages/
	patch -p1 -i /home/baruwa/subprocess_timeout.patch
	cd /home/baruwa