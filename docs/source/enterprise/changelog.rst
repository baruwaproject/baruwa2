=========
Changelog
=========

.. _change_2.0.1:

2.0.1
=====

* Fixed domains information leak when logged in as domain admin. Domain admins
  were able to see domains belonging to other users in the drop down menu
  under edit or delete accounts.
* Added support for theming and customization. Included are support for
  Interface, email, reports customization as well as productization with
  a custom name.
* Added support for shared quarantines on shared storage which allows
  messages to be accessed even when the node that processed them is offline.
* Implemented full cluster functionality for all components
* Improvements to Active Directory / LDAP including support for address
  verification of alias domain accounts, import of aliases from LDAP servers
  that use the mail attribute such as OpenLDAP, fix case sensitivity issue
  with Active Directory servers.
* Fixed MailScanner SQL config keyword issue.
* Fixed duplicates of account listings when user belonged to more than one
  domain
* Fixed various issues that caused quarantine reports not to be sent to some
  user accounts.
* Fixed auto user logout when they delete their account.
* Improve the predicate matching system to authorization of actions.
* Fixed previewing of embedded images in emails.
* Fixed the searching of archives when did not display the actual messages
  found.
* Fixed signature processing on the nodes after configuration in the interface.
* Added experimental PDF reporting command with theme support
* Added experimental Quarantine reporting command with theme support
* Fix to various cronjobs like the ones pruning database tables.
* Disabled NJABL
* Updated translations

2.0.0
=====

* Initial release