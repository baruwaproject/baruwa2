# -*- coding: utf-8 -*-
# Baruwa - Web 2.0 MailScanner front-end.
# Copyright (C) 2010-2012  Andrew Colin Kissa <andrew@topost_dataog.za.net>
# vim: ai ts=4 sts=4 et sw=4

"Organization tasks"

import os
import re
import csv

import pylons

from pylons import config
from celery.task import task
from sqlalchemy.pool import NullPool
from webob.multidict import MultiDict
from sqlalchemy import engine_from_config
from sqlalchemy.exc import IntegrityError
from pylons.i18n.translation import _get_translator

from baruwa.model.meta import Session
from baruwa.model.accounts import Group
from baruwa.model.domains import Domain, DomainAlias, DeliveryServer
from baruwa.model.domains import AuthServer
from baruwa.forms.domains import AddDomainForm, AddDomainAlias
from baruwa.forms.domains import AddDeliveryServerForm, AddAuthForm


BOOLFIELDS = ('status', 'smtp_callout', 'ldap_callout',
                'virus_checks', 'spam_checks', 'status',
                'enabled', 'ds_enabled', 'da_status',
                'as_split_address')
DOMAINFIELDS = ['name', 'site_url', 'status', 'smtp_callout',
                'ldap_callout', 'virus_checks', 'spam_checks',
                'spam_actions', 'highspam_actions', 'low_score',
                'high_score', 'message_size', 'delivery_mode',
                'language', 'report_every', 'timezone']
DAFIELDS = ['da_name', 'da_status',]
DSFIELDS = ['ds_address', 'ds_protocol', 'ds_port', 'ds_enabled',]
ASFIELDS = ['as_address', 'as_protocol', 'as_port', 'as_enabled',
            'as_split_address', 'as_user_map_template']

if not Session.registry.has():
    engine = engine_from_config(config, 'sqlalchemy.', poolclass=NullPool)
    Session.configure(bind=engine)


def dict2mdict(values):
    "convert dict to multidict"
    muld = MultiDict()
    for key in values:
        if (key in BOOLFIELDS and
            (values[key] == '' or values[key] == 'False'
            or values[key] is None)):
            continue
        muld.add(key, values[key])
    return muld

def getkeys(row, form=None):
    "get for a specific form"
    rdict = {}
    if form == 'da':
        fields = DAFIELDS
    elif form == 'ds':
        fields = DSFIELDS
    elif form == 'as':
        fields = ASFIELDS
    else:
        fields = DOMAINFIELDS

    for field in fields:
        key = field
        if form:
            s = r'%s_' % form
            key = re.sub(s, '', field)
        rdict[key] = row[field]
    return rdict


def savemodel(model, form, domainid=None):
    "save form data"
    for field in form:
        if field.name != 'csrf_token':
            setattr(model, field.name, field.data)
    if domainid:
        model.domain_id = domainid
    try:
        Session.add(model)
        Session.commit()
    except IntegrityError:
        Session.rollback()


def process_aux(row, domainid):
    "process auxillary domain data"
    try:
        session_dict = {}
        dummy = AddDomainAlias(dict2mdict({}), csrf_context=session_dict)
        # domain alias
        fields = getkeys(row, 'da')
        post_data = dict2mdict(fields)
        post_data.add('domain', str(domainid))
        post_data.add('csrf_token', dummy.csrf_token.current_token)
        form = AddDomainAlias(post_data, csrf_context=session_dict)
        qry = Session.query(Domain).filter(Domain.id == domainid)
        form.domain.query = qry
        if form.validate():
            mod = DomainAlias()
            savemodel(mod, form)
        # delivery server
        fields = getkeys(row, 'ds')
        post_data = dict2mdict(fields)
        post_data.add('csrf_token', dummy.csrf_token.current_token)
        form = AddDeliveryServerForm(post_data, csrf_context=session_dict)
        if form.validate():
            mod = DeliveryServer()
            savemodel(mod, form, domainid)
        # authentication server
        fields = getkeys(row, 'as')
        post_data = dict2mdict(fields)
        post_data.add('csrf_token', dummy.csrf_token.current_token)
        form = AddAuthForm(post_data, csrf_context=session_dict)
        if form.validate():
            mod = AuthServer()
            savemodel(mod, form, domainid)
    except TypeError:
        pass


@task(name='import-domains')
def importdomains(orgid, filename, skipfirst):
    "Import domains"
    logger = importdomains.get_logger()
    results = dict(rows=[], global_error=[])
    keys = tuple(DOMAINFIELDS + DAFIELDS + DSFIELDS + ASFIELDS)
    translator = _get_translator(None)
    pylons.translator._push_object(translator)
    try:
        with open(filename, 'rU') as handle:
            dialect = csv.Sniffer().sniff(handle.read(1024))
            handle.seek(0)
            rows = csv.DictReader(handle, fieldnames=keys, dialect=dialect)
            query = Session.query(Group).filter(Group.id == orgid)
            org = query.one()
            logger.info("Importing domains from file: %s for: %s" %
                        (filename, org.name))
            try:
                count = 1
                for row in rows:
                    if skipfirst and (count == 1):
                        count += 1
                        continue
                    result = dict(id=None,
                                name=row['name'],
                                imported=False,
                                error=None)
                    try:
                        session_dict = {}
                        dummy = AddDomainForm(dict2mdict({}),
                                csrf_context=session_dict)
                        fields = getkeys(row)
                        post_data = dict2mdict(fields)
                        post_data.add('csrf_token',
                                    dummy.csrf_token.current_token)
                        form = AddDomainForm(post_data,
                                csrf_context=session_dict)
                        form.organizations.query = query
                        if form.validate():
                            #insert to db
                            domain = Domain()
                            for field in form:
                                if field.name != 'csrf_token':
                                    setattr(domain, field.name, field.data)
                            domain.organizations.append(org)
                            Session.add(domain)
                            Session.commit()
                            result['id'] = domain.id
                            result['imported'] = True
                            logger.info("Imported domain: %s" % row['name'])
                            ## process other data
                            process_aux(row, domain.id)
                        else:
                            logger.info("Import failed domain: %s" %
                                        row['name'])
                            if isinstance(form.errors, dict):
                                errors = []
                                for field in form.errors:
                                    themsg = u'%s: %s' % (field,
                                                unicode(form.errors[field][0]))
                                    errors.append(themsg)
                                result['error'] = u', '.join(errors)
                            else:
                                result['error'] = form.errors
                    except TypeError, err:
                        logger.info("Import failed domain: %s" % row['name'])
                        result['error'] = str(err)
                    except IntegrityError, err:
                        Session.rollback()
                        logger.info("Import failed domain: %s" % row['name'])
                        result['error'] = 'Domain already exists'
                    finally:
                        count += 1
                        results['rows'].append(result)
            except csv.Error, err:
                logger.info("Import failure error: %s on line no: %s" %
                            (err, rows.line_num))
                errormsg = 'Error: %s on line no: %d' % (err, rows.line_num)
                results['global_error'] = errormsg
        logger.info("Processed file: %s" % filename)
    except (csv.Error, IOError), err:
        results['global_error'] = str(err)
        logger.info("Error: %s, processing %s" % (str(err), filename))
    # finally:
    #     Session.close()
    try:
        os.unlink(filename)
    except OSError:
        pass
    pylons.translator._pop_object()
    return results

