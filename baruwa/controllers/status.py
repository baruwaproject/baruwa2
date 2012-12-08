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

import json
import base64
import logging

from urlparse import urlparse
from cStringIO import StringIO

from pylons import response, request, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from pylons.i18n.translation import _
from repoze.what.predicates import All, not_anonymous
from repoze.what.plugins.pylonshq import ActionProtector
from repoze.what.plugins.pylonshq import ControllerProtector
from webhelpers import paginate
from reportlab.lib import colors
from sqlalchemy import desc
from webhelpers.html import literal
from celery.result import AsyncResult
from webhelpers.html.tags import link_to
from reportlab.graphics import renderPM
from sqlalchemy.orm.exc import NoResultFound
from lxml.html import fromstring, tostring, iterlinks
from sphinxapi import SphinxClient, SPH_MATCH_EXTENDED2
from celery.exceptions import TimeoutError, QueueNotFound

from baruwa.lib.dates import now
from baruwa.lib.base import BaseController, render
from baruwa.model.meta import Session
from baruwa.lib.helpers import flash, flash_alert
from baruwa.lib.graphs import PieChart
from baruwa.lib.query import UserFilter
from baruwa.lib.audit import audit_log
from baruwa.model.settings import Server
from baruwa.model.status import MailQueueItem, AuditLog
from baruwa.lib.graphs import PIE_CHART_COLORS
from baruwa.lib.misc import check_num_param
from baruwa.lib.misc import convert_settings_to_json
from baruwa.lib.templates.helpers import media_url
from baruwa.lib.query import DailyTotals, MailQueue
from baruwa.lib.query import clean_sphinx_q, restore_sphinx_q
from baruwa.tasks.status import export_auditlog
from baruwa.tasks.status import preview_queued_msg, process_queued_msgs
from baruwa.tasks.status import systemstatus, salint, bayesinfo
from baruwa.lib.auth.predicates import OnlySuperUsers, OnlyAdminUsers
from baruwa.forms.status import MailQueueProcessForm
from baruwa.lib.audit.msgs.status import QUEUEPREVIEW_MSG, QUEUEDOWNLOAD_MSG
from baruwa.lib.audit.msgs.status import HOSTSTATUS_MSG, HOSTSALINT_MSG
from baruwa.lib.audit.msgs.status import HOSTBAYES_MSG, AUDITLOGEXPORT_MSG

log = logging.getLogger(__name__)


@ControllerProtector(All(not_anonymous()))
class StatusController(BaseController):
    def __before__(self):
        "set context"
        BaseController.__before__(self)
        if self.identity:
            c.user = self.identity['user']
        else:
            c.user = None
        c.selectedtab = 'status'

    def _get_server(self, serverid):
        "utility"
        try:
            server = Session.query(Server).get(serverid)
        except NoResultFound:
            server = None
        return server

    @ActionProtector(OnlyAdminUsers())
    def index(self):
        "System status"
        c.servers = Session.query(Server).filter(
                    Server.hostname != 'default').all()
        labels = dict(clean=_('Clean'),
                    highspam=_('High scoring spam'),
                    lowspam=_('Low scoring spam'),
                    virii=_('Virus infected'),
                    infected=_('Policy blocked'))
        pie_colors = dict(clean='#006400',
                    highspam='#FF0000',
                    lowspam='#ffa07a',
                    virii='#000000',
                    infected='#d2691e')
        jsondata = [dict(tooltip=labels[attr],
                    y=getattr(c.baruwa_totals, attr),
                    stroke='black',
                    color=pie_colors[attr])
                    for attr in ['clean', 'highspam', 'lowspam', 'virii',
                    'infected'] if getattr(c.baruwa_totals, attr)]
        c.chart_data = json.dumps(jsondata)
        return render('/status/index.html')

    def graph(self, nodeid=None):
        "Generate graphical system status"
        totals = DailyTotals(Session, c.user)
        if nodeid:
            server = self._get_server(nodeid)
            if not server:
                abort(404)
            baruwa_totals = totals.get(hostname=server.hostname)
        else:
            baruwa_totals = totals.get()

        if not baruwa_totals.total:
            abort(404)

        piedata = []
        labels = []
        for attr in ['clean', 'highspam', 'lowspam', 'virii', 'infected']:
            value = getattr(baruwa_totals, attr) or 0
            piedata.append(value)
            if baruwa_totals.total > 0:
                labels.append(("%.1f%% %s" % ((1.0 * value /
                        baruwa_totals.total) * 100, attr)))
            else:
                labels.append('0%')
        pie = PieChart(350, 264)
        pie.chart.labels = labels
        pie.chart.data = piedata
        pie.chart.width = 180
        pie.chart.height = 180
        pie.chart.x = 90
        pie.chart.y = 30
        pie.chart.slices.strokeWidth = 1
        pie.chart.slices.strokeColor = colors.black
        pie.chart.slices[0].fillColor = PIE_CHART_COLORS[5]
        pie.chart.slices[1].fillColor = PIE_CHART_COLORS[0]
        pie.chart.slices[2].fillColor = PIE_CHART_COLORS[1]
        pie.chart.slices[3].fillColor = PIE_CHART_COLORS[9]
        pie.chart.slices[4].fillColor = PIE_CHART_COLORS[3]
        self.imgfile = StringIO()
        renderPM.drawToFile(pie,
                            self.imgfile, 'PNG',
                            bg=colors.HexColor('#ffffff'))
        response.content_type = 'image/png'
        response.headers['Cache-Control'] = 'max-age=0'
        return self.imgfile.getvalue()

    def mailq(self, serverid=None, queue='inbound', page=1, direction='dsc',
        order_by='timestamp'):
        "Display mailqueue"
        server = None
        if not serverid is None:
            server = self._get_server(serverid)
            if not server:
                abort(404)

        c.queue = queue
        c.server = server
        c.direction = direction
        c.order_by = desc(order_by) if direction == 'dsc' else order_by
        if queue == 'inbound':
            qdirection = 1
        else:
            qdirection = 2

        num_items = session.get('mailq_num_items', 10)

        query = Session.query(MailQueueItem).filter(
                MailQueueItem.direction == qdirection).order_by(order_by)

        if server:
            query = query.filter(MailQueueItem.hostname == server.hostname)

        uquery = UserFilter(Session, c.user, query, model=MailQueueItem)
        query = uquery.filter()

        c.form = MailQueueProcessForm(request.POST, csrf_context=session)
        pages = paginate.Page(query, page=int(page), items_per_page=num_items)
        choices = [(str(item.id), item.id) for item in pages.items]
        session['queue_choices'] = choices
        session.save()

        c.page = paginate.Page(query, page=int(page),
                                items_per_page=num_items)
        return render('/status/mailq.html')

    def process_mailq(self):
        "Process mailq"
        sendto = url('mailq-status')
        choices = session.get('queue_choices', [])
        form = MailQueueProcessForm(request.POST, csrf_context=session)
        form.id.choices = choices

        if request.POST and form.validate() and choices:
            queueids = form.id.data
            if form.queue_action.data != '0':
                hosts = {}
                direction = None
                queueitems = Session.query(MailQueueItem)\
                            .filter(MailQueueItem.id.in_(queueids))\
                            .all()
                for item in queueitems:
                    if not item.hostname in hosts:
                        hosts[item.hostname] = []
                    if not direction:
                        direction = item.direction
                    hosts[item.hostname].append(item.messageid)
                for hostname in hosts:
                    process_queued_msgs.apply_async(args=[hosts[hostname],
                                                    form.queue_action.data,
                                                    direction],
                                                    queue=hostname)
                flash(_('The request has been queued for processing'))
            session['queue_choices'] = []
            session.save()

        referer = request.headers.get('Referer', None)
        if referer and '/mailq' in referer:
            sendto = referer
        redirect(sendto)

    def mailq_detail(self, queueid):
        "View a queued message's details"
        query = Session.query(MailQueueItem)
        uquery = UserFilter(Session, c.user, query, model=MailQueueItem)
        query = uquery.filter()

        try:
            mailqitem = query.filter(MailQueueItem.id == queueid).one()
        except NoResultFound:
            #abort(404)
            flash_alert(_('The requested queued message was not found.'))
            redirect(url('mailq-status'))

        c.mailqitem = mailqitem
        c.form = MailQueueProcessForm(request.POST, csrf_context=session)
        session['queue_choices'] = [(queueid, queueid),]
        session.save()
        return render('/status/detail.html')

    def mailq_preview(self, queueid, attachid=None, imgid=None, allowimgs=None):
        "preview a queued message"
        query = Session.query(MailQueueItem)
        uquery = UserFilter(Session, c.user, query, model=MailQueueItem)
        query = uquery.filter()

        try:
            mailqitem = query.filter(MailQueueItem.id == queueid).one()
        except NoResultFound:
            flash_alert(_('The requested queued message was not found.'))
            redirect(url('mailq-status'))

        try:
            task = preview_queued_msg.apply_async(args=[mailqitem.messageid,
                    mailqitem.direction, attachid, imgid],
                    queue=mailqitem.hostname)
            task.wait(30)
            if task.result:
                if imgid:
                    response.content_type = task.result['content_type']
                    if task.result and 'img' in task.result:
                        info = QUEUEDOWNLOAD_MSG % dict(m=mailqitem.messageid,
                                                        a=task.result['name'])
                        audit_log(c.user.username,
                                1, unicode(info), request.host,
                                request.remote_addr, now())
                        return base64.decodestring(task.result['img'])
                    abort(404)
                if attachid:
                    info = QUEUEDOWNLOAD_MSG % dict(m=mailqitem.messageid,
                                                    a=task.result['name'])
                    audit_log(c.user.username,
                            1, unicode(info), request.host,
                            request.remote_addr, now())
                    response.content_type = task.result['mimetype']
                    dispos = 'attachment; filename="%s"' % task.result['name']
                    response.headers['Content-Disposition'] = str(dispos)
                    content_len = len(task.result['attachment'])
                    response.headers['Content-Length'] = content_len
                    response.headers['Pragma'] = 'public'
                    response.headers['Cache-Control'] = 'max-age=0'
                    return base64.decodestring(task.result['attachment'])
                for part in task.result['parts']:
                    if part['type'] == 'html':
                        html = fromstring(part['content'])
                        for element, attribute, link, pos in iterlinks(html):
                            if not link.startswith('cid:'):
                                if not allowimgs and attribute == 'src':
                                    element.attrib['src'] = '%simgs/blocked.gif' % media_url()
                                    element.attrib['title'] = link
                                    flash(_('This message contains external images, which have been blocked. ') +
                                    literal(link_to(_('Display images'),
                                    url('queue-preview-with-imgs', queueid=queueid), class_='uline')))
                            else:
                                imgname = link.replace('cid:', '')
                                element.attrib['src'] = url('queue-preview-img',
                                                        imgid=imgname.replace('/', '__xoxo__'),
                                                        queueid=queueid)
                        part['content'] = tostring(html)
                c.message = task.result
                info = QUEUEPREVIEW_MSG % dict(m=mailqitem.messageid)
                audit_log(c.user.username,
                        1, unicode(info), request.host,
                        request.remote_addr, now())
            else:
                raise TimeoutError
        except (TimeoutError, QueueNotFound):
            flash_alert(_('The message could not be processed'))
            redirect(url('mailq-status'))
        c.queueid = queueid
        c.messageid = mailqitem.messageid
        return render('/status/preview.html')

    @ActionProtector(OnlySuperUsers())
    def server_status(self, serverid):
        "Display server status"
        server = self._get_server(serverid)
        if not server:
            abort(404)

        totals = DailyTotals(Session, c.user)
        mailq = MailQueue(Session, c.user)
        totals = totals.get(server.hostname)
        inbound = mailq.get(1, server.hostname)[0]
        outbound = mailq.get(2, server.hostname)[0]

        statusdict = dict(total=totals.total,
                        mta=0,
                        scanners=0,
                        av=0,
                        clean_mail=totals.clean,
                        high_spam=totals.highspam,
                        virii=totals.virii,
                        spam_mail=totals.lowspam,
                        inq=inbound,
                        outq=outbound,
                        otherinfected=totals.infected,
                        uptime='Unknown',
                        time=None,
                        load=(0, 0, 0),
                        mem=dict(free=0, used=0, total=0,
                                percent=0),
                        partitions=[],
                        net={},
                        cpu=0)
        try:
            task = systemstatus.apply_async(queue=server.hostname)
            task.wait(30)
            hoststatus = task.result
            statusdict.update(hoststatus)
            info = HOSTSTATUS_MSG % dict(n=server.hostname)
            audit_log(c.user.username,
                    1, unicode(info), request.host,
                    request.remote_addr, now())
        except (TimeoutError, QueueNotFound):
            pass

        c.server = server
        c.status = statusdict
        return render('/status/serverstatus.html')

    @ActionProtector(OnlySuperUsers())
    def server_bayes_status(self, serverid):
        "Display bayes stats"
        server = self._get_server(serverid)
        if not server:
            abort(404)

        try:
            task = bayesinfo.apply_async(queue=server.hostname)
            task.wait(30)
            result = task.result
            info = HOSTBAYES_MSG % dict(n=server.hostname)
            audit_log(c.user.username,
                    1, unicode(info), request.host,
                    request.remote_addr, now())
        except (TimeoutError, QueueNotFound, OSError):
            result = {}
        c.server = server
        c.data = result
        return render('/status/bayes.html')

    @ActionProtector(OnlySuperUsers())
    def server_salint_stat(self, serverid):
        "Display server salint output"
        server = self._get_server(serverid)
        if not server:
            abort(404)

        try:
            task = salint.apply_async(queue=server.hostname)
            task.wait(30)
            result = task.result
            info = HOSTSALINT_MSG % dict(n=server.hostname)
            audit_log(c.user.username,
                    1, unicode(info), request.host,
                    request.remote_addr, now())
        except (TimeoutError, QueueNotFound, OSError):
            result = []
        c.server = server
        c.data = result
        return render('/status/salint.html')

    @ActionProtector(OnlySuperUsers())
    def audit(self, page=1, format=None):
        "Audit log"
        total_found = 0
        search_time = 0
        num_items = session.get('auditlog_num_items', 50)
        q = request.GET.get('q', None)
        kwds = {}
        if q:
            conn = SphinxClient()
            conn.SetMatchMode(SPH_MATCH_EXTENDED2)
            if page == 1:
                conn.SetLimits(0, num_items, 500)
            else:
                page = int(page)
                offset = (page - 1) * num_items
                conn.SetLimits(offset, num_items, 500)
            q = clean_sphinx_q(q)
            results = conn.Query(q, 'auditlog, auditlog_rt')
            q = restore_sphinx_q(q)
            if results and results['matches']:
                ids = [hit['id'] for hit in results['matches']]
                query = Session.query(AuditLog)\
                        .filter(AuditLog.id.in_(ids))\
                        .order_by(desc('timestamp'))\
                        .all()
                total_found = results['total_found']
                search_time = results['time']
                logcount = total_found
                kwds['presliced_list'] = True
            else:
                query = []
                lcount = 0
                logcount = 0
        else:
            query = Session.query(AuditLog)\
                    .order_by(desc('timestamp'))
            lcount = Session.query(AuditLog)\
                    .order_by(desc('timestamp'))
        if not 'logcount' in locals():
            logcount = lcount.count()
        items = paginate.Page(query, page=int(page),
                            items_per_page=num_items,
                            item_count=logcount, **kwds)
        if format == 'json':
            response.headers['Content-Type'] = 'application/json'
            jdict = convert_settings_to_json(items)
            if q:
                encoded = json.loads(jdict)
                encoded['q'] = q
                jdict = json.dumps(encoded)
            return jdict

        c.page = items
        c.q = q
        c.total_found = total_found
        c.search_time = search_time
        return render('/status/audit.html')

    @ActionProtector(OnlySuperUsers())
    def audit_export(self, isquery=None, format=None):
        "Export audit logs"
        query = request.GET.get('q', None)
        if isquery and query is None:
            flash_alert(_('No query specified for audit log export'))
            redirect(url('status-audit-logs'))

        task = export_auditlog.apply_async(args=[format, query])
        if not 'taskids' in session:
            session['taskids'] = []
        session['taskids'].append(task.task_id)
        session['exportauditlog-counter'] = 1
        session.save()
        redirect(url('status-auditlog-export-status', taskid=task.task_id))

    @ActionProtector(OnlySuperUsers())
    def audit_export_status(self, taskid):
        "Audit log export status"
        result = AsyncResult(taskid)
        if result is None or taskid not in session['taskids']:
            flash(_('The task status requested has expired or does not exist'))
            redirect(url('status-audit-logs'))

        if result.ready():
            finished = True
            flash.pop_messages()
            if isinstance(result.result, Exception):
                if c.user.is_superadmin:
                    flash_alert(_('Error occured in processing %s') %
                                result.result)
                else:
                    flash_alert(_('Backend error occured during processing.'))
                redirect(url('status-audit-logs'))
        else:
            session['exportauditlog-counter'] += 1
            session.save()
            if (session['exportauditlog-counter'] >= 20 and
                result.state in ['PENDING', 'RETRY', 'FAILURE']):
                result.revoke()
                del session['exportauditlog-counter']
                session.save()
                flash_alert(_('The audit log export failed, try again later'))
                redirect(url('status-audit-logs'))
            finished = False

        c.finished = finished
        c.results = result.result
        c.success = result.successful()
        d = request.GET.get('d', None)
        if finished and (d and d == 'y'):
            audit_log(c.user.username,
                    5, unicode(AUDITLOGEXPORT_MSG), request.host,
                    request.remote_addr, now())
            response.content_type = result.result['content_type']
            response.headers['Cache-Control'] = 'max-age=0'
            respdata = result.result['f']
            disposition = 'attachment; filename=%s' % result.result['filename']
            response.headers['Content-Disposition'] = str(disposition)
            response.headers['Content-Length'] = len(respdata)
            return respdata
        return render('/status/auditexportstatus.html')

    def setnum(self, format=None):
        "Set number of items to return for auditlog/mailq"
        app = request.GET.get('ac', 'mailq')
        num = check_num_param(request)

        if num and num in [10, 20, 50, 100]:
            if app == 'auditlog':
                session['auditlog_num_items'] = num
            else:
                session['mailq_num_items'] = num
            session.save()
        nextpage = request.headers.get('Referer', '/')
        if '://' in nextpage:
            from_url = urlparse(nextpage)
            nextpage = from_url[2]
        redirect(nextpage)
