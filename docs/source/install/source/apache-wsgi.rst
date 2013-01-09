
============================
Apache & mod_wsgi Deployment
============================

**NOTE 1:** If you're administrating your own system and looking for pointers on how
to optimize and manage your mod_wsgi installation, check out the developer's site;
the documentation is verbose, but very complete: `mod_wsgi main site
<http://code.google.com/p/modwsgi/wiki/InstallationInstructions>`_.

Components
==========

The following five components are involved in getting web requests through to
Baruwa with this setup.

``Apache``
   the web server

``mod_wsgi``
   Apache module that lets Apache host WSGI enabled Python applications

``baruwa.conf``
   Your apache configuration; tells mod_wsgi how to run your app

``baruwa.wsgi``
   The script that runs Baruwa as a WSGI application

``baruwa``
   the reason we're here!

Installation
============

Install the required packages using the following commands:

CentOS/RHEL/SL::

	yum install httpd mod_wsgi -y

Debian/Ubuntu::

	sudo apt-get install libapache2-mod-wsgi apache2-mpm-worker -y

FreeBSD::

	TODO

Configuration
=============

.. _apache_baruwa_conf:

Baruwa configuration
--------------------

Ensure that you have already created a ``production.ini`` file as outlined
in :ref:`baruwa_conf`

.. _apache_modwsgi_conf:

Mod_wsgi configuration
----------------------

Create the template directory ``/var/lib/baruwa/data/templates`` and set the
correct ownership on the template, sessions, uploads and cache directories::

	mkdir /var/lib/baruwa/data/templates

CentOS/RHEL/SL::

	chown apache.apache -R /var/lib/baruwa/data/cache
	chown apache.apache -R /var/lib/baruwa/data/uploads
	chown apache.apache -R /var/lib/baruwa/data/templates
	chown apache.apache -R /var/lib/baruwa/data/sessions

Debian/Ubuntu::

	chown www-data.www-data -R /var/lib/baruwa/data/cache
	chown www-data.www-data -R /var/lib/baruwa/data/uploads
	chown www-data.www-data -R /var/lib/baruwa/data/templates
	chown www-data.www-data -R /var/lib/baruwa/data/sessions

FreeBSD::

	TODO

A sample configuration file is provided in the source with the contents below,
you will modify and use this sample configuration file.

.. sourcecode:: apacheconf

	# -*- coding: utf-8 -*-
	# Baruwa - Web 2.0 MailScanner front-end.
	# Copyright (C) 2010-2012  Andrew Colin Kissa <andrew@topdog.za.net>
	# vim: ai ts=4 sts=4 et sw=4

	WSGIPythonWarnings ignore::DeprecationWarning::
	WSGISocketPrefix /var/run/httpd
	#WSGIPythonHome /home/baruwa/px
	WSGIPythonPath /home/baruwa/px/lib/python2.6/site-packages
	<VirtualHost *:80>
	        Alias /favicon.ico /home/baruwa/px/lib/python2.6/site-packages/baruwa/public/imgs/favicon.ico
	        Alias /imgs/ /home/baruwa/px/lib/python2.6/site-packages/baruwa/public/imgs/
	        Alias /js/ /home/baruwa/px/lib/python2.6/site-packages/baruwa/public/js/
	        Alias /css/ /home/baruwa/px/lib/python2.6/site-packages/baruwa/public/css/

	        # Make all the static content accessible
	        <Directory /home/baruwa/px/lib/python2.6/baruwa/public/*>
	            Order allow,deny
	            Allow from all
	            Options -Indexes
	        </Directory>
	        #WSGIDaemonProcess baruwa threads=10 display-name=baruwa-wsgi \
	        #    python-path=/home/baruwa/px/lib/python2.6/site-packages \
	        #    python-eggs=/var/tmp
	        #WSGIProcessGroup baruwa

	        WSGIScriptAlias / /home/baruwa/px/lib/python2.6/site-packages/baruwa/baruwa.wsgi

	    # change to your hostname
	    ServerName ms.home.topdog-software.com

	    <Directory /home/baruwa/px/lib/python2.4/site-packages/baruwa>
	        Order deny,allow
	        Allow from all
	    </Directory>
	    ErrorLog logs/baruwa-error_log
	    CustomLog logs/baruwa-access_log common
	</VirtualHost>

Download the provided sample configuration file::

	curl -O https://raw.github.com/akissa/baruwa2/2.0.0/extras/config/mod_wsgi/apache.conf

If system hostname is not the virtual host you want to use then change it
below to the actual name that you want to use for the baruwa virtual host

CentOS/RHEL/SL::

	# install the configuration file
	mv apache.conf /etc/httpd/conf.d/baruwa.conf
	service httpd restart

Debian/Ubuntu::

	sed -i -e "s:/var/run/httpd:/var/run/apache2:" \
		-e "s:ms.home.topdog-software.com:$(hostname -f):" \
		-e "s:logs/:/var/log/apache2/:g" apache.conf

	# install the configuration file
	sudo mv apache.conf /etc/apache2/sites-available/baruwa

	# enable the baruwa virtual host
	sudo a2ensite baruwa

	# reload the service
	sudo service apache2 reload

FreeBSD::

	TODO

.. include:: ../../includes/finalize.rst