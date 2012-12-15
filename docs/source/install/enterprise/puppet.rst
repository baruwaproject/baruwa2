
=========================================
Automated Enterprise Edition installation
=========================================

Overview
========

Step 1: Installation requirements
=================================

Install EPEL
------------

The EPEL repo provides packages which are in Fedora but no yet included in
RHEL/SL/CENTOS. More information about this repository can be 
found at `EPEL <http://fedoraproject.org/wiki/EPEL/FAQ>`_

You need to install this repo in order to access certain packages
that are required by Baruwa::

	rpm -Uvh http://download.fedoraproject.org/pub/epel/6/i386/epel-release-6-7.noarch.rpm

Enable Baruwa enterprise repo
-----------------------------

A Baruwa RHEL/SL/Centos repo is now available at http://repo.baruwa.org/
To install from this repo you need to enable the repo::

	rpm -Uvh http://repo.baruwa.org/el6/i386/baruwa-release-6-0.noarch.rpm

Step 2: Installation
--------------------

Install puppet::

	yum install puppet -y

Create a puppet host manifest for your host by copying the provided
sample::

	cp /etc/puppet/manifests/toasters/baruwa/init.pp \
	/etc/puppet/manifests/toasters/baruwa/$(hostname).pp

Edit the manifest file and set the options to reflect the host you are
installing.

Run puppet using the manifest file that you created. This will take some
time while it sets up your server. When the command finishes you will
have a fully working Baruwa installation::

	puppet -v /etc/puppet/manifests/toasters/baruwa/$(hostname).pp

Step 3: Getting help
--------------------
.. include:: ../../includes/help.rst
