# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4
# Baruwa - Web 2.0 MailScanner front-end.
# Copyright (C) 2010-2015  Andrew Colin Kissa <andrew@topdog.za.net>
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
import socket
import struct
import logging

import arrow

from urlparse import urlparse

from pylons import request, response, session, tmpl_context as c, url, config
from pylons.controllers.util import abort, redirect
from pylons.i18n.translation import _
from webhelpers import paginate
from celery.result import AsyncResult
from sqlalchemy.exc import IntegrityError
from repoze.what.predicates import All, not_anonymous
from sphinxapi import SphinxClient, SPH_MATCH_EXTENDED2
from repoze.what.plugins.pylonshq import ControllerProtector

from baruwa.lib.base import BaseController
from baruwa.lib.helpers import flash, flash_info, flash_alert
from baruwa.lib.query import clean_sphinx_q, restore_sphinx_q
from baruwa.lib.misc import check_num_param, extract_sphinx_opts
from baruwa.lib.misc import iscsv, convert_org_to_json
from baruwa.model.meta import Session
from baruwa.lib.audit import audit_log
from baruwa.lib.auth.predicates import OnlySuperUsers
from baruwa.tasks.settings import update_serial
from baruwa.model.accounts import Group
from baruwa.forms.organizations import RelayForm, RelayEditForm
from baruwa.forms.organizations import ImportCSVForm
from baruwa.tasks import importdomains
from baruwa.lib.audit.msgs import organizations as auditmsgs
from baruwa.lib.api import org_add_form, create_org, edit_org, delete_org, \
    update_if_changed, org_delete_form, relay_update_if_changed, add_relay, \
    edit_relay, delete_relay, get_org, get_relay


log = logging.getLogger(__name__)


@ControllerProtector(All(not_anonymous(), OnlySuperUsers()))
class OrganizationsController(BaseController):
    "Organizations controller"
    def __before__(self):
        "set context"
        BaseController.__before__(self)
        if self.identity:
            c.user = self.identity['user']
        else:
            c.user = None
        c.selectedtab = 'organizations'

    def index(self, page=1, format=None):
        "index page"
        total_found = 0
        search_time = 0
        num_items = session.get('organizations_num_items', 10)
        qry = request.GET.get('q', None)
        kwds = {}
        if qry:
            kwds['presliced_list'] = True
            conn = SphinxClient()
            sphinxopts = extract_sphinx_opts(config['sphinx.url'])
            conn.SetServer(sphinxopts.get('host', '127.0.0.1'))
            conn.SetMatchMode(SPH_MATCH_EXTENDED2)
            if page == 1:
                conn.SetLimits(0, num_items, 500)
            else:
                page = int(page)
                offset = (page - 1) * num_items
                conn.SetLimits(offset, num_items, 500)
            qry = clean_sphinx_q(qry)
            try:
                results = conn.Query(qry, 'organizations, organizations_rt')
            except (socket.timeout, struct.error):
                redirect(request.path_qs)
            qry = restore_sphinx_q(qry)
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
        if 'orgcount' not in locals():
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
        c.q = qry
        c.total_found = total_found
        c.search_time = search_time
        return self.render('/organizations/index.html')

    def detail(self, orgid):
        "Organization details"
        org = get_org(orgid)
        if not org:
            abort(404)
        c.org = org
        return self.render('/organizations/detail.html')

    def new(self):
        "Add an organization"
        c.form = org_add_form(request.POST, session)
        if request.method == 'POST' and c.form.validate():
            try:
                org = create_org(c.form, c.user, request.host,
                            request.remote_addr)
                msg = _('The organization: %s has been created') % org.name
                flash(msg)
                log.info(msg)
                redirect(url(controller='organizations'))
            except IntegrityError:
                Session.rollback()
                flash_alert(_('The organization already exists'))
        return self.render('/organizations/add.html')

    def edit(self, orgid):
        "Edit an organization"
        org = get_org(orgid)
        if not org:
            abort(404)

        c.id = org.id
        c.form = org_add_form(request.POST, session, org)
        if request.method == 'POST' and c.form.validate():
            if update_if_changed(c.form, org):
                try:
                    edit_org(org, c.user, request.host, request.remote_addr)
                    msg = _('The organization has been updated')
                    flash(msg)
                    log.info(msg)
                except IntegrityError:
                    Session.rollback()
                    msg = _('The organization could not be updated')
                    flash(msg)
                    log.info(msg)
            else:
                msg = _('No changes made, Organization not updated')
                flash_info(msg)
                log.info(msg)
            redirect(url(controller='organizations'))
        return self.render('/organizations/edit.html')

    def delete(self, orgid):
        "Delete an organization"
        org = get_org(orgid)
        if not org:
            abort(404)

        c.id = org.id
        c.form = org_delete_form(request.POST, session, org)
        if request.method == 'POST' and c.form.validate():
            delete_org(c.form, org, c.user, request.host,
                        request.remote_addr)
            msg = _('The organization has been deleted')
            flash(msg)
            log.info(msg)
            redirect(url(controller='organizations'))
        else:
            msg = _('The organization: %(s)s will be deleted,'
                ' This action is not reversible') % dict(s=org.name)
            flash(msg)
            log.info(msg)
        return self.render('/organizations/delete.html')

    def add_relay(self, orgid):
        "Add a mail relay"
        org = get_org(orgid)
        if not org:
            abort(404)

        c.form = RelayForm(request.POST, csrf_context=session)
        if request.method == 'POST' and c.form.validate():
            try:
                relay = add_relay(c.form, org, c.user, request.host,
                                    request.remote_addr)
                name = relay.address or relay.username
                msg = _('The outbound settings: %s have been created') % name
                flash(msg)
                log.info(msg)
            except IntegrityError:
                Session.rollback()
                msg = _('The outbound settings could not created, Try again')
                flash(msg)
                log.info(msg)
            redirect(url('org-detail', orgid=orgid))
        c.orgid = org.id
        c.orgname = org.name
        return self.render('/organizations/addrelay.html')

    def edit_relay(self, settingid):
        "Edit a mail relay"
        relay = get_relay(settingid)
        if not relay:
            abort(404)

        c.relayname = relay.address or relay.username
        c.relayid = relay.id
        c.orgid = relay.org_id
        c.form = RelayEditForm(request.POST, relay, csrf_context=session)
        if request.method == 'POST' and c.form.validate():
            if relay_update_if_changed(c.form, relay):
                try:
                    edit_relay(relay, c.user, request.host,
                                request.remote_addr)
                    msg = _('The outbound settings have been updated')
                    flash(msg)
                    log.info(msg)
                except IntegrityError:
                    Session.rollback()
                    msg = _('The outbound settings could not be updated')
                    flash(msg)
                    log.info(msg)
            else:
                msg = _('No changes made, The outbound settings not updated')
                flash(msg)
                log.info(msg)
            redirect(url('org-detail', orgid=relay.org_id))
        return self.render('/organizations/editrelay.html')

    def delete_relay(self, settingid):
        "Delete a mail relay"
        relay = get_relay(settingid)
        if not relay:
            abort(404)

        c.relayname = relay.address or relay.username
        c.relayid = relay.id
        c.orgid = relay.org_id
        c.form = RelayForm(request.POST, relay, csrf_context=session)
        if request.method == 'POST' and c.form.validate():
            orgid = relay.org_id
            try:
                delete_relay(relay, c.user, request.host, request.remote_addr)
                msg = _('The outbound settings have been deleted')
                flash(msg)
                log.info(msg)
            except:
                msg = _('The outbound settings could not be deleted')
                flash(msg)
                log.info(msg)
            redirect(url('org-detail', orgid=orgid))
        return self.render('/organizations/deleterelay.html')

    def import_domains(self, orgid):
        "import domains from csv file"
        org = get_org(orgid)
        if not org:
            abort(404)

        c.form = ImportCSVForm(request.POST, csrf_context=session)
        if request.method == 'POST' and c.form.validate():
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
                    if 'taskids' not in session:
                        session['taskids'] = []
                    session['taskids'].append(task.task_id)
                    session['dimport-counter'] = 1
                    session['dimport-file'] = dstfile
                    session.save()
                    msg = _('File uploaded, and is being processed, this page'
                            ' will automatically refresh to show the status')
                    flash(msg)
                    log.info(msg)
                    redirect(url('orgs-import-status', taskid=task.task_id))
                else:
                    filename = csvdata.filename.lstrip(os.sep)
                    if not iscsv(csvdata.file):
                        msg = _('The file: %s is not a CSV file') % filename
                        flash_alert(msg)
                        log.info(msg)
                    else:
                        msg = _('The file: %s already exists '
                                'and is being processed.') % filename
                        flash_alert(msg)
                        log.info(msg)
                    csvdata.file.close()
            else:
                msg = _('No CSV was file uploaded, try again')
                flash_alert(msg)
                log.info(msg)

        c.org = org
        return self.render('/organizations/importdomains.html')

    def import_status(self, taskid):
        "import domains status"
        result = AsyncResult(taskid)
        if result is None or taskid not in session['taskids']:
            msg = _('The task status requested has expired or does not exist')
            flash(msg)
            log.info(msg)
            redirect(url(controller='organizations', action='index'))

        if result.ready():
            finished = True
            flash.pop_messages()
            if isinstance(result.result, Exception):
                msg = _('Error occured in processing %s') % result.result
                if c.user.is_superadmin:
                    flash_alert(msg)
                    log.info(msg)
                else:
                    flash_alert(_('Backend error occured during processing.'))
                    log.info(msg)
                redirect(url(controller='organizations'))
            update_serial.delay()
            info = auditmsgs.IMPORTORG_MSG % dict(o='-')
            audit_log(c.user.username,
                    3, unicode(info), request.host,
                    request.remote_addr, arrow.utcnow().datetime)
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
        return self.render('/organizations/importstatus.html')

    # pylint: disable-msg=R0201
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
