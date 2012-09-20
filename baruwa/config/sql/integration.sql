--ldap recipient checks
DROP VIEW IF EXISTS ldaplookup;
CREATE VIEW ldaplookup AS
    SELECT 'user="' || binddn || '" pass="' || bindpw || '" '
    || CASE WHEN port=636 THEN
    'ldaps://' || address || ':' || CAST(port AS text) || '/'
    WHEN port=389 OR port IS NULL THEN
    'ldap://' || address || '/'
    ELSE
    'ldap://' || address || ':' || CAST(port AS text) || '/'
    END
    || basedn || '?' || emailattribute || '?' ||
    CASE WHEN search_scope='subtree' THEN 'sub?' ELSE 'one?' END ||
    REPLACE(REPLACE(emailsearchfilter, '%u', '${quote_ldap:$local_part}'), '%d', '$domain')
    AS url, name FROM ldapsettings, authservers, maildomains WHERE
    ldapsettings.auth_id = authservers.id AND
    authservers.domain_id = maildomains.id;

--quickpeek
DROP VIEW IF EXISTS quickpeek;
CREATE VIEW quickpeek AS
    SELECT value, hostname, external, internal,
    CASE WHEN hostname='default' THEN 2 ELSE 1 END AS rank
    FROM configurations, servers WHERE configurations.server_id = servers.id AND
    enabled='t' ORDER BY rank ASC;

--routedata
DROP VIEW IF EXISTS routedata;
CREATE VIEW routedata AS
    SELECT CASE WHEN port != 25 THEN
                CASE WHEN address !~* E'^(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\\.)+[a-zA-Z]{2,6}\\.?$' THEN
                    '['||address||']:'||port
                ELSE
                    address||':'||port
                END
            ELSE
                address
            END AS address, name, enabled, delivery_mode, protocol
    FROM destinations, maildomains
    WHERE maildomains.id=destinations.domain_id UNION
    SELECT CASE WHEN port != 25 THEN
                CASE WHEN address !~* E'^(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\\.)+[a-zA-Z]{2,6}\\.?$' THEN
                    '['||address||']:'||port
                ELSE
                    address||':'||port
                END
            ELSE
                address
            END AS address, domainalias.name AS name,
            domainalias.status AS enabled, delivery_mode, protocol
    FROM destinations, maildomains, domainalias
    WHERE maildomains.id=destinations.domain_id AND
    maildomains.id=domainalias.domain_id;

--relaydomains
DROP VIEW IF EXISTS relaydomains;
CREATE VIEW relaydomains AS
    SELECT name FROM maildomains WHERE status='t'
	UNION
    SELECT domainalias.name AS name FROM domainalias, maildomains WHERE
    domainalias.domain_id = maildomains.id AND maildomains.status='t'
    AND domainalias.status='t';

--current_domains
DROP VIEW IF EXISTS current_domains;
CREATE VIEW current_domains AS
    SELECT name FROM maildomains
    UNION
    SELECT name FROM domainalias;

--nonrandsmtp
DROP VIEW IF EXISTS mtasettings;
CREATE VIEW mtasettings AS
    SELECT name, protocol, delivery_mode, ldap_callout, smtp_callout FROM maildomains, destinations
    WHERE maildomains.id=destinations.domain_id AND destinations.enabled='t' AND maildomains.status='t'
    UNION
	SELECT domainalias.name AS name, protocol, delivery_mode, ldap_callout, smtp_callout FROM
    maildomains, destinations, domainalias WHERE maildomains.id=destinations.domain_id AND
    maildomains.id=domainalias.domain_id AND domainalias.status='t' AND destinations.enabled='t'
    AND maildomains.status='t';

-- Spam Actions = spamactions.customize
DROP VIEW IF EXISTS spamactions CASCADE;
CREATE VIEW spamactions AS
SELECT row_number, oldtable.*, character(50) 'spamactions' AS name FROM
	(SELECT ARRAY_TO_STRING(ARRAY['To: ', name, ' ',
	    CASE WHEN spam_actions=1 THEN 'deliver'
	    WHEN spam_actions=3 THEN 'delete' END], ' ') ruleset from maildomains WHERE status='t' AND spam_actions != 2
	UNION ALL
	SELECT ARRAY_TO_STRING(ARRAY['FromOrTo:', 'default', 'store'], ' ')) AS oldtable
	CROSS JOIN
	(SELECT ARRAY(SELECT ARRAY_TO_STRING(ARRAY['To:', name, ' ',
	    CASE WHEN spam_actions=1 THEN 'deliver'
	    WHEN spam_actions=3 THEN 'delete' END], ' ') ruleset from maildomains WHERE status='t' AND spam_actions != 2
	UNION ALL
	SELECT ARRAY_TO_STRING(ARRAY['FromOrTo:', 'default', 'store'], ' ')) AS id) AS oldids
	CROSS JOIN
	generate_series(1, (SELECT COUNT(*) FROM 
	(SELECT id FROM maildomains WHERE status='t' AND spam_actions != 2 UNION ALL SELECT 1) AS td)) AS row_number
	WHERE oldids.id[row_number] = oldtable.ruleset ORDER BY row_number;

--highspamactions.customize
DROP VIEW IF EXISTS highspamactions CASCADE;
CREATE VIEW highspamactions AS
	SELECT row_number, oldtable.*, character(50) 'highspamactions' AS name FROM
	(SELECT ARRAY_TO_STRING(ARRAY['To:', name, ' ',
	    CASE WHEN highspam_actions=1 THEN 'deliver'
	    WHEN highspam_actions=3 THEN 'delete' END], ' ') ruleset from maildomains WHERE status='t' AND highspam_actions != 2
	UNION ALL
	SELECT ARRAY_TO_STRING(ARRAY['FromOrTo:', 'default', 'store'], ' ')) AS oldtable
	CROSS JOIN
	(SELECT ARRAY(SELECT ARRAY_TO_STRING(ARRAY['To:', name, ' ',
	    CASE WHEN highspam_actions=1 THEN 'deliver'
	    WHEN highspam_actions=3 THEN 'delete' END], ' ') ruleset from maildomains WHERE status='t' AND highspam_actions != 2
	UNION ALL
	SELECT ARRAY_TO_STRING(ARRAY['FromOrTo:', 'default', 'store'], ' ')) AS id) AS oldids
	CROSS JOIN
	generate_series(1, (SELECT COUNT(*) FROM 
	(SELECT id FROM maildomains WHERE status='t' AND highspam_actions != 2 UNION ALL SELECT 1) AS td)) AS row_number
	WHERE oldids.id[row_number] = oldtable.ruleset ORDER BY row_number;

--spamchecks.customize
DROP VIEW IF EXISTS spamchecks CASCADE;
CREATE VIEW spamchecks AS
	SELECT row_number, oldtable.*, character(50) 'spamchecks' AS name FROM
	(SELECT ARRAY_TO_STRING(ARRAY['To:', name, 'no'], ' ') ruleset from maildomains WHERE status='t' AND spam_checks='f'
	UNION ALL
	SELECT ARRAY_TO_STRING(ARRAY['FromOrTo:', 'default', 'yes'], ' ')) AS oldtable
	CROSS JOIN
	(SELECT ARRAY(SELECT ARRAY_TO_STRING(ARRAY['To:', name, 'no'], ' ') ruleset from maildomains WHERE status='t' AND spam_checks='f'
	UNION ALL
	SELECT ARRAY_TO_STRING(ARRAY['FromOrTo:', 'default', 'yes'], ' ')) AS id) AS oldids
	CROSS JOIN
	generate_series(1, (SELECT COUNT(*) FROM 
	(SELECT id FROM maildomains WHERE status='t' AND spam_checks='f' UNION ALL SELECT 1) AS td)) AS row_number
	WHERE oldids.id[row_number] = oldtable.ruleset ORDER BY row_number;

--approvedlistinner
DROP VIEW IF EXISTS approvedlistinner CASCADE;
CREATE VIEW approvedlistinner AS
	--emailtoall
	SELECT ARRAY_TO_STRING(ARRAY['From:', from_address, 'yes'], ' ') ruleset, 1 num FROM lists 
	WHERE from_address LIKE '%@%' AND (to_address='any' OR to_address='') AND list_type=1
	--nonemailtoall
	UNION
	SELECT ARRAY_TO_STRING(ARRAY['From:',
	    CASE WHEN from_address ~* E'^(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\\.)+[a-zA-Z]{2,6}\\.?$' THEN '*@' || from_address
	    ELSE from_address END, 'yes'], ' ') ruleset, 1 num FROM lists 
	WHERE from_address NOT LIKE '%@%' AND (to_address='any' OR to_address='') AND list_type=1
	--emailto(domain|email)
	UNION
	SELECT ARRAY_TO_STRING(ARRAY['From:', from_address, ' and To: ', CASE WHEN to_address LIKE '%@%' THEN to_address
	    ELSE '*@' || to_address END, 'yes'], ' ') ruleset, 2 num FROM lists 
	WHERE from_address LIKE '%@%' AND (to_address!='any' AND to_address!='') AND list_type=1
	--nonemailto(domain|email)
	UNION
	SELECT ARRAY_TO_STRING(ARRAY['From:',
	    CASE WHEN from_address ~* E'^(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\\.)+[a-zA-Z]{2,6}\\.?$' THEN '*@' || from_address
	    ELSE from_address
	    END, ' and To: ', 
	    CASE WHEN to_address LIKE '%@%' THEN to_address
	    WHEN to_address ~* E'^(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\\.)+[a-zA-Z]{2,6}\\.?$' THEN '*@' || to_address
	    ELSE to_address END, 'yes'], ' ') ruleset, 3 num FROM lists 
	WHERE from_address NOT LIKE '%@%' AND (to_address!='any' AND to_address!='') AND list_type=1
	UNION SELECT ARRAY_TO_STRING(ARRAY['FromOrTo:', 'default', 'no'], ' ') ruleset, 4 num;

--approvedlist.customize
DROP VIEW IF EXISTS approvedlist CASCADE;
CREATE VIEW approvedlist AS
	SELECT row_number, oldtable.*, character(50) 'approvedlist' AS name FROM
	(SELECT ruleset FROM approvedlistinner) AS oldtable
	CROSS JOIN
	(SELECT ARRAY(SELECT ruleset FROM approvedlistinner ORDER BY num) AS id) AS oldids
	CROSS JOIN
	generate_series(1, (SELECT COUNT(*) FROM approvedlistinner)) AS row_number
	WHERE oldids.id[row_number] = oldtable.ruleset ORDER BY row_number;

--bannedlistinner
DROP VIEW IF EXISTS bannedlistinner CASCADE;
CREATE VIEW bannedlistinner AS
	--emailtoall
	SELECT ARRAY_TO_STRING(ARRAY['From:', from_address, 'yes'], ' ') ruleset, 1 num FROM lists 
	WHERE from_address LIKE '%@%' AND (to_address='any' OR to_address='') AND list_type=2
	--nonemailtoall
	UNION
	SELECT ARRAY_TO_STRING(ARRAY['From: ', 
	    CASE WHEN from_address ~* E'^(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\\.)+[a-zA-Z]{2,6}\\.?$' THEN '*@' || from_address
	    ELSE from_address END, 'yes'], ' ') ruleset, 1 num FROM lists 
	WHERE from_address NOT LIKE '%@%' AND (to_address='any' OR to_address='') AND list_type=2
	--emailto(domain|email)
	UNION
	SELECT ARRAY_TO_STRING(ARRAY['From: ', from_address, ' and To: ', CASE WHEN to_address LIKE '%@%' THEN to_address
	    ELSE '*@' || to_address END, ' yes'], ' ') ruleset, 2 num FROM lists 
	WHERE from_address LIKE '%@%' AND (to_address!='any' AND to_address!='') AND list_type=2
	--nonemailto(domain|email)
	UNION
	SELECT ARRAY_TO_STRING(ARRAY['From: ',
	    CASE WHEN from_address ~* E'^(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\\.)+[a-zA-Z]{2,6}\\.?$' THEN '*@' || from_address
	    ELSE from_address
	    END, ' and To: ', 
	    CASE WHEN to_address LIKE '%@%' THEN to_address
	    WHEN to_address ~* E'^(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\\.)+[a-zA-Z]{2,6}\\.?$' THEN '*@' || to_address
	    ELSE to_address END, ' yes'], '') ruleset, 3 num FROM lists 
	WHERE from_address NOT LIKE '%@%' AND (to_address!='any' AND to_address!='') AND list_type=2
	UNION SELECT ARRAY_TO_STRING(ARRAY['FromOrTo:', 'default', 'no'], ' ') ruleset, 4 num;

--bannedlist.customize
DROP VIEW IF EXISTS bannedlist CASCADE;
CREATE VIEW bannedlist AS
	SELECT row_number, oldtable.*, character(50) 'bannedlist' AS name FROM
	(SELECT ruleset FROM bannedlistinner) AS oldtable
	CROSS JOIN (SELECT ARRAY(SELECT ruleset FROM bannedlistinner ORDER BY num) AS id) AS oldids
	CROSS JOIN generate_series(1, (SELECT COUNT(*) FROM bannedlistinner)) AS row_number
	WHERE oldids.id[row_number] = oldtable.ruleset ORDER BY row_number;

--viruschecks.customize
DROP VIEW IF EXISTS virusscan CASCADE;
CREATE VIEW virusscan AS
	SELECT row_number, oldtable.*, character(50) 'viruschecks' AS name FROM
	(SELECT ARRAY_TO_STRING(ARRAY['To:', name, 'no'], ' ') ruleset from maildomains WHERE status='t' AND virus_checks='f'
	UNION ALL
	SELECT ARRAY_TO_STRING(ARRAY['FromOrTo:', 'default', 'yes'], ' ')) AS oldtable
	CROSS JOIN
	(SELECT ARRAY(SELECT ARRAY_TO_STRING(ARRAY['To:', name, 'no'], ' ') ruleset from maildomains WHERE status='t' AND virus_checks='f'
	UNION ALL
	SELECT ARRAY_TO_STRING(ARRAY['FromOrTo:', 'default', 'yes'], ' ')) AS id) AS oldids
	CROSS JOIN
	generate_series(1, (SELECT COUNT(*) FROM 
	(SELECT id FROM maildomains WHERE status='t' AND virus_checks='f' UNION ALL SELECT 1) AS td)) AS row_number
	WHERE oldids.id[row_number] = oldtable.ruleset ORDER BY row_number;

--innerhighspamscore
DROP VIEW IF EXISTS innerhighspamscore CASCADE;
CREATE VIEW innerhighspamscore AS
	SELECT address, high_score, 1 num FROM addresses, users WHERE
	addresses.user_id=users.id AND users.active='t' AND addresses.enabled='t'
	UNION
	SELECT email, high_score, 2 num FROM users WHERE high_score > 0
	UNION
	SELECT '*@' || name, high_score, 3 num FROM maildomains WHERE
	maildomains.status='t' AND maildomains.high_score > 0;

--highspamscore.customize
DROP VIEW IF EXISTS highspamscore CASCADE;
CREATE VIEW highspamscore AS
	SELECT row_number, oldtable.*, character(50) 'highspamscore' AS name FROM
	(SELECT ARRAY_TO_STRING(ARRAY['To:', address, ' ', TEXT(high_score)], ' ') ruleset from innerhighspamscore where high_score != 10
	UNION ALL
	SELECT ARRAY_TO_STRING(ARRAY['FromOrTo:', 'default', '10'], ' ')) AS oldtable
	CROSS JOIN
	(SELECT ARRAY(SELECT ARRAY_TO_STRING(ARRAY['To:', address, ' ', TEXT(high_score)], ' ') ruleset from innerhighspamscore where high_score != 10
	UNION ALL
	SELECT ARRAY_TO_STRING(ARRAY['FromOrTo:', 'default', '10'], ' ')) AS id) AS oldids
	CROSS JOIN
	generate_series(1, (SELECT COUNT(*) FROM 
	(SELECT address FROM innerhighspamscore WHERE high_score != 10 UNION ALL SELECT '1') AS td)) AS row_number
	WHERE oldids.id[row_number] = oldtable.ruleset ORDER BY row_number;

--innerspamscore
DROP VIEW IF EXISTS innerspamscore CASCADE;
CREATE VIEW innerspamscore AS
	SELECT address, low_score, 1 num FROM addresses, users WHERE
	addresses.user_id=users.id AND users.active='t' AND addresses.enabled='t' AND low_score > 0
	UNION SELECT email, low_score, 2 num FROM users WHERE low_score > 0
	UNION SELECT '*@' || name, low_score, 3 num FROM maildomains WHERE maildomains.status='t' AND maildomains.low_score > 0;

--spamscore.customize
DROP VIEW IF EXISTS spamscore CASCADE;
CREATE VIEW spamscore AS
	SELECT row_number, oldtable.*, character(50) 'spamscore' AS name FROM
	(SELECT ARRAY_TO_STRING(ARRAY['To:', address, ' ', TEXT(low_score)], ' ') ruleset from innerspamscore where low_score != 5
	UNION ALL
	SELECT ARRAY_TO_STRING(ARRAY['FromOrTo:', 'default', '5'], ' ')) AS oldtable
	CROSS JOIN
	(SELECT ARRAY(SELECT ARRAY_TO_STRING(ARRAY['To:', address, ' ', TEXT(low_score)], ' ') ruleset from innerspamscore  where low_score != 5
	UNION ALL
	SELECT ARRAY_TO_STRING(ARRAY['FromOrTo:', 'default', '5'], ' ')) AS id) AS oldids
	CROSS JOIN
	generate_series(1, (SELECT COUNT(*) FROM 
	(SELECT address FROM innerspamscore  WHERE low_score != 5 UNION ALL SELECT '1') AS td)) AS row_number
	WHERE oldids.id[row_number] = oldtable.ruleset ORDER BY row_number;

--messagesize.customize
DROP VIEW IF EXISTS messagesize CASCADE;
CREATE VIEW messagesize AS
	SELECT row_number, oldtable.*, character(50) 'messagesize' AS name FROM
	(SELECT ARRAY_TO_STRING(ARRAY['To:', '*@', name, ' ', TEXT(message_size)], ' ') ruleset from maildomains WHERE status='t' AND message_size != '0'
	UNION ALL
	SELECT ARRAY_TO_STRING(ARRAY['FromOrTo:', 'default', '0'], ' ')) AS oldtable
	CROSS JOIN
	(SELECT ARRAY(SELECT ARRAY_TO_STRING(ARRAY['To:', '*@', name, ' ', TEXT(message_size)], ' ')
	 ruleset from maildomains WHERE status='t' AND message_size !='0'
	UNION ALL
	SELECT ARRAY_TO_STRING(ARRAY['FromOrTo:', 'default', '0'], ' ')) AS id) AS oldids
	CROSS JOIN
	generate_series(1, (SELECT COUNT(*) FROM 
	(SELECT id FROM maildomains WHERE status='t' AND message_size != '0' UNION ALL SELECT 1) AS td)) AS row_number
	WHERE oldids.id[row_number] = oldtable.ruleset ORDER BY row_number;

-- innersignmsgs
DROP VIEW IF EXISTS innersignmsgs CASCADE;
CREATE VIEW innersignmsgs AS
	--email aliases
	SELECT ARRAY_TO_STRING(ARRAY['From:', address, 'yes'], ' ') ruleset, 1 AS num FROM
	users, addresses, user_signatures WHERE users.id = addresses.user_id AND users.id = user_signatures.user_id AND users.active='t'
	AND addresses.enabled='t' AND user_signatures.enabled='t' AND user_signatures.signature_type = 1
	UNION
	--user email address
	SELECT ARRAY_TO_STRING(ARRAY['From:', email, 'yes'], ' ') ruleset, 1 AS num FROM
	users, user_signatures WHERE users.id = user_signatures.user_id AND user_signatures.enabled='t' AND users.active='t'
	AND user_signatures.signature_type = 1
	UNION
	-- domains
	SELECT ARRAY_TO_STRING(ARRAY['From: ', '*@', name, ' yes'], '') ruleset, 2 AS num FROM
	maildomains, domain_signatures WHERE maildomains.id = domain_signatures.domain_id AND maildomains.status='t'
	AND domain_signatures.enabled='t' AND domain_signatures.signature_type = 1
	UNION
	-- default
	SELECT E'FromOrTo: default  no' AS ruleset, 3 AS num;

-- signmsgs.customize
-- Sign Clean Messages
DROP VIEW IF EXISTS signmsgs CASCADE;
CREATE VIEW signmsgs AS
	SELECT row_number, oldtable.*, character(50) 'signmsgs' AS name FROM
    (SELECT ruleset FROM innersignmsgs) AS oldtable
    CROSS JOIN
    (SELECT ARRAY(SELECT ruleset FROM innersignmsgs ORDER BY num) AS id) AS oldids
	CROSS JOIN
	generate_series(1, (SELECT COUNT(*) FROM innersignmsgs)) AS row_number
	WHERE oldids.id[row_number] = oldtable.ruleset ORDER BY row_number;

-- innerhtmlsigs
DROP VIEW IF EXISTS innerhtmlsigs CASCADE;
CREATE VIEW innerhtmlsigs AS
	--email aliases
	SELECT ARRAY_TO_STRING(ARRAY['From: ', address, ' %signature-dir%/users/', username, '/sig.html'], '') ruleset, 1 AS num FROM
	users, addresses, user_signatures WHERE users.id = addresses.user_id AND users.id = user_signatures.user_id AND users.active='t'
	AND addresses.enabled='t' AND user_signatures.enabled='t' AND user_signatures.signature_type = 2
	UNION
	--user email address
	SELECT ARRAY_TO_STRING(ARRAY['From: ', email, ' %signature-dir%/users/', username, '/sig.html'], '') ruleset, 1 AS num FROM
	users, user_signatures WHERE users.id = user_signatures.user_id AND user_signatures.enabled='t' AND users.active='t'
	AND user_signatures.signature_type = 2
	UNION
	-- domains
	SELECT ARRAY_TO_STRING(ARRAY['From: ', '*@', name, ' %signature-dir%/domains/', name, '/sig.html'], '') ruleset, 2 AS num FROM
	maildomains, domain_signatures WHERE maildomains.id = domain_signatures.domain_id AND maildomains.status='t'
	AND domain_signatures.enabled='t' AND domain_signatures.signature_type = 2
	UNION
	-- default
	SELECT E'FromOrTo: default %report-dir%/inline.sig.html' AS ruleset, 3 AS num;

-- htmlsigs.customize
-- Inline HTML Signature
DROP VIEW IF EXISTS htmlsigs CASCADE;
CREATE VIEW htmlsigs AS
	SELECT row_number, oldtable.*, character(50) 'htmlsigs' AS name FROM
    (SELECT ruleset FROM innerhtmlsigs) AS oldtable
    CROSS JOIN
    (SELECT ARRAY(SELECT ruleset FROM innerhtmlsigs ORDER BY num) AS id) AS oldids
	CROSS JOIN
	generate_series(1, (SELECT COUNT(*) FROM innerhtmlsigs)) AS row_number
	WHERE oldids.id[row_number] = oldtable.ruleset ORDER BY row_number;

-- innertextsigs
DROP VIEW IF EXISTS innertextsigs CASCADE;
CREATE VIEW innertextsigs AS
	--email aliases
	SELECT ARRAY_TO_STRING(ARRAY['From: ', address, '  %signature-dir%/users/', username, '/sig.txt'], '') ruleset, 1 AS num FROM
	users, addresses, user_signatures WHERE users.id = addresses.user_id AND users.id = user_signatures.user_id AND users.active='t'
	AND addresses.enabled='t' AND user_signatures.enabled='t' AND user_signatures.signature_type = 1
	UNION
	--user email address
	SELECT ARRAY_TO_STRING(ARRAY['From: ', email, '  %signature-dir%/users/', username, '/sig.txt'], '') ruleset, 1 AS num FROM
	users, user_signatures WHERE users.id = user_signatures.user_id AND user_signatures.enabled='t' AND users.active='t'
	AND user_signatures.signature_type = 1
	UNION
	-- domains
	SELECT ARRAY_TO_STRING(ARRAY['From: ', '*@', name, ' %signature-dir%/domains/', name, '/sig.txt'], '') ruleset, 2 AS num FROM
	maildomains, domain_signatures WHERE maildomains.id = domain_signatures.domain_id AND maildomains.status='t'
	AND domain_signatures.enabled='t' AND domain_signatures.signature_type = 1
	UNION
	-- default
	SELECT E'FromOrTo: default  %report-dir%/inline.sig.txt' AS ruleset, 3 AS num;

-- textsigs.customize
-- Inline Text Signature
DROP VIEW IF EXISTS textsigs CASCADE;
CREATE VIEW textsigs AS
	SELECT row_number, oldtable.*, character(50) 'textsigs' AS name FROM
    (SELECT ruleset FROM innertextsigs) AS oldtable
    CROSS JOIN
    (SELECT ARRAY(SELECT ruleset FROM innertextsigs ORDER BY num) AS id) AS oldids
	CROSS JOIN
	generate_series(1, (SELECT COUNT(*) FROM innertextsigs)) AS row_number
	WHERE oldids.id[row_number] = oldtable.ruleset ORDER BY row_number;

-- innersigimgfiles
DROP VIEW IF EXISTS innersigimgfiles CASCADE;
CREATE VIEW innersigimgfiles AS
	-- email aliases
	SELECT ARRAY_TO_STRING(ARRAY['From: ', address, ' %signature-dir%/users/', username, '/', name], '') ruleset, 1 AS num FROM
	users, user_sigimgs, addresses WHERE users.id = user_sigimgs.user_id AND users.id = addresses.user_id
	AND users.active='t'
	UNION
	-- email addresses
	SELECT ARRAY_TO_STRING(ARRAY['From: ', email, ' %signature-dir%/users/', username, '/', name], '') ruleset, 1 AS num FROM
	users, user_sigimgs WHERE users.id = user_sigimgs.user_id AND users.active='t'
	UNION
	-- domains
	SELECT ARRAY_TO_STRING(ARRAY['From: ', '*@', maildomains.name, ' %signature-dir%/domains/', maildomains.name, '/', dom_sigimgs.name], '') ruleset,
	2 AS num FROM maildomains, dom_sigimgs WHERE maildomains.id = dom_sigimgs.domain_id AND maildomains.status='t'
	UNION
	-- default
	SELECT 'FromOrTo: default no' AS ruleset, 3 AS num;

-- sigimgfiles.customize
-- Signature Image Filename
DROP VIEW IF EXISTS sigimgfiles CASCADE;
CREATE VIEW sigimgfiles AS
	SELECT row_number, oldtable.*, character(50) 'sigimgfiles' AS name FROM
    (SELECT ruleset FROM innersigimgfiles) AS oldtable
    CROSS JOIN
    (SELECT ARRAY(SELECT ruleset FROM innersigimgfiles ORDER BY num) AS id) AS oldids
	CROSS JOIN
	generate_series(1, (SELECT COUNT(*) FROM innersigimgfiles)) AS row_number
	WHERE oldids.id[row_number] = oldtable.ruleset ORDER BY row_number;

-- innersigimgs
DROP VIEW IF EXISTS innersigimgs CASCADE;
CREATE VIEW innersigimgs AS
	-- email aliases
	SELECT ARRAY_TO_STRING(ARRAY['From: ', address, ' ', user_sigimgs.name], '') ruleset, 1 AS num FROM
	users, user_sigimgs, addresses WHERE users.id = user_sigimgs.user_id AND users.id = addresses.user_id
	AND users.active='t'
	UNION
	-- email addresses
	SELECT ARRAY_TO_STRING(ARRAY['From: ', email, ' ', user_sigimgs.name], '') ruleset, 1 AS num FROM
	users, user_sigimgs WHERE users.id = user_sigimgs.user_id AND users.active='t'
	UNION
	-- domains
	SELECT ARRAY_TO_STRING(ARRAY['From: ', '*@', maildomains.name, ' ', dom_sigimgs.name], '') ruleset,
	2 AS num FROM maildomains, dom_sigimgs WHERE maildomains.id = dom_sigimgs.domain_id AND maildomains.status='t'
	UNION
	-- default
	SELECT 'FromOrTo: default no' AS ruleset, 3 AS num;

-- sigimgs.customize
-- Signature Image <img> Filename
DROP VIEW IF EXISTS sigimgs CASCADE;
CREATE VIEW sigimgs AS
	SELECT row_number, oldtable.*, character(50) 'sigimgs' AS name FROM
    (SELECT ruleset FROM innersigimgs) AS oldtable
    CROSS JOIN
    (SELECT ARRAY(SELECT ruleset FROM innersigimgs ORDER BY num) AS id) AS oldids
	CROSS JOIN
	generate_series(1, (SELECT COUNT(*) FROM innersigimgs)) AS row_number
	WHERE oldids.id[row_number] = oldtable.ruleset ORDER BY row_number;

--msrulesets
DROP VIEW IF EXISTS msrulesets;
CREATE VIEW msrulesets AS
    SELECT * FROM spamactions UNION
    SELECT * FROM highspamactions UNION
    SELECT * FROM spamchecks UNION
    SELECT * FROM approvedlist UNION
    SELECT * FROM bannedlist UNION
    SELECT * FROM virusscan UNION
    SELECT * FROM highspamscore UNION
    SELECT * FROM spamscore UNION
	SELECT * FROM htmlsigs UNION
	SELECT * FROM textsigs UNION
	SELECT * FROM sigimgfiles UNION
	SELECT * FROM sigimgs UNION
	SELECT * FROM signmsgs UNION
    SELECT * FROM messagesize UNION
    SELECT * FROM report_ruleset('languages') UNION
    SELECT * FROM report_ruleset('rejectionreport') UNION
    SELECT * FROM report_ruleset('deletedcontentmessage') UNION
    SELECT * FROM report_ruleset('deletedfilenamemessage') UNION
    SELECT * FROM report_ruleset('deletedvirusmessage') UNION
    SELECT * FROM report_ruleset('deletedsizemessage') UNION
    SELECT * FROM report_ruleset('storedcontentmessage') UNION
    SELECT * FROM report_ruleset('storedfilenamemessage') UNION
    SELECT * FROM report_ruleset('storedvirusmessage') UNION
    SELECT * FROM report_ruleset('storedsizemessage') UNION
    SELECT * FROM report_ruleset('disinfectedreport') UNION
    SELECT * FROM report_ruleset('inlinewarninghtml') UNION
    SELECT * FROM report_ruleset('inlinewarningtxt') UNION
    SELECT * FROM report_ruleset('sendercontentreport') UNION
    SELECT * FROM report_ruleset('sendererrorreport') UNION
    SELECT * FROM report_ruleset('senderfilenamereport') UNION
    SELECT * FROM report_ruleset('sendervirusreport') UNION
    SELECT * FROM report_ruleset('sendersizereport') UNION
    SELECT * FROM report_ruleset('senderspamreport') UNION
    SELECT * FROM report_ruleset('senderspamrblreport') UNION
    SELECT * FROM report_ruleset('senderspamsareport') UNION
    SELECT * FROM report_ruleset('inlinespamwarning') UNION
    SELECT * FROM report_ruleset('recipientspamreport')
    ORDER BY row_number ASC;
