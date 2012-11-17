
================
Exim Integration
================

Routing
=======

You can use the following route_data options in your routers used
to deliver the cleaned mail. Both randomized and failover routing
are supported.

.. sourcecode:: bash

	ROUTE_QUERY = SELECT '"<+ ' || 
			array_to_string(ARRAY(SELECT address FROM routedata WHERE enabled='t'
			AND name='${quote_pgsql:$domain}'),' + ') || '"' as a
	begin routers
	deliver_clean_randomize:
	   driver = manualroute
	   domains = +relay_sql_rand_smtp
	   transport = remote_smtp
	   hosts_randomize = true
	   route_data = ${lookup pgsql {ROUTE_QUERY}}
	deliver_clean_norandomized:
	   driver = manualroute
	   domains = +relay_sql_nonrand_smtp
	   transport = remote_smtp
	   hosts_randomize = false
	   route_data = ${lookup pgsql {ROUTE_QUERY}}

Delivery notification
=====================

Logging of mail delivery and non delivery information to a
database is supported.

.. sourcecode:: bash

	DELIVERY_QUERY = ${lookup pgsql \
		{INSERT INTO messagestatus (messageid, hostname, ipaddress, port, confirmation) \
	    VALUES('${quote_pgsql:$message_exim_id}', '${quote_pgsql:$dbl_delivery_fqdn}', \
	 	'${quote_pgsql:$dbl_delivery_ip}', \
	    ${quote_pgsql:$dbl_delivery_port}, '${quote_pgsql:$dbl_delivery_confirmation}')}}
	DEFER_QUERY = ${lookup pgsql {INSERT INTO messagestatus (messageid, hostname, ipaddress,\
	 	port, confirmation, errorno, errorstr) \
		VALUES('${quote_pgsql:$message_exim_id}', '${quote_pgsql:$dbl_delivery_fqdn}',\
		 '${quote_pgsql:$dbl_delivery_ip}', ${quote_pgsql:$dbl_delivery_port},\
		 '${quote_pgsql:$dbl_delivery_confirmation}', ${quote_pgsql:$dbl_defer_errno}, \
		'${quote_pgsql:$dbl_defer_errstr}')}}
	
	dbl_delivery_query = DELIVERY_QUERY

	begin transports
	remote_smtp:
	   driver = smtp
	   dbl_host_defer_query = DEFER_QUERY


Relaying
========

Relay information from with in Baruwa can be used to authorize the
relaying of mail in exim. Both inbound and outbound relaying is
supported. Address verification is supported using SMTP callbacks
and LDAP lookups.

.. sourcecode:: bash

	RELAY_SQL_DOMAINS = pgsql;SELECT name FROM relaydomains WHERE name='${quote_pgsql:$domain}';
	SMTP_SQL_DOMAINS = pgsql;SELECT name FROM mtasettings WHERE name='${quote_pgsql:$domain}' \
	                         AND protocol=1;
	LMTP_SQL_DOMAINS = pgsql;SELECT name FROM mtasettings WHERE name='${quote_pgsql:$domain}' \
	                         AND protocol=2;
	RELAY_SQL_HOSTS = pgsql;SELECT address FROM relaysettings WHERE enabled='t' AND \
						address='${quote_pgsql:$sender_host_address}';
	LDAP_DOMAINS = pgsql;SELECT name FROM mtasettings WHERE name='${quote_pgsql:$domain}' \
	                     AND ldap_callout='t';
	LDAP_LOOKUP = ${lookup pgsql {SELECT url FROM ldaplookup WHERE name='${quote_pgsql:$domain}'}}

	domainlist relay_sql_domains = RELAY_SQL_DOMAINS
	domainlist relay_sql_smtp_domains = SMTP_SQL_DOMAINS
	domainlist relay_sql_lmtp_domains = LMTP_SQL_DOMAINS
	domainlist ldap_domains = LDAP_DOMAINS
	hostlist relay_sql_hosts = RELAY_SQL_HOSTS

	acl_check_rcpt:
		require message       = relay not permitted
	          	domains       = +local_domains : +relay_sql_domains
		accept  hosts         = +relay_sql_hosts
		          control       = submission/sender_retain
		drop    message       = REJECTED - User Not Found
		          domains       = +ldap_domains
		          condition     = ${lookup ldap{${expand:LDAP_LOOKUP}}{0}{1}}

SMTP Authentication
===================

User information from with in Baruwa can be used to authenticate
SMTP connections.

.. sourcecode:: bash

	begin authenticators
	PLAIN:
	   driver = plaintext
	   server_prompts = :
	   server_condition = ${if and{ {!eq {$auth2}{}} {!eq {$auth3}{}}\
	                                {bool{${perl{check_password}\
	                                {${lookup pgsql {ORG_CHECK_PLAIN}{$value}}}\
	                                {$auth3}}}\
	                                }\
	                              }\
	                       {yes}{no}}
	   server_set_id = $2
	   server_advertise_condition = ${if def:tls_cipher }

	LOGIN:
	   driver = plaintext
	   server_prompts = "Username:: : Password::"
	   server_condition = ${if and{ {!eq {$auth1}{}} {!eq {$auth2}{}}\
		                            {bool{${perl{check_password}\
		                            {${lookup pgsql {ORG_CHECK_LOGIN}{$value}}}\
		                            {$auth2}}}}\
		                          }\
		                  {yes}{no}}
	   server_set_id = $1
	   server_advertise_condition = ${if def:tls_cipher }

DKIM
====

You can sign messages in Exim using signatures generated via Baruwa.
When you create and enable DKIM signatures in the interface they are
automatically deployed to all your nodes.

.. sourcecode:: bash

	begin transports
	remote_smtp:
	   driver = smtp
	   delay_after_cutoff = false
	   dkim_domain = ${if exists{/etc/MailScanner/baruwa/dkim/${lc:$sender_address_domain}.pem}\
	                 {${lc:$sender_address_domain}}{}}
	   dkim_selector = baruwa
	   dkim_private_key = ${if exists{/etc/MailScanner/baruwa/dkim/${lc:$sender_address_domain}.pem}\
	                       {/etc/MailScanner/baruwa/dkim/${lc:$sender_address_domain}.pem}{0}}


Authorized and Banned sender lists
==================================

Also known as white and black lists, they can be integrated into Exim allowing
for rejection or acceptance of messages from senders on the lists.

.. sourcecode:: bash

	BLACKLISTED_DOMAINS = pgsql;SELECT from_address FROM lists \
						WHERE to_address='any' AND list_type=2 \
						AND from_address='${quote_pgsql:$sender_address_domain}';
	BLACKLISTED_ADDRESS = pgsql;SELECT from_address from lists WHERE \
						to_address='any' AND list_type=2 AND \
						from_address='${quote_pgsql:$sender_address}';
	BLACKLISTED_HOSTS = pgsql;SELECT from_address FROM lists WHERE \
						to_address='any' AND list_type=2 AND \
						from_address='${quote_pgsql:$sender_host_address}';

	domainlist blacklisted_domains = BLACKLISTED_DOMAINS
	addresslist blacklisted_addresses = BLACKLISTED_ADDRESS
	hostlist blacklisted_hosts = BLACKLISTED_HOSTS

	drop message          = REJECTED - Sender $sender_address is banned
	          hosts         = +blacklisted_hosts
	drop message          = REJECTED - Domain $sender_address_domain is banned
	        domains       = +blacklisted_domains

There is more
=============

There is a lot more that can be done please refer to the example configurations in
the tar ball.
