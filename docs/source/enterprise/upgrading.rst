=========
Upgrading
=========

2.0.1
=====

Upgrade Type
------------

* Security [Severity: Medium]
* Bug fix
* Enhancement

Backward compatibility
----------------------

This release does not introduce any backwards incompatible changes.

New dependencies
----------------

* sqlparse

New configuration options
-------------------------

* ``ms.quarantine.shared`` - Enables and disables shared quarantine features ``default: disabled``
* ``baruwa.themes.base`` - Sets the directory containing themes ``default: /usr/share/baruwa/themes``
* ``baruwa.custom.name`` - Sets the custom product name for rebranding ``default: Baruwa Hosted``
* ``baruwa.custom.url`` - Sets the url for the product ``default: http://www.baruwa.net/``

Upgrading
---------

Baruwa Enterprise Edition has switched from using the certificate authenticated
repository to a Spacewalk managed entitlement system. In order to access the new
system you need to install the Spacewalk client tools and obtain an activation
key for your server entitlement.

Review the changelog for version :ref:`change_2.0.1` and read the updated
documentation before you proceed with the upgrade.

Backup your current system::

	tar cjvf /usr/local/src/baruwa-configs.tar.bz2 /etc/baruwa
	tar cjvf /usr/local/src/baruwa-software.tar.bz2 /usr/lib/python2.6/site-packages/baruwa 

When ready to perform the upgrade, have your activation key handy then run the
following commands, replace ``<activation-key>`` with your actual activation
key::

	rpm -Uvh https://www.baruwa.com/downloads/baruwa-enterprise-release-6-2.noarch.rpm
	rpm -Uvh http://yum.spacewalkproject.org/1.9/RHEL/6/x86_64/spacewalk-client-repo-1.9-1.el6.noarch.rpm
	yum install rhn-client-tools rhn-check rhn-setup rhnsd m2crypto yum-rhn-plugin -y
	rhnreg_ks --serverUrl=http://bn.baruwa.com/XMLRPC --activationkey=<activation-key>

Download and install the updated puppet toaster::

	curl -O https://www.baruwa.com/downloads/puppet-toaster-latest.tar.bz2
	tar xjvf puppet-toaster-latest.tar.bz2 -C /etc/puppet/

Review the new options available to the puppet manifest and add to your previous
manifest, then run::

	yum upgrade -y
	rm -rf /var/lib/baruwa/data/cache/*
	rm -rf /var/lib/baruwa/data/sessions/*
	rm -rf /var/lib/baruwa/data/templates/*
	service uwsgi restart
	service baruwa restart
	puppet -v /etc/puppet/manifests/toasters/baruwa/$(hostname).pp

If you had customized your interface, then follow the theming guidelines to create
a theme that will not be overridden by your next update.
