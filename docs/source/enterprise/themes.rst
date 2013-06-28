.. _themes:

======
Themes
======

Themes, also known as skins, in the Baruwa Enterprise Edition are a
combination of Mako Template, CSS and JS files that control the
appearance of the Baruwa Web interface as well as reports and emails
sent out by the system.

The theme system allows you to easily change the appearance of
Baruwa, for example, to use the logo and colors of your company or
institution. Themes are linked to the hostname used to access the
Baruwa server and the domain user accounts belong to, which means
that you can virtual host various brands on the same server with
different appearance and product name for each.

Using themes ensures that the changes you make survive upgrades as
opposed to changes made to the default template and asset files
shipped with Baruwa which get overwritten during an upgrade.

What can be customized
======================

* Logos
* Web interface
* Emails
* Reports
* Product name
* Product url

Guidelines
==========

* Themes ``MUST`` retain the copyright notice at the bottom.

Configuration
=============

The default configuration assumes that themes are stored under the
following directory ``/usr/share/baruwa/themes`` with the following
directory structure::

	/templates/<hostname>/
	/templates/<domainname>/
	/assets/<hostname>/
	/assets/<domainname>/

Themes are configured by:

* Pointing the web server configuration for assets to the site's asset directory
* Setting the ``baruwa.themes.base`` to the directory containing the themes
* Setting the ``baruwa.custom.name`` to the custom product name
* Setting the ``baruwa.custom.url`` to the custom product web url

Creating a simple theme
=======================

To start off, you simply copy the default templates and assets into the a
theme directory for the hostname you would like to customize for.

I will be using the hostname ``spamfighter.example.com``::

	BARUWA_PATH=$(python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")
	mkdir -p /usr/share/baruwa/themes/assets/spamfighter.example.com/
	mkdir -p /usr/share/baruwa/themes/templates/spamfighter.example.com/
	cp -a $BARUWA_PATH/baruwa/templates/* /usr/share/baruwa/themes/templates/spamfighter.example.com/
	cp -a $BARUWA_PATH/baruwa/public/* /usr/share/baruwa/themes/assets/spamfighter.example.com/

You can now modify the changes to the templates under ``/usr/share/baruwa/themes/templates/spamfighter.example.com/``
and the CSS, JS and image files under ``/usr/share/baruwa/themes/assets/spamfighter.example.com/``

In order to brand other non web interfaces such as email you need to link the
themes to the domain name you want to brand.

For example to theme the domain name ``example.com``::

	ln -s /usr/share/baruwa/themes/assets/spamfighter.example.com \
	/usr/share/baruwa/themes/assets/example.com
	ln -s /usr/share/baruwa/themes/templates/spamfighter.example.com \
	/usr/share/baruwa/themes/templates/example.com

Creating themes from scratch
============================

It is possible to totally redesign the Baruwa interface using a theme, this
requires an understanding of the data being sent into the template files by
Baruwa as well as the Mako Template language.

Theme customization services are available from the author.

Emails and Reports
==================

In order to send out reports and emails that are customized using the above
configurations you need to use the new generation commands.

* ``paster send-quarantine-reports-ng`` for quarantine reports
* ``send-pdf-reports-ng`` for pdf reports
