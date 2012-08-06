# -*- coding: utf-8 -*-
# Baruwa - Web 2.0 MailScanner front-end.
# Copyright (C) 2010-2012  Andrew Colin Kissa <andrew@topdog.za.net>
# vim: ai ts=4 sts=4 et sw=4

"Domain tasks"

import socket

from pylons import config
from celery.task import task
from sqlalchemy.pool import NullPool
from sqlalchemy import engine_from_config
from sqlalchemy.orm.exc import NoResultFound
#from pylons.i18n.translation import _

from baruwa.model.meta import Session
from baruwa.model.domains import Domain
from baruwa.lib.outputformats import build_csv
from baruwa.model.accounts import User, domain_owners
from baruwa.model.accounts import organizations_admins as oa
from baruwa.lib.mail.message import TestDeliveryServers
from baruwa.tasks.organizations import DOMAINFIELDS, DAFIELDS
from baruwa.tasks.organizations import DSFIELDS, ASFIELDS


if not Session.registry.has():
    engine = engine_from_config(config, 'sqlalchemy.', poolclass=NullPool)
    Session.configure(bind=engine)


@task(name='test-smtp-server')
def test_smtp_server(host, port, from_addr,
                    to_addr, host_id, count=None):
    "Tests a delivery server"
    result = {'errors': {}, 'host': host_id}
    logger = test_smtp_server.get_logger()
    logger.info("Starting connection tests to: %(host)s" % {
                'host': host})
    try:
        server = TestDeliveryServers(host, port, to_addr, from_addr)
        if server.ping(count):
            result['ping'] = True
        else:
            result['ping'] = False
            result['errors']['ping'] = ' '.join(server.errors)
            server.reset_errors()
        if server.smtp_test():
            result['smtp'] = True
        else:
            result['smtp'] = False
            result['errors']['smtp'] = ' '.join(server.errors)
    except (socket.gaierror, socket.timeout, socket.error), errormsg:
        result['smtp'] = False
        result['errors']['smtp'] = str(errormsg)
    return result


@task(name='export-domains')
def exportdomains(userid, orgid=None):
    "Export domains"
    logger = exportdomains.get_logger()
    results = dict(f=None, global_error='')
    try:
        logger.info('Starting export of domains for userid: %s' % userid)
        user = Session.query(User).get(userid)
        if user.is_peleb:
            results['global_error'] = 'You are not authorized to export domains'
            return results
        if user.is_domain_admin and orgid:
            results['global_error'] = \
            'You are not authorized to export organization domains'
            return results

        domains = Session.query(Domain)
        if orgid:
            domains = domains.join(domain_owners).filter(
                        domain_owners.c.organization_id == orgid)
        if user.is_domain_admin:
            domains = domains.join(domain_owners,
                        (oa, domain_owners.c.organization_id == \
                        oa.c.organization_id))\
                        .filter(oa.c.user_id == user.id)
        rows = []
        for domain in domains.all():
            row = domain.to_csv()
            if domain.servers:
                row.update(domain.servers[0].to_csv())
            if domain.authservers:
                row.update(domain.authservers[0].to_csv())
            if domain.aliases:
                row.update(domain.aliases[0].to_csv())
            rows.append(row)
        if rows:
            keys = tuple(DOMAINFIELDS + DAFIELDS + DSFIELDS + ASFIELDS)
            results['f'] = build_csv(rows, keys)
            logger.info('Export complete, returning csv file')
        else:
            results['global_error'] = 'No domains found'
            logger.info('Export failed: %s' % results['global_error'])
    except NoResultFound:
        results['global_error'] = 'User account does not exist'
        logger.info('Export failed: %s' % results['global_error'])
    except TypeError:
        results['global_error'] = 'Internal error occured'
        logger.info('Export failed: %s' % results['global_error'])
    # finally:
    #     Session.close()
    return results
