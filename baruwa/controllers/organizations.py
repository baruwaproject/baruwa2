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
"Organizations controller"

import os
import shutil
import logging

from urlparse import urlparse

from pylons import request, response, session, tmpl_context as c, url, config
from pylons.controllers.util import abort, redirect
from pylons.i18n.translation import _
from webhelpers import paginate
from celery.result import AsyncResult
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from repoze.what.predicates import All, not_anonymous
from sphinxapi import SphinxClient, SPH_MATCH_EXTENDED2
from repoze.what.plugins.pylonshq import ControllerProtector

from baruwa.lib.dates import now
from baruwa.lib.base import BaseController, render
from baruwa.lib.helpers import flash, flash_info, flash_alert
from baruwa.lib.query import clean_sphinx_q, restore_sphinx_q
from baruwa.lib.misc import check_num_param
from baruwa.lib.misc import iscsv, convert_org_to_json
from baruwa.model.meta import Session
from baruwa.lib.audit import audit_log
from baruwa.lib.auth.predicates import OnlySuperUsers
from baruwa.tasks.settings import update_serial
from baruwa.model.accounts import Group, User, Relay
from baruwa.model.domains import Domain
from baruwa.forms.organizations import OrgForm, RelayForm, RelayEditForm
from baruwa.forms.organizations import DelOrgForm
from baruwa.forms.organizations import ImportCSVForm
from baruwa.tasks import importdomains
from baruwa.lib.audit.msgs.organizations import *

log = logging.getLogger(__name__)


@ControllerProtector(All(not_anonymous(), OnlySuperUsers()))
class OrganizationsController(BaseController):
    def __before__(self):
        "set context"
        BaseController.__before__(self)
        if self.identity:
            c.user = self.identity['user']
        else:
            c.user = None
        c.selectedtab = 'organizations'

    def _get_org(self, orgid):
        "Get organization"
        try:
            org = Session.query(Group).options(
                joinedload('domains')).get(orgid)
        except NoResultFound:
            org = None
        return org

    def _get_setting(self, settingid):
        "Get relay settings"
        try:
            setting = Session.query(Relay).options(
                    joinedload('org')).get(settingid)
        except NoResultFound:
            setting = None
        return setting

    def index(self, page=1, format=None):
        "index page"
        total_found = 0
        search_time = 0
        num_items = session.get('organizations_num_items', 10)
        q = request.GET.get('q', None)
        kwds = {}
        if q:
            kwds['presliced_list'] = True
            conn = SphinxClient()
            conn.SetMatchMode(SPH_MATCH_EXTENDED2)
            if page == 1:
                conn.SetLimits(0, num_items, 500)
            else:
                page = int(page)
                offset = (page - 1) * num_items
                conn.SetLimits(offset, num_items, 500)
            q = clean_sphinx_q(q)
            results = conn.Query(q, 'organizations, organizations_rt')
            q = restore_sphinx_q(q)
            if results and results['matches']:
                ids = [hit['id'] for hit in results['matches']]
                orgs = Session.query(Group)\
                        .filter(Group.id.in_(ids))\
                        .all()
                total_found = results['total_found']
                search_time = results['time']
                orgcount = total_found
            else:
                orgs = []
                ocount = 0
                orgcount = 0
        else:
            orgs = Session.query(Group)
            ocount = Session.query(Group.id)
        if not 'orgcount' in locals():
            orgcount = ocount.count()
        items = paginate.Page(orgs, page=int(page),
                            items_per_page=num_items,
                            item_count=orgcount,
                            **kwds)
        if format == 'json':
            response.headers['Content-Type'] = 'application/json'
            data = convert_org_to_json(items)
            return data

        c.page = items
        c.q = q
        c.total_found = total_found
        c.search_time = search_time
        return render('/organizations/index.html')

    def detail(self, orgid):
        "Organization details"
        org = self._get_org(orgid)
        if not org:
            abort(404)
        c.org = org
        return render('/organizations/detail.html')

    def new(self):
        "Add an organization"
        c.form = OrgForm(request.POST, csrf_context=session)
        c.form.domains.query = Session.query(Domain)
        c.form.admins.query = Session.query(User).filter(
                                User.account_type == 2)
        if request.POST and c.form.validate():
            try:
                org = Group()
                org.name = c.form.name.data
                org.domains = c.form.domains.data
                Session.add(org)
                Session.commit()
                info = ADDORG_MSG % dict(o=org.name)
                audit_log(c.user.username,
                        3, unicode(info), request.host,
                        request.remote_addr, now())
                flash(_('The organization has been created'))
                redirect(url(controller='organizations'))
            except IntegrityError:
                Session.rollback()
                flash_alert(_('The organization already exists'))
        return render('/organizations/add.html')

    def edit(self, orgid):
        "Edit an organization"
        org = self._get_org(orgid)
        if not org:
            abort(404)

        c.form = OrgForm(request.POST, org, csrf_context=session)
        c.form.domains.query = Session.query(Domain)
        c.form.admins.query = Session.query(User).filter(
                                User.account_type == 2)
        c.id = org.id
        if request.POST and c.form.validate():
            updated = False
            for field in c.form:
                if (field.name != 'csrf_token' and
                    field.data != getattr(org, field.name)):
                    setattr(org, field.name, field.data)
                    updated = True
            if updated:
                try:
                    Session.add(org)
                    Session.commit()
                    info = UPDATEORG_MSG % dict(o=org.name)
                    audit_log(c.user.username,
                            2, unicode(info), request.host,
                            request.remote_addr, now())
                    flash(_('The organization has been updated'))
                except IntegrityError:
                    Session.rollback()
                    flash(_('The organization could not be updated'))
            else:
                flash_info(_('No changes made, Organization not updated'))
            redirect(url(controller='organizations'))
        return render('/organizations/edit.html')

    def delete(self, orgid):
        "Delete an organization"
        org = self._get_org(orgid)
        if not org:
            abort(404)

        c.form = DelOrgForm(request.POST, org, csrf_context=session)
        c.form.domains.query = Session.query(Domain)
        c.form.admins.query = Session.query(User).filter(
                                User.account_type == 2)
        c.id = org.id
        if request.POST and c.form.validate():
            org_name = org.name
            if c.form.delete_domains.data:
                for domain in org.domains:
                    Session.delete(domain)
            Session.delete(org)
            Session.commit()
            info = DELETEORG_MSG % dict(o=org_name)
            audit_log(c.user.username,
                    4, unicode(info), request.host,
                    request.remote_addr, now())
            flash(_('The organization has been deleted'))
            redirect(url(controller='organizations'))
        else:
            flash(_('The organization: %(s)s will be deleted,'
                ' This action is not reversible') % dict(s=org.name))
        return render('/organizations/delete.html')

    def add_relay(self, orgid):
        "Add a mail relay"
        org = self._get_org(orgid)
        if not org:
            abort(404)

        c.form = RelayForm(request.POST, csrf_context=session)
        if request.POST and c.form.validate():
            try:
                outbound = Relay()
                outbound.address = c.form.address.data
                outbound.username = c.form.username.data
                outbound.enabled = c.form.enabled.data
                outbound.org = org
                if c.form.password1.data:
                    outbound.set_password(c.form.password1.data)
                Session.add(outbound)
                Session.commit()
                relay_name = c.form.address.data or c.form.username.data
                info = ADDRELAY_MSG % dict(r=relay_name)
                audit_log(c.user.username,
                        3, unicode(info), request.host,
                        request.remote_addr, now())
                flash(_('The outbound settings have been created'))
            except IntegrityError:
                Session.rollback()
                flash(_('The outbound settings could not created, Try again'))
            redirect(url('org-detail', orgid=orgid))
        c.orgid = org.id
        c.orgname = org.name
        return render('/organizations/addrelay.html')

    def edit_relay(self, settingid):
        "Edit a mail relay"
        relay = self._get_setting(settingid)
        if not relay:
            abort(404)

        c.form = RelayEditForm(request.POST, relay, csrf_context=session)
        c.relayname = relay.address or relay.username
        c.relayid = relay.id
        c.orgid = relay.org_id
        if request.POST and c.form.validate():
            updated = False
            for field in c.form:
                if field.name == 'csrf_token':
                    continue
                if (not field.name in ['password1', 'password2'] and
                    field.data != getattr(relay, field.name)):
                    setattr(relay, field.name, field.data)
                    updated = True
                if field.name == 'password1' and field.data != '':
                    relay.set_password(field.data)
                    updated = True
            if updated:
                try:
                    Session.add(relay)
                    Session.commit()
                    info = UPDATERELAY_MSG % dict(r=c.relayname)
                    audit_log(c.user.username,
                            2, unicode(info), request.host,
                            request.remote_addr, now())
                    flash(_('The outbound settings have been updated'))
                except IntegrityError:
                    Session.rollback()
                    flash(_('The outbound settings could not be updated'))
            else:
                flash(_('No changes made, The outbound settings not updated'))
            redirect(url('org-detail', orgid=relay.org_id))
        return render('/organizations/editrelay.html')

    def delete_relay(self, settingid):
        "Delete a mail relay"
        relay = self._get_setting(settingid)
        if not relay:
            abort(404)

        c.form = RelayForm(request.POST, relay, csrf_context=session)
        c.relayname = relay.address or relay.username
        c.relayid = relay.id
        c.orgid = relay.org_id
        if request.POST and c.form.validate():
            orgid = relay.organization_id
            try:
                Session.delete(relay)
                Session.commit()
                info = DELETERELAY_MSG % dict(r=c.relayname)
                audit_log(c.user.username,
                        4, unicode(info), request.host,
                        request.remote_addr, now())
                flash(_('The outbound settings have been deleted'))
            except:
                flash(_('The outbound settings could not be deleted'))
            redirect(url('org-detail', orgid=orgid))
        return render('/organizations/deleterelay.html')

    def import_domains(self, orgid):
        "import domains from csv file"
        org = self._get_org(orgid)
        if not org:
            abort(404)

        c.form = ImportCSVForm(request.POST, csrf_context=session)
        if request.POST and c.form.validate():
            basedir = config['pylons.cache_dir']
            csvdata = request.POST['csvfile']
            if hasattr(csvdata, 'filename'):
                dstfile = os.path.join(basedir, 'uploads',
                            csvdata.filename.lstrip(os.sep))
                if not os.path.exists(dstfile) and iscsv(csvdata.file):
                    csvfile = open(dstfile, 'w')
                    shutil.copyfileobj(csvdata.file, csvfile)
                    csvdata.file.close()
                    csvfile.close()
                    task = importdomains.apply_async(args=[orgid,
                            dstfile, c.form.skipfirst.data])
                    if not 'taskids' in session:
                        session['taskids'] = []
                    session['taskids'].append(task.task_id)
                    session['dimport-counter'] = 1
                    session['dimport-file'] = dstfile
                    session.save()
                    flash(_('File uploaded, and is being processed, this page'
                            ' will automatically refresh to show the status'))
                    redirect(url('orgs-import-status', taskid=task.task_id))
                else:
                    filename = csvdata.filename.lstrip(os.sep)
                    if not iscsv(csvdata.file):
                        flash_alert(_('The file: %s is not a CSV file') %
                                    filename)
                    else:
                        flash_alert(_('The file: %s already exists '
                                'and is being processed.') % filename)
                    csvdata.file.close()
            else:
                flash_alert(_('No CSV was file uploaded, try again'))

        c.org = org
        return render('/organizations/importdomains.html')

    def import_status(self, taskid):
        "import domains status"
        result = AsyncResult(taskid)
        if result is None or taskid not in session['taskids']:
            flash(_('The task status requested has expired or does not exist'))
            redirect(url(controller='organizations', action='index'))

        if result.ready():
            finished = True
            flash.pop_messages()
            if isinstance(result.result, Exception):
                if c.user.is_superadmin:
                    flash_alert(_('Error occured in processing %s') %
                                result.result)
                else:
                    flash_alert(_('Backend error occured during processing.'))
                redirect(url(controller='organizations'))
            update_serial.delay()
            info = IMPORTORG_MSG % dict(o='-')
            audit_log(c.user.username,
                    3, unicode(info), request.host,
                    request.remote_addr, now())
        else:
            session['dimport-counter'] += 1
            session.save()
            if (session['dimport-counter'] >= 10 and
                result.state in ['PENDING', 'RETRY', 'FAILURE']):
                result.revoke()
                try:
                    os.unlink(session['dimport-file'])
                except OSError:
                    pass
                del session['dimport-file']
                del session['dimport-counter']
                session.save()
                flash_alert(_('The import could not be processed,'
                            ' try again later'))
                redirect(url(controller='organizations'))
            finished = False

        c.finished = finished
        c.results = result.result
        c.success = result.successful()
        return render('/organizations/importstatus.html')

    def setnum(self, format=None):
        "Set num of organizations returned"
        num = check_num_param(request)

        if num and num in [10, 20, 50, 100]:
            session['organizations_num_items'] = num
            session.save()
        nextpage = request.headers.get('Referer', '/')
        if '://' in nextpage:
            from_url = urlparse(nextpage)
            nextpage = from_url[2]
        redirect(nextpage)
