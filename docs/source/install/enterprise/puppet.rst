.. _auto_install:

=========================================
Automated Enterprise Edition installation
=========================================

.. include:: overview.rst

.. include:: requirements.rst

Step 2: Installation
--------------------

**CentOS/RHEL/SL**

Install puppet::

	yum install puppet -y

**Debian/Ubuntu**

Install puppet::

	apt-get install puppet -y

Download and install the puppet toaster from the baruwa.com website::

	curl -O https://www.baruwa.com/downloads/puppet-toaster-latest.tar.bz2
	tar xjvf puppet-toaster-latest.tar.bz2 -C /etc/puppet/

Create a puppet host manifest for your host by copying the provided
sample::

	cp /etc/puppet/manifests/toasters/baruwa/init.pp \
	/etc/puppet/manifests/toasters/baruwa/$(hostname).pp

Edit the manifest file and set the options to reflect the host you are
installing.

Make sure you change the following options


+--------------------------------+------------------------------+
| Option                         | Description                  |
+================================+==============================+
| **$pgsql_password**            | Postgresql admin password    |
+--------------------------------+------------------------------+
| **$baruwa_admin_user**         | Baruwa admin username        |
+--------------------------------+------------------------------+
| **$baruwa_admin_email**        | Baruwa admin user email      |
+--------------------------------+------------------------------+
| **$baruwa_admin_passwd**       | Baruwa admin user password   |                  
+--------------------------------+------------------------------+
| **$baruwa_pgsql_passwd**       | Baruwa Postgresql password   |
+--------------------------------+------------------------------+
| **$baruwa_timezone**           | Server Timezone              |
+--------------------------------+------------------------------+
| **$baruwa_session_secret**     | Session encryption key       |
+--------------------------------+------------------------------+
| **$baruwa_app_uuid**           | Baruwa application UUID      |
+--------------------------------+------------------------------+
| **$baruwa_rabbitmq_passwd**    | Baruwa RabbitMQ password     |
+--------------------------------+------------------------------+
| **$baruwa_quarantine_host_url**| Quarantine URL               |
+--------------------------------+------------------------------+
| **$baruwa_web_vhost**          | Baruwa virtual host name     |
+--------------------------------+------------------------------+
| **$baruwa_web_serveraliases**  | Baruwa server aliases        |
+--------------------------------+------------------------------+
| **$baruwa_mail_host**          | Mail server hostname         |
+--------------------------------+------------------------------+
| **$baruwa_bayes_pgsql_pass**   | Bayes Postgresql password    |
+--------------------------------+------------------------------+
| **$openssl_country_code**      | SSL Certificate country code |
+--------------------------------+------------------------------+
| **$openssl_ca_name**           | SSL CA name                  |
+--------------------------------+------------------------------+
| **$openssl_province_name**     | SSL Certificate province     |
+--------------------------------+------------------------------+
| **$openssl_city_name**         | SSL city name                |
+--------------------------------+------------------------------+
| **$openssl_org_name**          | SSL organization name        |
+--------------------------------+------------------------------+

**SSL Certificates**

If you have an SSL certificate that is issued by a recognized CA and would
like Baruwa to use it, install it prior to running puppet::

	mkdir -p /etc/pki/baruwa/{certs,private}

Create the file ``/etc/pki/baruwa/certs/$(hostname).pem`` with the contents
of your SSL certificate

Create the file ``/etc/pki/baruwa/private/$(hostname).key`` with the contents
of your SSL private key

Run puppet using the manifest file that you created. This will take some
time while it sets up your server. When the command finishes you will
have a fully working Baruwa installation::

	puppet -v /etc/puppet/manifests/toasters/baruwa/$(hostname).pp

.. note::
	If any of the tasks fails, rerun the above command.

Step 3: Finalize configuration
------------------------------

Now that the installation and setup are complete, you need to finalize the
setup by :ref:`add_scanning_node`, :ref:`add_organization`,
:ref:`add_domain` and :ref:`add_account`.

Review the :ref:`admin_guide` for other configuration and setup options
available.

Step 4: Getting help
--------------------
.. include:: help.rst
