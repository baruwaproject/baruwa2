
=================
Setup MailScanner
=================

The configuration of MailScanner is beyond the scope of this documentation. If
you are not familiar with MailScanner please refer to the
`documentation <http://mailscanner.info/documentation.html>`_ on the
MailScanner website or read the
`MailScanner book <http://mailscanner.info/files/MailScanner-Guide.pdf>`_ which
is freely available online. :ref:`ms_sample_configs` are provided for MailScanner
and Exim you can reuse.

In order to use Baruwa with mailscanner you need to make a few changes to the
MailScanner code and install the :ref:`install_custom_module`.
:ref:`baruwa_ms_patches` are provided to assist you in doing that.

.. _baruwa_ms_patches:

Baruwa patches
~~~~~~~~~~~~~~

The changes made enable the following

	+ Passing the lint flag to custom modules
 	+ Fixes to the SQL configuration module

It is assumed that your MailScanner file is located at ``/usr/sbin/MailScanner``
and your modules at ``/usr/share/MailScanner/MailScanner``. If on your system
they are in different locations please modify the commands below to reflect that::

	cd /usr/sbin
	patch -i /usr/local/src/mailscanner-baruwa-iwantlint.patch
	cd /usr/share/MailScanner/MailScanner
	patch -p3 -i /usr/local/src/mailscanner-baruwa-sql-config.patch

Dependencies
~~~~~~~~~~~~

The Baruwa Custom module uses the following perl packages ``String::CRC32``,
``Encoding::FixLatin``, ``AnyEvent::Handle`` and ``EV``. These packages need
to be installed on your system for the module to function correctly.

Install the Perl modules using CPAN::

	cpan install String::CRC32 Encoding::FixLatin AnyEvent::Handle EV

.. _install_custom_module:

Baruwa Custom module
~~~~~~~~~~~~~~~~~~~~

The Custom MailScanner module provided by Baruwa is used for asynchronous logging
of message meta data to the database and the updating of the sphinx real time
index.

The module has to be installed to the MailScanner custom functions directory
``/usr/share/MailScanner/MailScanner/CustomFunctions``. Please change to reflect
the directory on your system::

	tar xjvf baruwa-2.0.0.tar.bz2 --strip-components=3 \
		baruwa-2.0.0/extras/perl/BS.pm
	mv BS.pm /usr/share/MailScanner/MailScanner/CustomFunctions

.. _ms_sample_configs:

Sample configurations
~~~~~~~~~~~~~~~~~~~~~

Sample configuration files for MailScanner and exim are provided in the source
tar ball under ``extras/config/exim`` and ``extras/config/mailscanner``.
Please review and reuse.