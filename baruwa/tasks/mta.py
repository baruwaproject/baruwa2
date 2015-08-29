# -*- coding: utf-8 -*-
# Baruwa - Web 2.0 MailScanner front-end.
# Copyright (C) 2010-2015  Andrew Colin Kissa <andrew@topdog.za.net>
# vim: ai ts=4 sts=4 et sw=4
"MTA tasks"
import os
import grp
import pwd

from cdb import cdbmake
from pylons import config
from celery.task import task

from baruwa.model.meta import Session

SETTINGS_MAP = {1: 'allow_empty_replyto.cdb',
                2: 'blocked-subjects',
                3: 'non-tls-hosts.cdb',
                4: 'remove-headers.cdb',
                5: 'skip_av_checks.cdb',
                6: 'skip_dkim.cdb',
                7: 'skip_dnsbl.cdb',
                8: 'skip_default_signature.cdb',
                9: 'skip_ratelimit.cdb',
                10: 'skip_spf.cdb'}


def generate_cdb_file(data, filename):
    """Generate a CDB file"""
    cache_dir = config.get('cache_dir', '/var/lib/baruwa/data')
    dest = os.path.join(cache_dir, 'db', filename)
    maker = cdbmake(dest, dest + ".tmp")
    for line in data:
        maker.add(line.key, line.value)
    maker.finish()
    del(maker)
    os.chmod(dest, 0640)
    uid = pwd.getpwnam("baruwa").pw_uid
    gid = grp.getgrnam("exim").gr_gid
    os.chown(dest, uid, gid)


def generate_text_file(data, filename):
    """Generate a TXT file"""
    cache_dir = config.get('cache_dir', '/var/lib/baruwa/data')
    dest = os.path.join(cache_dir, 'db', filename)
    with open(dest, 'w') as handle:
        for line in data:
            handle.write("%s\n" % line[0])
    os.chmod(dest, 0640)
    uid = pwd.getpwnam("baruwa").pw_uid
    gid = grp.getgrnam("exim").gr_gid
    os.chown(dest, uid, gid)


@task(name='generate-relay-domains', ignore_result=True)
def create_relay_domains():
    """Generate relay domains cdb"""
    sql = """SELECT name AS key, name AS value FROM relaydomains"""
    domains = Session.execute(sql)
    generate_cdb_file(domains, 'relaydomains.cdb')
    Session.close()


@task(name='generate-relay-hosts', ignore_result=True)
def create_relay_hosts():
    """Generate relay hosts cdb"""
    sql = """SELECT address AS key, address AS value
            FROM relaysettings WHERE enabled='t' AND
            address NOT LIKE '%/%'"""
    addrs = Session.execute(sql)
    generate_cdb_file(addrs, 'relayhosts.cdb')
    sql = """SELECT address || ':' AS key FROM relaysettings
            WHERE enabled='t' AND address LIKE '%/%'"""
    netaddrs = Session.execute(sql)
    generate_text_file(netaddrs, 'relaynets')
    sql = """SELECT 'trusted_networks ' || address AS key
            FROM relaysettings WHERE enabled='t' AND
            address != ''"""
    trusted_nets = Session.execute(sql)
    generate_text_file(trusted_nets, 'baruwa-custom.cf.local')
    Session.close()


@task(name='generate-relay-proto-domains', ignore_result=True)
def create_relay_proto_domains(protocol):
    """Generate relay domains cdb"""
    if protocol == 1:
        sql = """SELECT name AS key, name AS value FROM mtasettings
                WHERE protocol=1"""
        filename = 'relaysmtpdomains.cdb'
    else:
        sql = """SELECT name AS key, name AS value FROM mtasettings
                WHERE protocol=2"""
        filename = 'relaylmtpdomains.cdb'
    domains = Session.execute(sql)
    generate_cdb_file(domains, filename)
    Session.close()


@task(name='generate-ldap-domains', ignore_result=True)
def create_ldap_domains():
    """Generate LDAP domains"""
    sql = """SELECT name AS key, name AS value FROM
            mtasettings WHERE ldap_callout='t'"""
    domains = Session.execute(sql)
    generate_cdb_file(domains, 'ldapdomains.cdb')
    Session.close()


@task(name='generate-ldap-data', ignore_result=True)
def create_ldap_data():
    """Generate ldap data"""
    sql = """SELECT ldapmaps.name AS key, url
            AS value FROM ldaplookup, ldapmaps
            WHERE ldaplookup.name=ldapmaps.parent"""
    items = Session.execute(sql)
    generate_cdb_file(items, 'ldapdata.cdb')
    Session.close()


@task(name='generate-callback-domains', ignore_result=True)
def create_callback_domains():
    """Generate SMTP callback domains"""
    sql = """SELECT name AS key, name AS value FROM
            mtasettings WHERE smtp_callout='t'"""
    domains = Session.execute(sql)
    generate_cdb_file(domains, 'cbdomains.cdb')
    Session.close()


@task(name='generate-domain-lists', ignore_result=True)
def create_domain_lists(list_type):
    """Approved list"""
    if list_type == 1:
        sql = """SELECT from_address AS key, from_address AS value
                FROM lists WHERE to_address='any' AND list_type=1"""
        filename = 'approvedlists.cdb'
    else:
        sql = """SELECT from_address AS key, from_address AS value
                FROM lists WHERE to_address='any' AND list_type=2"""
        filename = 'bannedlists.cdb'
    addrs = Session.execute(sql)
    generate_cdb_file(addrs, filename)
    Session.close()


@task(name='generate-route-data', ignore_result=True)
def create_route_data():
    """Generate route data"""
    sql = """SELECT name AS key, '"<+ ' ||
            array_to_string(array_agg(address), ' + ' ) || '"' AS value
            FROM routedata WHERE enabled='t' GROUP BY name"""
    addrs = Session.execute(sql)
    generate_cdb_file(addrs, 'routedata.cdb')
    Session.close()


@task(name='generate-auth-data', ignore_result=True)
def create_auth_data():
    """Create auth data"""
    sql = """SELECT username AS key, password AS value
            FROM relaysettings WHERE username !='' AND
            password !=''"""
    recs = Session.execute(sql)
    generate_cdb_file(recs, 'auth.cdb')
    Session.close()


@task(name='generate-smtp-data', ignore_result=True)
def create_smtp(delivery_mode):
    """Create SMTP domains"""
    if delivery_mode == 1:
        sql = """SELECT name AS key, name AS value FROM
                mtasettings WHERE delivery_mode=1 AND
                protocol=1"""
        filename = 'smtprand.cdb'
    else:
        sql = """SELECT name AS key, name AS value FROM
                mtasettings WHERE delivery_mode=2 AND
                protocol=1"""
        filename = 'smtpnonrand.cdb'
    domains = Session.execute(sql)
    generate_cdb_file(domains, filename)
    Session.close()


@task(name='generate-lmtp', ignore_result=True)
def create_lmtp(delivery_mode):
    """Create LMTP domains"""
    if delivery_mode == 1:
        sql = """SELECT name AS key, name AS value FROM
                mtasettings WHERE delivery_mode=1 AND
                protocol=2"""
        filename = 'lmtprand.cdb'
    else:
        sql = """SELECT name AS key, name AS value FROM
                mtasettings WHERE delivery_mode=2 AND
                protocol=2"""
        filename = 'lmtpnonrand.cdb'
    domains = Session.execute(sql)
    generate_cdb_file(domains, filename)
    Session.close()


@task(name='generate-post-smtp-av', ignore_result=True)
def create_post_smtp_av():
    """Create post smtp av domains"""
    sql = """SELECT name AS key, '1' AS value FROM
            alldomains WHERE virus_checks_at_smtp='f'"""
    domains = Session.execute(sql)
    generate_cdb_file(domains, 'postsmtpav.cdb')
    Session.close()


@task(name='generate-av-checks-disabled', ignore_result=True)
def create_av_disabled():
    """Create AV checks disabled domains"""
    sql = """SELECT name AS key, '1' AS value FROM
            alldomains WHERE virus_checks='f'"""
    domains = Session.execute(sql)
    generate_cdb_file(domains, 'avdisabled.cdb')
    Session.close()


@task(name='generate-ratelimit', ignore_result=True)
def create_ratelimit():
    """Create Ratelimit"""
    sql = """SELECT CASE WHEN address != '' THEN
            address ELSE username END AS key,
            CAST(ratelimit AS text) AS value FROM
            relaysettings WHERE enabled='t'
            """
    items = Session.execute(sql)
    generate_cdb_file(items, 'ratelimit.cdb')
    Session.close()


@task(name='generate-mta-settings', ignore_result=True)
def create_mta_settings(setting_type):
    """Create MTA settings"""
    sql = """SELECT address AS key, address AS value FROM
            mta_settings WHERE address_type=%d AND enabled='t'
            """ % int(setting_type)
    items = Session.execute(sql)
    if int(setting_type) == 2:
        generate_text_file(items, SETTINGS_MAP[int(setting_type)])
    else:
        generate_cdb_file(items, SETTINGS_MAP[int(setting_type)])
    Session.close()
