# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4
# Baruwa - Web 2.0 MailScanner front-end.
# Copyright (C) 2010-2012  Andrew Colin Kissa <andrew@topdog.za.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import logging

from urlparse import urlparse

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import redirect, abort
from pylons.i18n.translation import _
from webhelpers import paginate
from celery.result import AsyncResult
#from sqlalchemy.sql import and_
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError, DataError
from repoze.what.predicates import All, not_anonymous
from sphinxapi import SphinxClient, SPH_MATCH_EXTENDED2
from repoze.what.plugins.pylonshq import ActionProtector, ControllerProtector

from baruwa.lib.base import BaseController, render
from baruwa.lib.helpers import flash, flash_info, flash_alert
from baruwa.lib.auth.predicates import OnlyAdminUsers, OnlySuperUsers
from baruwa.lib.auth.predicates import OwnsDomain
from baruwa.lib.caching_query import FromCache
from baruwa.lib.query import get_dom_crcs
from baruwa.lib.dates import now
from baruwa.lib.audit import audit_log
from baruwa.lib.query import clean_sphinx_q, restore_sphinx_q
from baruwa.lib.misc import check_num_param
from baruwa.lib.misc import convert_dom_to_json
from baruwa.tasks.settings import update_serial
from baruwa.tasks.domains import exportdomains, test_smtp_server
from baruwa.model.meta import Session
from baruwa.model.auth import LDAPSettings, RadiusSettings
from baruwa.model.accounts import Group, domain_owners
from baruwa.model.accounts import organizations_admins as oa
from baruwa.model.domains import DomainAlias
from baruwa.model.domains import Domain, DeliveryServer, AuthServer
from baruwa.forms.domains import DelDomainAlias, EditDomainForm
from baruwa.forms.domains import BulkDelDomains, AddLDAPSettingsForm
from baruwa.forms.domains import AddDomainForm, AddDeliveryServerForm
from baruwa.forms.domains import AddAuthForm, AUTH_PROTOCOLS, EditDomainAlias
from baruwa.forms.domains import AddDomainAlias, AddRadiusSettingsForm
from baruwa.lib.audit.msgs.domains import *

log = logging.getLogger(__name__)


@ControllerProtector(All(not_anonymous(), OnlyAdminUsers()))
class DomainsController(BaseController):
    def __before__(self):
        "set context"
        BaseController.__before__(self)
        if self.identity:
            c.user = self.identity['user']
        else:
            c.user = None
        c.selectedtab = 'domains'

    def _get_server(self, destinationid):
        "utility"
        try:
            cachekey = u'deliveryserver-%s' % destinationid
            q = Session.query(DeliveryServer)\
                    .filter(DeliveryServer.id==destinationid)\
                    .options(FromCache('sql_cache_med', cachekey))
            if self.invalidate:
                q.invalidate()
            server = q.one()
        except NoResultFound:
            server = None
        return server

    def _get_organizations(self, orgid=None):
        "Get organizations"
        query = Session.query(Group)
        if orgid:
            query = query.filter(Group.id == orgid)
        return query

    def _get_authserver(self, authid):
        "Get an auth server"
        try:
            cachekey = u'authserver-%s' % authid
            q = Session.query(AuthServer).filter(AuthServer.id==authid)\
                .options(FromCache('sql_cache_med', cachekey))
            if self.invalidate:
                q.invalidate()
            server = q.one()
        except NoResultFound:
            server = None
        return server

    def _get_alias(self, aliasid):
        "Get a domain alias"
        try:
            cachekey = u'domainalias-%s' % aliasid
            q = Session.query(DomainAlias).filter(DomainAlias.id==aliasid)\
                .options(FromCache('sql_cache_med', cachekey))
            if self.invalidate:
                q.invalidate()
            alias = q.one()
        except NoResultFound:
            alias = None
        return alias

    def index(self, page=1, orgid=None, format=None):
        "Browse domains"
        num_items = session.get('domains_num_items', 10)
        c.form = BulkDelDomains(request.POST, csrf_context=session)
        if request.POST:
            if c.form.domainid.data and c.form.whatdo.data == 'disable':
                Session.query(Domain).filter(
                        Domain.id.in_(c.form.domainid.data)
                    ).update({'status':False}, synchronize_session='fetch')
                Session.commit()
            if c.form.domainid.data and c.form.whatdo.data == 'enable':
                Session.query(Domain).filter(
                        Domain.id.in_(c.form.domainid.data)
                    ).update({'status':True}, synchronize_session='fetch')
                Session.commit()
            if c.form.domainid.data and c.form.whatdo.data == 'delete':
                session['bulk_domain_delete'] = c.form.domainid.data
                session.save()
                # redirect for confirmation
                redirect(url('domains-confirm-delete'))
        domains = Session.query(Domain).options(
                joinedload(Domain.organizations))
        domcount = Session.query(Domain.id)

        if orgid and c.user.is_superadmin:
            domains = domains.join(domain_owners).filter(
                        domain_owners.c.organization_id == orgid)
            domcount = domcount.join(domain_owners).filter(
                        domain_owners.c.organization_id == orgid)
        if c.user.is_domain_admin:
            domains = domains.join(domain_owners,
                    (oa, domain_owners.c.organization_id == oa.c.organization_id))\
                    .filter(oa.c.user_id == c.user.id)
            domcount = domcount.join(domain_owners,
                    (oa, domain_owners.c.organization_id == oa.c.organization_id))\
                    .filter(oa.c.user_id == c.user.id)

        pages = paginate.Page(domains, page=int(page),
                                items_per_page=num_items,
                                item_count=domcount.count())
        if format == 'json':
            response.headers['Content-Type'] = 'application/json'
            data = convert_dom_to_json(pages, orgid)
            return data

        c.orgid = orgid
        c.page = pages
        return render('/domains/index.html')

    def search(self, format=None):
        "Search for domains"
        total_found = 0
        search_time = 0
        num_items = session.get('domains_num_items', 10)
        q = request.GET.get('q', '')
        org = request.GET.get('o', None)
        page = int(request.GET.get('p', 1))
        # if q:
        kwds = {'presliced_list': True}
        conn = SphinxClient()
        conn.SetMatchMode(SPH_MATCH_EXTENDED2)
        if page == 1:
            conn.SetLimits(0, num_items, 500)
        else:
            offset = (page - 1) * num_items
            conn.SetLimits(offset, num_items, 500)
        if org:
            conn.SetFilter('orgs', [int(org)])
        if c.user.is_domain_admin:
            crcs = get_dom_crcs(Session, c.user)
            conn.SetFilter('domain_name', crcs)
        q = clean_sphinx_q(q)
        results = conn.Query(q, 'domains, domains_rt')
        q = restore_sphinx_q(q)
        if results and results['matches']:
            ids = [hit['id'] for hit in results['matches']]
            domains = Session.query(Domain)\
                    .options(joinedload('organizations'))\
                    .filter(Domain.id.in_(ids))\
                    .all()
            total_found = results['total_found']
            search_time = results['time']
            domaincount = total_found
        else:
            domains = []
            domaincount = 0

        c.page = paginate.Page(domains, page=page,
                                items_per_page=num_items,
                                item_count=domaincount,
                                **kwds)
        c.q = q
        c.org = org
        c.total_found = total_found
        c.search_time = search_time
        return render('/domains/searchresults.html')

    @ActionProtector(OnlySuperUsers())
    def add(self, orgid=None):
        "Add a domain"
        c.form = AddDomainForm(request.POST, csrf_context=session)
        c.form.organizations.query = self._get_organizations(orgid)
        if request.POST and c.form.validate():
            try:
                domain = Domain()
                for field in c.form:
                    if field.name != 'csrf_token':
                        setattr(domain, field.name, field.data)
                Session.add(domain)
                Session.commit()
                update_serial.delay()
                info = ADDDOMAIN_MSG % dict(d=domain.name)
                audit_log(c.user.username,
                        3, unicode(info), request.host,
                        request.remote_addr, now())
                flash(_('The domain: %(dom)s has been created') %
                    dict(dom=domain.name))
                redirect(url(controller='domains'))
            except IntegrityError:
                Session.rollback()
                flash_alert(_('The domain name %(dom)s already exists') %
                    dict(dom=domain.name))

        return render('/domains/new.html')

    @ActionProtector(OwnsDomain())
    def detail(self, domainid):
        "Domain details"
        domain = self._get_domain(domainid)
        if not domain:
            abort(404)
        c.domain = domain
        return render('/domains/detail.html')

    @ActionProtector(OwnsDomain())
    def edit(self, domainid):
        "Edit a domain"
        domain = self._get_domain(domainid)
        if not domain:
            abort(404)
        c.form = EditDomainForm(request.POST, domain, csrf_context=session)
        if c.user.is_superadmin:
            c.form.organizations.query_factory = self._get_organizations
        else:
            del c.form.organizations
        c.id = domainid
        if request.POST and c.form.validate():
            updated = False
            kw = {'domainid': domain.id}
            for field in c.form:
                intfields = ['spam_actions', 'highspam_actions',
                            'delivery_mode', 'report_every']
                if (field.name in intfields and
                    int(field.data) == getattr(domain, field.name)):
                    continue
                if (field.name != 'csrf_token' and
                    field.data != getattr(domain, field.name)):
                    setattr(domain, field.name, field.data)
                    updated = True
            if updated:
                try:
                    Session.add(domain)
                    Session.commit()
                    update_serial.delay()
                    info = UPDATEDOMAIN_MSG % dict(d=domain.name)
                    audit_log(c.user.username,
                            2, unicode(info), request.host,
                            request.remote_addr, now())
                    flash(_('The domain: %(dom)s has been updated') %
                        dict(dom=domain.name))
                    kw['uc'] = 1
                except IntegrityError:
                    Session.rollback()
                    flash(_('The domain %(dom)s could not be updated') %
                        dict(dom=domain.name))
            else:
                flash_info(_('No changes were made to the domain'))
            redirect(url('domain-detail', **kw))
        return render('/domains/edit.html')

    @ActionProtector(OwnsDomain())
    def delete(self, domainid):
        "Delete a domain"
        domain = self._get_domain(domainid)
        if not domain:
            abort(404)
        c.form = EditDomainForm(request.POST, domain, csrf_context=session)
        del c.form.organizations
        c.id = domainid
        if request.POST and c.form.validate():
            name = domain.name
            Session.delete(domain)
            Session.commit()
            update_serial.delay()
            info = DELETEDOMAIN_MSG % dict(d=name)
            audit_log(c.user.username,
                    4, unicode(info), request.host,
                    request.remote_addr, now())
            flash(_('The domain has been deleted'))
            redirect(url(controller='domains'))
        else:
            flash(_('The domain: %(name)s and all associated data will'
                ' be deleted, This action cannot be reversed.') %
                dict(name=domain.name))
        return render('/domains/delete.html')

    def confirm_delete(self):
        "Confirm bulk delete of domains"
        domainids = session.get('bulk_domain_delete', [])
        if not domainids:
            redirect(url(controller='domains', action='index'))

        num_items = 10
        if len(domainids) > num_items and len(domainids) <= 20:
            num_items = 20
        if len(domainids) > num_items and len(domainids) <= 50:
            num_items = 50
        if len(domainids) > num_items and len(domainids) <= 100:
            num_items = 100

        domains = Session.query(Domain).filter(Domain.id.in_(domainids))\
                    .options(joinedload('organizations'))
        domcount = Session.query(Domain.id).filter(Domain.id.in_(domainids))

        if c.user.is_domain_admin:
            domains = domains.join(domain_owners,
                        (oa,
                        domain_owners.c.organization_id ==
                        oa.c.organization_id))\
                        .filter(oa.c.user_id == c.user.id)
            domcount = domcount.join(domain_owners,
                        (oa, domain_owners.c.organization_id ==
                        oa.c.organization_id))\
                        .filter(oa.c.user_id == c.user.id)

        if request.POST:
            tasks = []
            for domain in domains.all():
                info = DELETEDOMAIN_MSG % dict(d=domain.name)
                tasks.append((c.user.username,
                        4, unicode(info), request.host,
                        request.remote_addr,
                        now()))
                Session.delete(domain)
            Session.commit()
            del session['bulk_domain_delete']
            session.save()
            for task in tasks:
                audit_log(*task)
            flash(_('The domains have been deleted'))
            redirect(url(controller='domains'))
        else:
            flash(_('The following domains are about to be deleted,'
                    ' this action is not reversible, Do you wish to'
                    ' continue ?'))

        try:
            c.page = paginate.Page(domains, page=1,
                                    items_per_page=num_items,
                                    item_count=domcount.count())
        except DataError:
            flash_alert(_('An error occured try again'))
            redirect(url(controller='domains', action='index'))
        return render('/domains/confirmbulkdel.html')

    @ActionProtector(OwnsDomain())
    def adddestination(self, domainid):
        "Add a destination server"
        domain = self._get_domain(domainid)
        if not domain:
            abort(404)
        c.form = AddDeliveryServerForm(request.POST, csrf_context=session)
        c.id = domainid
        if request.POST and c.form.validate():
            server = DeliveryServer()
            for field in c.form:
                if field.name != 'csrf_token':
                    setattr(server, field.name, field.data)
            try:
                domain.servers.append(server)
                Session.add(server)
                Session.add(domain)
                Session.commit()
                info = ADDDELSVR_MSG % dict(d=domain.name, ds=server.address)
                audit_log(c.user.username,
                        3, unicode(info), request.host,
                        request.remote_addr, now())
                flash(_('The destination server has been created'))
                redirect(url(controller='domains', action='detail',
                        domainid=domain.id))
            except IntegrityError:
                Session.rollback()
                flash_alert(
                    _('The destination server %(dest)s already exists ') %
                    dict(dest=server.address))
        return render('/domains/adddestination.html')

    @ActionProtector(OwnsDomain())
    def editdestination(self, destinationid):
        "Edit destination server"
        server = self._get_server(destinationid)
        if not server:
            abort(404)
        c.form = AddDeliveryServerForm(request.POST,
                                        server,
                                        csrf_context=session)
        if request.POST and c.form.validate():
            updated = False
            kw = dict(domainid=server.domain_id)
            for field in c.form:
                if (field.name != 'csrf_token' and
                    field.data != getattr(server, field.name)):
                    setattr(server, field.name, field.data)
                    updated = True
            if updated:
                try:
                    Session.add(server)
                    Session.commit()
                    flash(_('The destination server has been updated'))
                    info = UPDATEDELSVR_MSG % dict(d=server.domains.name,
                                                    ds=server.address)
                    audit_log(c.user.username,
                            2, unicode(info), request.host,
                            request.remote_addr, now())
                    self.invalidate = 1
                    self._get_server(destinationid)
                    redirect(url('domain-detail', **kw))
                except IntegrityError:
                    Session.rollback()
                    flash_alert(_('The update failed'))
            else:
                flash_info(_('No changes were made to the destination server'))
                redirect(url('domain-detail', **kw))
        c.id = destinationid
        c.domainid = server.domain_id
        return render('/domains/editdestination.html')

    @ActionProtector(OwnsDomain())
    def testdestination(self, destinationid):
        "Test mail destination server"
        server = self._get_server(destinationid)
        if not server:
            abort(404)

        taskid = request.GET.get('taskid', None)
        if not taskid:
            to_addr = 'postmaster@%s' % server.domains.name
            task = test_smtp_server.apply_async(args=[
                                    server.address,
                                    server.port,
                                    '<>',
                                    to_addr,
                                    server.id,
                                    3])
            taskid = task.task_id
            session['taskids'].append(taskid)
            session['testdest-count'] = 1
            session.save()
            redirect(url.current(taskid=taskid))
        else:
            result = AsyncResult(taskid)
            if result is None or taskid not in session['taskids']:
                flash(_('The connection test failed try again later'))
                redirect(url('domain-detail', domainid=server.domain_id))
            if result.ready():
                if ('smtp' in result.result and 'ping' in result.result
                    and result.result['smtp'] and result.result['ping']):
                    flash(_('The server: %s is up and accepting mail from us'
                        % server.address))
                else:
                    if 'ping' in result.result['errors']:
                        errors = result.result['errors']['ping']
                    else:
                        errors = result.result['errors']['smtp']
                    flash(_('The server: %s is not accepting mail from us: %s')
                        % (server.address, errors))
                redirect(url('domain-detail', domainid=server.domain_id))
            else:
                session['testdest-count'] += 1
                session.save()
                if (session['testdest-count'] >= 10 and
                    result.state in ['PENDING', 'RETRY', 'FAILURE']):
                    result.revoke()
                    del session['testdest-count']
                    session.save()
                    flash_alert('Failed to initialize backend,'
                                ' try again later')
                    redirect(url('domain-detail', domainid=server.domain_id))

        c.server = server
        c.domainid = server.domain_id
        c.taskid = taskid
        c.finished = False
        return render('/domains/testdestination.html')

    @ActionProtector(OwnsDomain())
    def deletedestination(self, destinationid):
        "Delete destination server"
        server = self._get_server(destinationid)
        if not server:
            abort(404)
        c.form = AddDeliveryServerForm(request.POST,
                                        server,
                                        csrf_context=session)
        if request.POST and c.form.validate():
            name = server.domains.name
            server_addr = server.address
            domainid = server.domain_id
            Session.delete(server)
            Session.commit()
            flash(_('The destination server has been deleted'))
            info = DELETEDELSVR_MSG % dict(d=name, ds=server_addr)
            audit_log(c.user.username,
                    4, unicode(info), request.host,
                    request.remote_addr, now())
            redirect(url('domain-detail', domainid=domainid))
        else:
            flash(_('The destination server: %(s)s will be deleted,'
                ' This action is not reversible') % dict(s=server.address))
        c.id = destinationid
        c.domainid = server.domain_id
        return render('/domains/deletedestination.html')

    @ActionProtector(OwnsDomain())
    def add_auth(self, domainid):
        "Add auth server"
        domain = self._get_domain(domainid)
        if not domain:
            abort(404)
        c.form = AddAuthForm(request.POST, csrf_context=session)
        if request.POST and c.form.validate():
            server = AuthServer()
            for field in c.form:
                if field.data and field.name != 'csrf_token':
                    setattr(server, field.name, field.data)
            try:
                domain.authservers.append(server)
                Session.add(server)
                Session.add(domain)
                Session.commit()
                info = ADDAUTHSVR_MSG % dict(d=domain.name, ds=server.address)
                audit_log(c.user.username,
                        3, unicode(info), request.host,
                        request.remote_addr, now())
                flash(_('The authentication settings have been created'))
                redirect(url(controller='domains', action='detail',
                        domainid=domain.id))
            except IntegrityError:
                Session.rollback()
                auth = dict(AUTH_PROTOCOLS)[str(server.protocol)]
                flash_alert(
                    _('The host %(dest)s already configured for %(auth)s '
                    'authentication for this domain') %
                    dict(dest=server.address, auth=auth))
        c.domainid = domainid
        c.domainname = domain.name
        return render('/domains/addauth.html')

    @ActionProtector(OwnsDomain())
    def edit_auth(self, authid):
        "Edit auth server"
        server = self._get_authserver(authid)
        if not server:
            abort(404)
        c.form = AddAuthForm(request.POST, server, csrf_context=session)
        #del c.form.protocol
        if request.POST and c.form.validate():
            updated = False
            kw = dict(domainid=server.domain_id)
            for field in c.form:
                if field.name == 'protocol' or field.name == 'csrf_token':
                    continue
                if (field.data != getattr(server, field.name)
                    and field.data != ''):
                    setattr(server, field.name, field.data)
                    updated = True
                if (field.name == 'user_map_template' and
                    field.data != getattr(server, field.name)):
                    setattr(server, field.name, field.data)
                    updated = True
            if updated:
                try:
                    Session.add(server)
                    Session.commit()
                    flash(_('The authentication settings have been updated'))
                    self.invalidate = 1
                    self._get_authserver(authid)
                    info = UPDATEAUTHSVR_MSG % dict(d=server.domains.name,
                                                    ds=server.address)
                    audit_log(c.user.username,
                            2, unicode(info), request.host,
                            request.remote_addr, now())
                    redirect(url('domain-detail', **kw))
                except IntegrityError:
                    Session.rollback()
                    flash_alert(_('The authentication settings update failed'))
            else:
                flash_info(_('No changes were made to the '
                            'authentication settings'))
                redirect(url('domain-detail', **kw))
        c.domainid = server.domains.id
        c.domainname = server.domains.name
        c.authid = authid
        return render('/domains/editauth.html')

    @ActionProtector(OwnsDomain())
    def delete_auth(self, authid):
        "Delete auth server"
        server = self._get_authserver(authid)
        if not server:
            abort(404)
        c.form = AddAuthForm(request.POST, server, csrf_context=session)
        if request.POST and c.form.validate():
            name = server.domains.name
            server_addr = server.address
            domainid = server.domains.id
            Session.delete(server)
            Session.commit()
            flash(_('The authentication settings have been deleted'))
            info = DELETEAUTHSVR_MSG % dict(d=name, ds=server_addr)
            audit_log(c.user.username,
                    4, unicode(info), request.host,
                    request.remote_addr, now())
            redirect(url('domain-detail', domainid=domainid))
        else:
            flash(_('The authentication server: %(s)s will be deleted,'
                ' This action is not reversible') % dict(s=server.address))
        c.domainid = server.domains.id
        c.domainname = server.domains.name
        c.authid = authid
        return render('/domains/deleteauth.html')

    @ActionProtector(OwnsDomain())
    def auth_settings(self, domainid, proto=5):
        "Authentication settings"
        domain = self._get_domain(domainid)
        if not domain:
            abort(404)
        try:
            protocols = {'4': 'radius',
                        '5': 'ldap',
                        '6': 'yubikey',
                        '7': 'oauth'}
            protocol = protocols[proto]
            server = Session.query(AuthServer)\
                    .filter(AuthServer.domain_id == domainid)\
                    .filter(AuthServer.protocol == proto).one()
        except KeyError:
            flash_alert(_('The protocol supplied does not use extra settings'))
            redirect(url(controller='domains',
                    action='detail',
                    domainid=domain.id))
        except NoResultFound:
            flash_alert(_('Please add an authentication server for the '
                '%(proto)s protocol Before attempting to configure '
                'the %(proto)s settings')
            % dict(proto=proto))
            redirect(url(controller='domains',
                    action='detail',
                    domainid=domain.id))
        forms = {'4': AddRadiusSettingsForm, '5': AddLDAPSettingsForm}
        form = forms[proto]
        if (hasattr(server, protocol + 'settings') and
            getattr(server, protocol + 'settings')):
            authobj = getattr(server, protocol + 'settings')[0]
            c.form = form(request.POST, authobj, csrf_context=session)
        else:
            authobj = None
            c.form = form(request.POST, csrf_context=session)
        if request.POST and c.form.validate():
            updated = False
            if authobj:
                settings = getattr(server, protocol + 'settings')[0]
            else:
                settingsdict = {'4': RadiusSettings, '5': LDAPSettings}
                settings = settingsdict[proto]()
            for field in c.form:
                if field.name == 'csrf_token':
                    continue
                if authobj:
                    if getattr(settings, field.name) != field.data:
                        setattr(settings, field.name, field.data)
                        updated = True
                else:
                    setattr(settings, field.name, field.data)
            try:
                if authobj is None:
                    settings.auth_id = server.id
                if updated or authobj is None:
                    Session.add(settings)
                    Session.commit()
                if authobj:
                    flash(_('The %(proto)s settings have been updated')
                        % dict(proto=protocol))
                else:
                    flash(_('The %(proto)s settings have been created') 
                        % dict(proto=protocol))
                info = AUTHSETTINGS_MSG % dict(d=domain.name, a=proto)
                audit_log(c.user.username,
                        2, unicode(info), request.host,
                        request.remote_addr, now())
                redirect(url(controller='domains', action='detail',
                domainid=domain.id))
            except IntegrityError:
                Session.rollback()
                flash_alert(
                    _('The auth settings already exist, '
                    'use update to modify them'))
        else:
            if proto == '4' and 'authobj' in locals():
                flash(_('The Radius secret is not be displayed in'
                    ' the form, To update type the new secret in '
                    '"Radius secret" below.'))
        c.domain = domain
        c.proto = proto
        return render('/domains/authsettings.html')

    @ActionProtector(OwnsDomain())
    def rulesets(self, domainid):
        "Scanner rulesets"
        domain = self._get_domain(domainid)
        if not domain:
            abort(404)
        c.domainid = domain.id
        c.domainname = domain.name
        return render('/domains/rulesets.html')

    @ActionProtector(OwnsDomain())
    def addalias(self, domainid):
        "Add alias domain"
        domain = self._get_domain(domainid)
        if not domain:
            abort(404)

        c.form = AddDomainAlias(request.POST, csrf_context=session)
        c.form.domain.query = Session.query(Domain).filter(Domain.id==domainid)
        if request.POST and c.form.validate():
            alias = DomainAlias()
            for field in c.form:
                if field.data and field.name != 'csrf_token':
                    setattr(alias, field.name, field.data)
            try:
                domain.aliases.append(alias)
                Session.add(alias)
                Session.add(domain)
                Session.commit()
                update_serial.delay()
                info = ADDDOMALIAS_MSG % dict(d=alias.name)
                audit_log(c.user.username,
                        3, unicode(info), request.host,
                        request.remote_addr, now())
                flash(_('The domain alias: %s has been created') % alias.name)
                redirect(url(controller='domains', action='detail',
                        domainid=domain.id))
            except IntegrityError:
                Session.rollback()
                flash_alert(_('The domain alias: %s already exists') %
                            alias.name)

        c.domainid = domain.id
        c.domainname = domain.name
        return render('/domains/addalias.html')

    def editalias(self, aliasid):
        "Edit alias domain"
        alias = self._get_alias(aliasid)
        if not alias:
            abort(404)

        c.form = EditDomainAlias(request.POST, alias, csrf_context=session)
        c.form.domain.query = Session.query(Domain)\
                            .filter(Domain.id==alias.domain_id)
        if request.POST and c.form.validate():
            updated = False
            for field in c.form:
                if (field.name != 'csrf_token' and
                    field.data != getattr(alias, field.name)):
                    setattr(alias, field.name, field.data)
                    updated = True
            if updated:
                try:
                    Session.add(alias)
                    Session.commit()
                    update_serial.delay()
                    info = UPDATEDOMALIAS_MSG % dict(d=alias.name)
                    audit_log(c.user.username,
                            2, unicode(info), request.host,
                            request.remote_addr, now())
                    flash(_('The domain alias: %s has been updated') %
                            alias.name)
                    redirect(url('domain-detail', domainid=alias.domain_id))
                except IntegrityError:
                    Session.rollback()
                    flash_alert(_('The update failed'))
            else:
                flash_info(_('No changes were made to the domain alias'))
                redirect(url('domain-detail', domainid=alias.domain_id))

        c.aliasid = aliasid
        c.domainid = alias.domain_id
        c.domainname = alias.domain.name
        return render('/domains/editalias.html')

    def deletealias(self, aliasid):
        "Delete alias domain"
        alias = self._get_alias(aliasid)
        if not alias:
            abort(404)

        c.form = DelDomainAlias(request.POST, alias, csrf_context=session)
        c.form.domain.query = Session.query(Domain)\
                            .filter(Domain.id==alias.domain_id)
        if request.POST and c.form.validate():
            domainid = alias.domain_id
            aliasname = alias.name
            Session.delete(alias)
            Session.commit()
            update_serial.delay()
            info = DELETEDOMALIAS_MSG % dict(d=aliasname)
            audit_log(c.user.username,
                    4, unicode(info), request.host,
                    request.remote_addr, now())
            flash(_('The domain alias: %s has been deleted') % aliasname)
            redirect(url('domain-detail', domainid=domainid))

        c.aliasid = aliasid
        c.domainid = alias.domain_id
        c.domainname = alias.domain.name
        return render('/domains/deletealias.html')

    def export_domains(self, orgid=None):
        "export domains"
        task = exportdomains.apply_async(args=[
                c.user.id, orgid])
        session['taskids'].append(task.task_id)
        session['dexport-count'] = 1
        session.save()
        flash(_('Domains export is being processed'))
        redirect(url('domains-export-status', taskid=task.task_id))

    def export_status(self, taskid):
        "export status"
        result = AsyncResult(taskid)
        if result is None or taskid not in session['taskids']:
            flash(_('The task status requested has expired or does not exist'))
            redirect(url(controller='domains', action='index'))

        if result.ready():
            finished = True
            flash.pop_messages()
            if isinstance(result.result, Exception):
                if c.user.is_superadmin:
                    flash_alert(_('Error occured in processing %s') %
                                result.result)
                else:
                    flash_alert(_('Backend error occured during processing.'))
                redirect(url(controller='domains'))
            results = dict(
                        f=True if not result.result['global_error'] else False,
                        id=taskid, global_error=result.result['global_error'])
        else:
            session['dexport-count'] += 1
            if (session['dexport-count'] >= 10 and
                result.state in ['PENDING', 'RETRY', 'FAILURE']):
                result.revoke()
                flash_alert(_('The export could not be processed,'
                            ' try again later'))
                del session['dexport-count']
                session.save()
                redirect(url(controller='domains'))
            finished = False
            results = dict(f=None, global_error=None)

        c.finished = finished
        c.results = results
        c.success = result.successful()
        d = request.GET.get('d', None)
        if finished and (d and d == 'y'):
            info = EXPORTDOM_MSG % dict(d='all')
            audit_log(c.user.username,
                    5, unicode(info), request.host,
                    request.remote_addr, now())
            response.content_type = 'text/csv'
            response.headers['Cache-Control'] = 'max-age=0'
            csvdata = result.result['f']
            disposition = 'attachment; filename=domains-export-%s.csv' % taskid
            response.headers['Content-Disposition'] = str(disposition)
            response.headers['Content-Length'] = len(csvdata)
            return csvdata
        return render('/domains/exportstatus.html')

    def setnum(self, format=None):
        "Set number of items returned"
        num = check_num_param(request)

        if num and num in [10, 20, 50, 100]:
            session['domains_num_items'] = num
            session.save()
        nextpage = request.headers.get('Referer', '/')
        if '://' in nextpage:
            from_url = urlparse(nextpage)
            nextpage = from_url[2]
        redirect(nextpage)
