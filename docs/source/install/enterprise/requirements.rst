Step 1: Installation requirements
=================================

You need a valid Baruwa enterprise subscription for the server as well as the
private key and server certificate.

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

	rpm -Uvh https://www.baruwa.com/downloads/baruwa-enterprise-release-6-1.noarch.rpm

Install Baruwa enterprise server certificate and key
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install the certificate that you received when you purchased your server subscription.
The certificate needs to be installed to ``/etc/pki/baruwa-enterprise/client.pem``.

Install the private key that you created in :ref:`enterprise_pk` and used to
:ref:`enterprise_csr` to ``/etc/pki/baruwa-enterprise/client.key``

Proceed to :ref:`auto_install_step2`

Step 1b: Installation requirements for Debian/Ubuntu
----------------------------------------------------

Baruwa uses packages from only the main and universe repos, you should disable
the other repos such as the multiverse and backports repos.

Enable Baruwa enterprise repo
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Baruwa Debian/Ubuntu enterprise repository is available to subscribers
only. To install from this repo you need to enable the repo::

	curl -O https://www.baruwa.com/downloads/baruwa-enterprise-keyring_0.1-1_all.deb
	dpkg -i baruwa-enterprise-keyring_0.1-1_all.deb

Install Baruwa enterprise server certificate and key
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install the certificate that you received when you purchased your server subscription.
The certificate needs to be installed to ``/etc/apt/certs/baruwa-enterprise/client.pem``.

Install the private key that you created in :ref:`enterprise_pk` and used to
:ref:`enterprise_csr` to ``/etc/apt/certs/baruwa-enterprise/client.key``

Set the hostname
~~~~~~~~~~~~~~~~~

The debian/ubuntu installer does not set the full host name, you need to
manually set the full hostname by running the following commands. Be sure
to change ``host.example.com`` to your actual hostname::

	cat > /etc/hostname << 'EOF'
	host.example.com
	EOF
	hostname host.example.com

Proceed to :ref:`auto_install_step2`
