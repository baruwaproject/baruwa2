
========================
NGINX & uWSGI Deployment
========================

**NOTE 1:** If you're administrating your own system and looking for pointers on how
to optimize and manage uWSGI or NGINX installations, check out the developer's site.

`uWSGI main site
<http://projects.unbit.it/uwsgi/>`_.
You can find example configurations as well as the official documentation on uWSGI here.

`uWSGI Mailing List
<http://lists.unbit.it/cgi-bin/mailman/listinfo/uwsgi>`_.
uWSGI also has a fantastic mailing list where the author contributes daily, and
is always willing to help out new users try to work through their issues.

`NGINX main site
<http://wiki.nginx.org>`_.
This is the main NGINX Wiki that where you can find the full documentation for NGINX,
all NGINX modules as well as many recipes and tips for configuring NGINX.

Components
==========
The following five components are involved in getting web requests through to
Baruwa with this setup.

``NGINX``
   the web server

``uWSGI``
   WSGI application container that serves Baruwa

``baruwa.conf``
   Your nginx configuration file.

``production.ini``
   The Baruwa deployment file for your production server.

``baruwa``
   the reason we're here!

Installation
============

Install the required packages using the following commands:

CentOS/RHEL/SL::

	yum install nginx

**The recommended repositories for CentOS/RHEL/SL do not provide uwsgi at the
moment you need to build it from source**

Debian/Ubuntu::

	sudo apt-get install uwsgi uwsgi-plugin-python nginx

FreeBSD::

	TODO

Configuration
=============

Baruwa Configuration
--------------------

**NOTE 1:** You should have already created a ``production.ini`` file as
outlined in :ref:`baruwa_conf`

uWSGI Configuration
-------------------

The first thing you will want to do is to edit the [uwsgi] section of your
production.ini file. This section will contain various parameters for the uWSGI
server and will automatically load your application when NGINX passes requests
over to it. You need to add ``home = /home/baruwa/px`` to the existing options:

.. sourcecode:: ini

    [uwsgi]
    socket = /var/run/baruwa/baruwa.sock
    master = true
    processes = 5
    uid = baruwa
    gid = baruwa
    daemonize = /var/log/uwsgi/uwsgi-baruwa.log
    home = /home/baruwa/px

``socket:`` uWSGI will create a unix socket at this location on your system
that will listen for incoming requests. You can also use a TCP socket, but if
you are running NGINX on the same server as uWSGI, a standard unix socket will
be much faster. This socket name will be used again in your NGINX configuration
to pass requests into uWSGI.

``master:`` Enables uWSGI master process manager. You should be enabling this
unless you have a good reason not to.

``processes:`` The number of uWSGI worker processes to spawn.

``home:`` This defines the virtual environment to use and will allow uWSGI
to correctly find your baruwa installation. If you get errors about baruwa not
loading, check that this setting is correct first.

``daemonize:`` Run uWSGI in daemon mode, and log all data to the file specified.

Create the template directory ``/var/lib/baruwa/data/templates`` and set the
correct ownership on the template, sessions, uploads and cache directories::

	mkdir /var/lib/baruwa/data/templates
	chown baruwa.baruwa -R /var/lib/baruwa/data/cache
	chown baruwa.baruwa -R /var/lib/baruwa/data/uploads
	chown baruwa.baruwa -R /var/lib/baruwa/data/templates
	chown baruwa.baruwa -R /var/lib/baruwa/data/sessions

Now that you have configured uWSGI, you can point to your ini file and launch uWSGI
like this:

CentOS/RHEL/SL::

	uwsgi --ini-paste /etc/baruwa/production.ini

Debian/Ubuntu::

	sudo ln -s /etc/baruwa/production.ini /etc/uwsgi/apps-enabled
	sudo service uwsgi restart

FreeBSD::

	TODO

If everything went well uWSGI will now be listening on the unix socket you
specified above. Of course you still need to tell NGINX how to talk to uWSGI so
let's configure that now.

NGINX Configuration
-------------------

A sample configuration file is provided in the source with the contents below,
you will modify and use this sample configuration file:

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
	        server_name ms.home.topdog-software.com;
	        access_log /var/log/nginx/baruwa-access.log combined;
	        error_log /var/log/nginx/baruwa-error.log;
	        charset utf-8;
	            keepalive_requests    50;
	        keepalive_timeout     300 300;
	        server_tokens off;
	        root /home/baruwa/px/lib/python2.6/site-packages/baruwa/public;
	        index index.html index.htm;
	        client_max_body_size 25M;
	        location ~*/(imgs|js|css)/ {
	          root /home/baruwa/px/lib/python2.6/site-packages/baruwa/public;
	          expires max;
	          add_header Cache-Control "public";
	          break;
	        }
	        location = /favicon.ico {
	          root /home/baruwa/px/lib/python2.6/site-packages/baruwa/public/imgs;
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

Download the provided sample configuration file::

	curl -O https://raw.github.com/akissa/baruwa2/2.0.0/extras/config/uwsgi/nginx.conf

Install the configuration file:

CentOS/RHEL/SL::

	mv nginx.conf /etc/nginx/conf.d/baruwa.conf

Debian/Ubuntu::

	sudo mv nginx.conf /etc/nginx/sites-available/baruwa
	sudo ln -s /etc/nginx/sites-available/baruwa \
		/etc/nginx/sites-enabled/baruwa

FreeBSD::

	TODO

At this point you can start your NGINX server and then proceed to finalize
setup!

CentOS/RHEL/SL::

	service nginx restart

Debian/Ubuntu::

	sudo service nginx restart

FreeBSD::

	TODO

.. include:: ../includes/finalize.rst

