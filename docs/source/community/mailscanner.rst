
=================
Setup MailScanner
=================

The configuration of MailScanner is beyond the scope of this documentation. If
you are not familiar with MailScanner please refer to the
`documentation <http://mailscanner.info/documentation.html>`_ on the
MailScanner website or read the
`MailScanner book <http://mailscanner.info/files/MailScanner-Guide.pdf>`_ which
is freely available online. :ref:`ms_sample_configs` are provided for MailScanner
and Exim which you can reuse.

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

	curl -O https://raw.github.com/akissa/baruwa2/2.0.0/extras/patches/mailscanner-baruwa-iwantlint.patch
	curl -O https://raw.github.com/akissa/baruwa2/2.0.0/extras/patches/mailscanner-baruwa-sql-config.patch
	cd /usr/sbin
	patch -i /home/baruwa/mailscanner-baruwa-iwantlint.patch
	cd /usr/share/MailScanner/MailScanner
	patch -p3 -i /home/baruwa/mailscanner-baruwa-sql-config.patch
	cd /home/baruwa

Dependencies
~~~~~~~~~~~~

The Baruwa Custom module uses the following perl packages ``String::CRC32``,
``Encoding::FixLatin``, ``AnyEvent::Handle``, ``DBD::mysql``, ``DBD::Pg`` and ``EV``.
These packages need to be installed on your system for the module to function
correctly.

Install the Perl modules using CPAN::

	cpan install String::CRC32 Encoding::FixLatin AnyEvent::Handle EV DBD::mysql DBD::Pg

.. _install_custom_module:

Baruwa Custom module
~~~~~~~~~~~~~~~~~~~~

The Custom MailScanner module provided by Baruwa is used for asynchronous logging
of message meta data to the database and the updating of the sphinx real time
index.

The module has to be installed to the MailScanner custom functions directory
``/usr/share/MailScanner/MailScanner/CustomFunctions``. Please change to reflect
the directory on your system::

	curl -O https://raw.github.com/akissa/baruwa2/2.0.0/extras/perl/BS.pm
	mv BS.pm /usr/share/MailScanner/MailScanner/CustomFunctions

.. _ms_sample_configs:

Sample configurations
~~~~~~~~~~~~~~~~~~~~~

Sample configuration files for MailScanner and exim are provided in the source
under `extras/config/exim <https://github.com/akissa/baruwa2/tree/2.0.0/extras/config/exim>`_ 
and `extras/config/mailscanner <https://github.com/akissa/baruwa2/tree/2.0.0/extras/config/mailscanner>`_.
Please review and reuse.

Proceed to :ref:`baruwa_install`