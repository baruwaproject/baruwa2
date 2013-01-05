
================
Managing Domains
================

.. _add_domain:

Adding a Domain
===============

Domains can be added by either importing them using a CSV file or by adding
them using the ``Add domain`` form.

To a domain by import refer to :ref:`importing_domains`. To add a domain
using the ``Add domain`` form,

1. Mouse over ``Domains``
2. Click ``Add a domain``
3. Enter the domain details
4. Click the ``Add domain`` Button

Updating a Domain
=================

1. Click ``Domains``
2. Select the domain > Click ``Edit`` under actions
3. Update the details you want to change
4. Click the ``Update Domain`` Button

Deleting a Domain
=================

1. Click ``Domains``
2. Select the domain > Click the ``Domain name``
3. Click ``Delete domain``
4. Click the ``Delete Domain`` Button

Exporting Domains
=================

Domains can be exported to CSV, To export domains.

1. Click ``Domains``
2. Click ``Export Domains``
3. Click ``Download the csv file``
4. Save the CSV file to your computer

Domain Settings
===============

Each domain has a range of additional settings that you can configure. These
include :ref:`delivery_servers`, :ref:`authentication_servers`, :ref:`alias_domains`,
:ref:`dkim`, :ref:`signatures`

.. _delivery_servers:

Delivery Servers
----------------

Delivery servers are the actual mail servers hosting the email accounts where
messages processed by Baruwa need to be delivered.

Multiple servers per domain are supported and they can be configured to either
``load balance`` or ``fail over``.

In ``load balance`` mode mail is sent to the group of servers in a ``round robin``
manner while in ``fail over`` mail is sent to the first in the list and only to
the others if the first is not available.

Adding a delivery server
~~~~~~~~~~~~~~~~~~~~~~~~

1. Click ``Domains``
2. Select the domain > Click the actions ``settings`` icon
3. Click ``Add delivery server``
4. Enter server IP address or Hostname in the ``Server address`` field
5. Select the protocol in the ``Protocol`` drop down
6. Change the port in the ``Port`` field if your mail server does not use port 25
7. Ensure the ``Enabled`` checkbox is checked
8. Click the ``Add server`` button

Editing a delivery server
~~~~~~~~~~~~~~~~~~~~~~~~~

1. Click ``Domains``
2. Select the domain > Click the ``Domain name``
3. Scroll to the bottom
4. Select the ``delivery server`` > Click ``Edit``
5. Make changes
6. Click the ``Update server`` button

Deleting a delivery server
~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Click ``Domains``
2. Select the domain > Click the ``Domain name``
3. Scroll to the bottom under ``Delivery Servers``
4. Select the ``delivery server`` > Click ``Delete``
5. Click the ``Delete server`` button 

.. _authentication_servers:

Authentication Settings
-----------------------

Authentication settings allow users within a domain be be authenticated to
an external authentication system.

This can be used for centralized user management and to allow users to use
existing authentication credentials instead of creating duplicate accounts
on the Baruwa system.

The supported external authentication mechanisms include:

* ``AD/LDAP``
* ``SMTP``
* ``POP3``
* ``IMAP``
* ``RADIUS``

The following mechanisms are planned but have not been implemented yet:

* ``YUBIKEY``
* ``OAUTH``

The AD/LDAP mechanism allows for the user details in the directory to be
automatically updated to the Baruwa account created for them. These details
include:

* ``First name``
* ``Last name``
* ``Primary Email Address``
* ``Alias Email Addresses``

Adding Authentication Settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Click ``Domains``
2. Select the domain > Click the actions ``settings`` icon
3. Click ``Add Authentication settings``
4. Enter server IP address or Hostname in the ``Server address`` field
5. Select the Authentication protocol in the ``Protocol`` drop down
6. Enter the port in the ``Port`` field
7. Ensure the ``Enabled`` checkbox is checked
8. Enter a username map template if your usernames require translation e.g
   ``Webmin`` creates usernames like ``domainowner.username`` the template would
   be ``domainowner.%(user)`` For available variables see :ref:`user_map_templates`
9. Click the ``Add`` button

The ``AD/LDAP`` and ``RADIUS`` mechanisms require additional settings which can be
added by :ref:`ad_additional_settings` and :ref:`radius_additional_setting`.

.. _user_map_templates:

Username map template variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Username map templates are low you to map Baruwa logins to complex user naming
schemes such as those used by web hosting control panels for ``virtual accounts``.

The following variables are available to your ``username map template``:

* ``%(user)`` - replaced by user part of the login
* ``%(domain)`` - replaced by the domain part of the login

.. _ad_additional_settings:

Adding AD/LDAP Authentication additional settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

AD/LDAP authentication requires the following additional setting.

* ``Base DN`` - The LDAP Directory Base DN
* ``Username attribute`` - The username attribute, defaults to ``uid``
* ``Email attribute`` - The email attribute, defaults to ``mail``
* ``Bind DN`` - The BIND DN if Directory does not allow anonymous binds
* ``Bind password`` - The BIND password
* ``Use TLS`` - Use a TLS connection
* ``Search for UserDN`` - Find the UserDN then Bind to that
* ``Auth Search Filter`` - Filter used to find the UserDN
* ``Auth Search Scope`` - Search Scope, defaults to ``subtree``
* ``Email Search Filter`` - Filter used to find email addresses
* ``Email Search Scope`` - Search Scope, defaults to ``subtree``

To Add AD/LDAP Authentication additional settings:

1. Click ``Domains``
2. Select the domain > Click the ``Domain name``
3. Scroll to the bottom under ``Authentication Servers``
4. Select the LDAP ``Authentication server`` > Click ``Settings``
5. Enter the required settings
6. Click the ``Save settings`` button

.. _radius_additional_setting:

Adding RADIUS Authentication additional settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The RADIUS protocol requires a shared secret between the client and the server, the
additional settings allows you to configure this.

To Add RADIUS Authentication additional settings:

1. Click ``Domains``
2. Select the domain > Click the ``Domain name``
3. Scroll to the bottom under ``Authentication Servers``
4. Select the RADIUS ``Authentication server`` > Click ``Settings``
5. Enter the shared secret in the ``Radius secret`` field
6. Click the ``Save settings`` button 

.. _alias_domains:

Alias Domains
-------------

Some domains have mail addressed to the same account using different domain names,
Alias domains allow users access to all their messages regardless of the domain
name under a single login.

Adding an Alias Domain
~~~~~~~~~~~~~~~~~~~~~~

1. Click ``Domains``
2. Select the domain > Click the actions ``settings`` icon
3. Click ``Add Alias Domain``
4. Enter Alias domain name in the ``Domain alias name`` field
5. Ensure the ``Enabled`` checkbox is checked
6. Click the ``Add`` button

.. _dkim:

DKIM
----

*DomainKeys Identified Mail (DKIM) is a method for associating a domain name to an
email message, thereby allowing a person, role, or organization to claim some
responsibility for the message. The association is set up by means of a digital
signature which can be validated by recipients.*
`Wikipidia <https://en.wikipedia.org/wiki/DomainKeys_Identified_Mail>`_

Baruwa allows you to manage the digital signatures within the interfaces and signs
any outbound messages for which DKIM is enabled.

.. _generate_dkim_keys:

Generate DKIM Keys
~~~~~~~~~~~~~~~~~~

To generate DKIM keys for a domain,

1. Click ``Domains``
2. Select the domain > Click the actions ``settings`` icon
3. Click ``DKIM`` > ``Generate DKIM keys``
4. Select ``DNS record`` and add to you DNS zone

Enable DKIM signing
~~~~~~~~~~~~~~~~~~~

1. Make sure your have followed the steps in :ref:`generate_dkim_keys`
2. Click ``Domains``
3. Select the domain > Click the actions ``settings`` icon
4. Click ``DKIM`` > ``Enable/Disable DKIM signing``
5. Ensure the ``Enabled`` checkbox is checked
6. Click the ``Submit`` button

Regenerate DKIM keys
--------------------

1. Click ``Domains``
2. Select the domain > Click the actions ``settings`` icon
3. Click ``DKIM`` > ``Regenerate DKIM keys``
4. Select ``DNS record`` and update your DNS zone

.. _signatures:

Signatures
----------

Baruwa can manage email signatures / disclaimers that are added to messages
that are sent outbound through it. Both HTML and Text signatures are supported.
HTML signatures support a single embedded image.

Adding Signatures/Disclaimers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Click ``Domains``
2. Select the domain > Click the actions ``settings`` icon
3. Click ``Signatures`` > ``Add signature``
4. Select ``Signature type`` from the drop down
5. Enter signature content
6. Ensure the ``Enabled`` checkbox is checked
7. Click the ``Add signature`` button

.. _domains_import_accounts:

Importing Accounts
------------------

Accounts can be imported into a domain using a CSV file.

1. Click ``Domains``
2. Select the domain > Click the actions ``settings`` icon
3. Click ``Import accounts``
4. Browse for the CSV file by clicking ``Browse`` next to the ``CSV file`` field
5. Check ``Skip first line`` if your first line contains descriptions.
6. Click the ``Import`` Button

Exporting Accounts
------------------

Accounts can be exported from a domain to a CSV file.

1. Click ``Domains``
2. Select the domain > Click the actions ``settings`` icon
3. Click ``Export accounts``
4. Click ``Download the csv file``
5. Save the file to your computer

Rulesets
--------

.. note::
	Domain specific rule sets are not implemented yet.

Searching for Domains
=====================

If you have a large number of domains you can search for a domain by
name.

1. Click ``Domains``
2. Enter the Domains name in the search box
3. Click the ``Search`` Button

Bulk domain management
======================

To ``enable``, ``disable`` or ``delete`` multiple domains:

1. Click ``Domains``
2. Use the checkbox to select the domains
3. Select ``enable`` or ``disable`` or ``delete`` at the top
4. Click the ``Submit`` button
