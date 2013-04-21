Step 1: Installation requirements
=================================

You need a valid Baruwa enterprise subscription, which provides you with
a server entitlement as well as an activation key to activate the entitlement.

Enable the EPEL repository
--------------------------

The EPEL repository is a volunteer-based community effort from the
Fedora project to create a repository of high-quality add-on packages
for Red Hat Enterprise (RHEL) and its compatible spinoffs such as CentOS,
Oracle Enterprise Linux or Scientific Linux. You can find more details on
EPEL including how to add it to your host at
`http://fedoraproject.org/wiki/EPEL <http://fedoraproject.org/wiki/EPEL>`_
and `http://fedoraproject.org/wiki/EPEL/FAQ#howtouse <http://fedoraproject.org/wiki/EPEL/FAQ#howtouse>`_.

You need to enable this repo in order to access certain packages
that are required by Baruwa::

	rpm -Uvh http://download.fedoraproject.org/pub/epel/6/i386/epel-release-6-8.noarch.rpm

Install Spacewalk client packages
---------------------------------

Baruwa Enterprise Edition entitlements are managed by the Baruwa Network.
The Baruwa Network uses the Spacewalk server to manage entitlements.
In order to access the Baruwa Enterprise Edition repository you need to
install the Spacewalk client tools. These tools are provided by the
Spacewalk project via a yum repository which you need to enable::

	rpm -Uvh http://yum.spacewalkproject.org/1.9/RHEL/6/x86_64/spacewalk-client-repo-1.9-1.el6.noarch.rpm

Having enabled the Spacewalk repository you can now install the Spacewalk
client packages::

	yum install rhn-client-tools rhn-check rhn-setup rhnsd m2crypto yum-rhn-plugin -y

Install Baruwa signing keys
---------------------------

The packages in the Baruwa Centos/RHEL/SL enterprise repository are cryptographically
signed using GPG keys. The package containing these GPG keys needs to be manually
installed before continuing to the next step::

	rpm -Uvh https://www.baruwa.com/downloads/baruwa-enterprise-release-6-2.noarch.rpm
	rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-BARUWA-ENTERPRISE-6

Activate Entitlement
--------------------

The Baruwa Centos/RHEL/SL enterprise repository is available to subscribers
only. To install from this repo you need to activate the entitlement for the
server that you are installing.

The server entitlement ``activation key`` is emailed to you when you purchase a
subscription. Use the ``activation key`` to register your server with the
Baruwa Network using the command below::

	rhnreg_ks --serverUrl=https://bn.baruwa.com/XMLRPC --activationkey=<activation-key>
