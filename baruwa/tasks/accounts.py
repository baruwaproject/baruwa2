# -*- coding: utf-8 -*-
# Baruwa - Web 2.0 MailScanner front-end.
# Copyright (C) 2010-2012  Andrew Colin Kissa <andrew@topdog.za.net>
# vim: ai ts=4 sts=4 et sw=4

"Accounts tasks"

import os
import csv

import pylons

from pylons import config
from celery.task import task
from webob.multidict import MultiDict
from sqlalchemy.sql import and_
from sqlalchemy.orm import joinedload
from sqlalchemy.pool import NullPool
from sqlalchemy import engine_from_config
from sqlalchemy.orm.exc import NoResultFound
from pylons.i18n.translation import _get_translator
from sqlalchemy.exc import IntegrityError, ProgrammingError

from baruwa.model.meta import Session
from baruwa.model.domains import Domain
from baruwa.lib.outputformats import build_csv
from baruwa.model.accounts import User, Address, domain_owners, domain_users
from baruwa.model.accounts import organizations_admins as oa
from baruwa.forms.accounts import AddUserForm, AddressForm


ACCOUNTFIELDS = ['username', 'password1', 'email', 'account_type', 'active',
                'firstname', 'lastname', 'send_report', 'spam_checks',
                'low_score', 'high_score', 'timezone']
ADDRESSFIELDS = ['address', 'enabled']
BOOLEANFIELDS = ['active', 'send_report', 'spam_checks', 'enabled']

if not Session.registry.has():
    engine = engine_from_config(config, 'sqlalchemy.', poolclass=NullPool)
    Session.configure(bind=engine)


def dict2mdict(values):
    "convert dict to multidict"
    muld = MultiDict()
    for key in values:
        if (key in BOOLEANFIELDS and
            (values[key] == '' or values[key] == 'False'
            or values[key] is None)):
            continue
        muld.add(key, values[key])
    return muld


def getkeys(row, form=None):
    "get for a specific form"
    rdict = {}
    if form == 'af':
        fields = ADDRESSFIELDS
    else:
        fields = ACCOUNTFIELDS

    for field in fields:
        rdict[field] = row[field]
    return rdict


def add_address(row, user, requester):
    "Add address"
    session_dict = {}
    dummy = AddressForm(dict2mdict({}), csrf_context=session_dict)
    fields = getkeys(row, 'af')
    post_data = dict2mdict(fields)
    post_data.add('csrf_token', dummy.csrf_token.current_token)
    form = AddressForm(post_data, csrf_context=session_dict)
    if form.validate():
        try:
            if requester.is_domain_admin:
                # check if they own the domain
                domainname = form.address.data.split('@')[1]
                Session.query(Domain).options(
                        joinedload('organizations')).join(
                        domain_owners,
                        (oa, domain_owners.c.organization_id == \
                        oa.c.organization_id))\
                        .filter(oa.c.user_id == user.id)\
                        .filter(Domain.name == domainname).one()
            addr = Address(address=form.address.data)
            addr.enabled = form.enabled.data
            addr.user = user
            Session.add(addr)
            Session.commit()
        except (IntegrityError, NoResultFound):
            pass


@task(name='import-accounts')
def importaccounts(domid, filename, skipfirst, userid):
    "import accounts"
    logger = importaccounts.get_logger()
    results = dict(rows=[], global_error=[])
    keys = tuple(ACCOUNTFIELDS + ADDRESSFIELDS)
    translator = _get_translator(None)
    pylons.translator._push_object(translator)
    try:
        with open(filename, 'rU') as handle:
            dialect = csv.Sniffer().sniff(handle.read(1024))
            handle.seek(0)
            rows = csv.DictReader(handle, fieldnames=keys, dialect=dialect)
            query = Session.query(Domain).filter(Domain.id == domid)
            domain = query.one()
            requester = Session.query(User).get(userid)
            logger.info("Importing accounts from file: %s for: %s" %
                        (filename, domain.name))
            try:
                count = 1
                for row in rows:
                    if skipfirst and (count == 1):
                        count += 1
                        continue
                    result = dict(id=None,
                                username=row['username'],
                                imported=False,
                                error=None)
                    try:
                        session_dict = {}
                        dummy = AddUserForm(dict2mdict({}),
                                csrf_context=session_dict)
                        fields = getkeys(row)
                        post_data = dict2mdict(fields)
                        post_data.add('password2', row['password1'])
                        post_data.add('domains', domid)
                        post_data.add('csrf_token',
                                    dummy.csrf_token.current_token)
                        form = AddUserForm(post_data,
                                csrf_context=session_dict)
                        form.domains.query = query
                        if form.validate():
                            #db insert
                            if domain.name != form.email.data.split('@')[1]:
                                raise TypeError(
                                    'Cannot import: %s into domain: %s' %
                                    (form.email.data, domain.name)
                                    )
                            user = User(form.username.data, form.email.data)
                            for attr in ['firstname', 'lastname', 'email',
                                'active', 'account_type', 'send_report',
                                'spam_checks', 'low_score', 'high_score',
                                'timezone']:
                                setattr(user, attr, getattr(form, attr).data)
                            user.local = True
                            user.set_password(form.password1.data)
                            if user.is_peleb:
                                user.domains = [domain]
                            Session.add(user)
                            Session.commit()
                            result['id'] = user.id
                            result['imported'] = True
                            logger.info("Imported account: %s" %
                                        row['username'])
                            #address add
                            add_address(row, user, requester)
                        else:
                            logger.info("Import failed account: %s" %
                                        row['username'])
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
                        logger.info("Import failed account: %s" %
                                    row['username'])
                        result['error'] = str(err)
                    except IntegrityError, err:
                        Session.rollback()
                        logger.info("Import failed account: %s" %
                                    row['username'])
                        result['error'] = 'Account already exists'
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


@task(name='export-accounts')
def exportaccounts(domainid, userid, orgid):
    "Export Accounts"
    logger = exportaccounts.get_logger()
    results = dict(f=None, global_error='')
    try:
        logger.info('Starting export of accounts for userid: %s' % userid)
        user = Session.query(User).get(userid)
        if user.is_peleb:
            results['global_error'] = \
            'You are not authorized to export accounts'
            return results
        if user.is_domain_admin and orgid:
            results['global_error'] = \
            'You are not authorized to export organization accounts'
            return results
        users = Session.query(User)\
                .options(joinedload('addresses'))\
                .order_by(User.id)
        if user.is_domain_admin:
            users = users.join(domain_users, (domain_owners,
                                domain_users.c.domain_id ==
                                domain_owners.c.domain_id),
                                (oa,
                                domain_owners.c.organization_id ==
                                oa.c.organization_id)
                                ).filter(oa.c.user_id == user.id)
        if domainid:
            users = users.filter(and_(domain_users.c.domain_id == domainid,
                                domain_users.c.user_id == User.id))
        if orgid:
            users = users.filter(and_(domain_users.c.user_id == User.id,
                                domain_users.c.domain_id == \
                                domain_owners.c.domain_id,
                                domain_owners.c.organization_id == orgid))
        rows = []
        for account in users.all():
            row = account.to_csv()
            if account.addresses:
                row.update(account.addresses[0].to_csv())
            rows.append(row)
        if rows:
            keys = tuple(ACCOUNTFIELDS + ADDRESSFIELDS)
            results['f'] = build_csv(rows, keys)
            logger.info('Export complete, returning csv file')
        else:
            results['global_error'] = 'No accounts found'
            logger.info('Export failed: %s' % results['global_error'])
    except (NoResultFound, ProgrammingError):
        results['global_error'] = 'User account does not exist'
        logger.info('Export failed: %s' % results['global_error'])
    # finally:
    #     Session.close()
    return results