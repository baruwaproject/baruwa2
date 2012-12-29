
=========================================
Automated Enterprise Edition installation
=========================================

Overview
========

Step 1: Installation requirements
=================================

Step 1a: Installation requirements for CentOS/RHEL/SL
-----------------------------------------------------

Install EPEL
~~~~~~~~~~~~

The EPEL repository is a volunteer-based community effort from the
Fedora project to create a repository of high-quality add-on packages
for Red Hat Enterprise (RHEL) and its compatible spinoffs such as CentOS,
Oracle Enterprise Linux or Scientific Linux. You can find more details on
EPEL including how to add it to your host at
`http://fedoraproject.org/wiki/EPEL <http://fedoraproject.org/wiki/EPEL>`_
and `http://fedoraproject.org/wiki/EPEL/FAQ#howtouse <http://fedoraproject.org/wiki/EPEL/FAQ#howtouse>`_.

You need to install this repo in order to access certain packages
that are required by Baruwa::

	rpm -Uvh http://download.fedoraproject.org/pub/epel/6/i386/epel-release-6-8.noarch.rpm

Enable Baruwa enterprise repo
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Baruwa Centos/RHEL/SL enterprise repository is available to subscribers
only. To install from this repo you need to enable the repo::

	rpm -Uvh http://enterprise.baruwa.com/el6/i386/baruwa-enterprise-6-0.noarch.rpm

Step 1b: Installation requirements for Debian/Ubuntu
----------------------------------------------------

Baruwa uses packages from only the main and universe repos, you should disable
the other repos such as the multiverse and backports repos.

Enable Baruwa enterprise repo
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Baruwa Debian/Ubuntu enterprise repository is available to subscribers
only. To install from this repo you need to enable the repo::

	wget xxxx

The debian/ubuntu installer does not set the full host name, you need to
manually set the full hostname by running the following commands. Be sure
to change ``host.example.com`` to your actual hostname::

	cat > /etc/hostname << 'EOF'
	host.example.com
	EOF
	hostname host.example.com

Step 2: Installation
--------------------

**CentOS/RHEL/SL**

Install puppet::

	yum install puppet -y

**Debian/Ubuntu**

Install puppet::

	apt-get install puppet -y

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
setup by creating settings, adding domains and creating accounts.

Step 4: Getting help
--------------------
.. include:: ../../includes/help.rst
