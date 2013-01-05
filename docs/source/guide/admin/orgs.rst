
======================
Managing Organizations
======================

Organizations enable easy management of large number of domains, Administrators
are assigned to Organizations and can manage all the domains with in the
organization.

You can create smaller organizations out of bigger organizations and add
specific domains from a bigger organization to allow delegation of domain
management.

.. _add_organization:

Add an Organization
-------------------

1. Mouse over ``Organizations``
2. Click ``Add Organization``
3. Enter the name in ``Organization name``
4. Select domain in ``Domains`` list if they already exist
5. Select admins from ``Admins`` list if they already exist
6. Click the ``Add organization`` Button

Update an Organization
----------------------

1. Click ``Organizations``
2. Select organization > Click ``Edit``
3. Make changes
4. Click the ``Update organization`` Button

Delete an Organization
----------------------

1. Click ``Organizations``
2. Select organization > Click ``Delete``
3. Check ``Delete Organization domains`` if you want to delete domains belonging
   to the organization.
4. Click the ``Delete organization`` Button

Search for an Organization
--------------------------

If you have a large number of organizations you can search for an organization by
name.

1. Click ``Organizations``
2. Enter the organization name in the search box
3. Click the ``Search`` Button

List all domains that belong to an organization
-----------------------------------------------

To find all domains that belong to a specific organization.

1. Click ``Organizations``
2. Select organization > Click ``List domains``

List all accounts that belong to an organization
------------------------------------------------

To find all accounts that belong to a specific organization.

1. Click ``Organizations``
2. Select organization > Click ``List accounts``

Add a new domain to an organization
-----------------------------------

1. Click ``Organizations``
2. Select organization > Click ``Add domain``
3. Enter the domain details
4. Click ``Add domain``

.. _importing_domains:

Import domains to an organization
---------------------------------

Domains can be imported using a CSV formatted file. To import domains in to
an organization.

1. Click ``Organizations``
2. Select organization > Click ``Import domains``
3. Browse for the CSV file by clicking ``Browse`` next to the ``CSV file`` field
4. Check ``Skip first line`` if your first line contains descriptions.
5. Click the ``Import`` Button

Export an Organization's user accounts
--------------------------------------

You can export all the user accounts with in an organization.

1. Click ``Organizations``
2. Click the organization name
3. Click ``Export accounts``
4. Click ``Download the csv file``
5. Save the file to your computer

View Organization details
-------------------------

To view the details of an organization such as number of ``domains``, ``admins``,
``relay settings``

1. Click ``Organizations``
2. Click the organization name


Add Outbound SMTP relay settings
--------------------------------

Relaying of outbound mail is authenticated on a per organization basis, to enable
an organization to send outbound mail through Baruwa you need to add relay settings.

Two kinds of outbound relaying are supported.

* IP address
* SMTP AUTH

Add Outbound SMTP IP Address settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This allows the specific IP address to send outbound mail through Baruwa.

1. Click ``Organizations``
2. Click the organization name
3. Click ``Add relay setting``
4. Enter the IP address in the ``Hostname`` field
5. Ensure the ``Enabled`` checkbox is checked
6. Click ``Add settings``

Add Outbound SMTP AUTH settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This allows any client that supplies these credentials to send outbound mail
through Baruwa.

1. Click ``Organizations``
2. Click the organization name
3. Click ``Add relay setting``
4. Ensure the ``Enabled`` checkbox is checked
5. Enter the username in the ``SMTP-AUTH username`` field
6. Enter the password in the ``SMTP-AUTH password`` field
7. Reenter the password in the ``Retype Password`` field
8. Click ``Add settings``

