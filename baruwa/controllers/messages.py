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
"Messages controller"

import json
import base64
import socket
import logging
import struct
import urllib2

import arrow

from urlparse import urlparse

from celery import group
from pylons import config
from sqlalchemy import desc
from webhelpers import paginate
from celery.result import GroupResult
from pylons.i18n.translation import _
from paste.deploy.converters import asbool
from sqlalchemy.exc import OperationalError
from celery.backends.cache import CacheBackend
from repoze.what.predicates import not_anonymous
from repoze.what.plugins.pylonshq import ActionProtector
from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sphinxapi import SphinxClient, SPH_MATCH_EXTENDED2
from celery.exceptions import TimeoutError, QueueNotFound

from baruwa.model.meta import Session
from baruwa.lib.audit import audit_log
from baruwa.lib.net import system_hostname
from baruwa.lib.base import BaseController
from baruwa.lib.pagination import paginator
from baruwa.lib.dates import convert_date
from baruwa.lib.caching_query import FromCache
from baruwa.lib.helpers import flash, flash_alert
from baruwa.lib.templates.html import image_fixups
from baruwa.tasks import preview_msg, update_autorelease
from baruwa.lib.misc import jsonify_msg_list, convert_to_json
from baruwa.lib.misc import check_num_param, extract_sphinx_opts
from baruwa.lib.query import DynaQuery, UserFilter, filter_sphinx
from baruwa.forms.messages import ReleaseMsgForm, BulkReleaseForm
from baruwa.tasks import release_message, process_quarantined_msg
from baruwa.lib.query import clean_sphinx_q, restore_sphinx_q, MsgCount
from baruwa.model.messages import Message, Archive, MessageStatus
from baruwa.lib.audit.msgs.messages import MSGDOWNLOAD_MSG, MSGPREVIEW_MSG
from baruwa.lib.api import get_messages, get_messagez, get_msg_count, \
    get_archived, get_releasereq

log = logging.getLogger(__name__)

# celery backend
RBACKEND = CacheBackend()


def ajax_code(code, msg):
    "Return AJAX coded message"
    # response.headers['Content-Type'] = 'application/json'
    response.status = code
    response.text = msg
    return response


def process_release_results(context, msg, result, dbsession, func):
    "Process the results of a release task"
    html = []
    context.id = msg.messageid
    errors = dict(result['errors'])
    templates = dict(
                    release='/messages/includes/released.html',
                    learn='/messages/includes/salearn.html',
                    delete='/messages/includes/delete.html')

    def rendertemplate(error_msg, action):
        "Render template"
        context.msg = error_msg
        context.success = error_msg == ''
        html.append(func(templates[action]))

    if context.form.release.data:
        # release
        if context.form.usealt.data:
            to_addr = context.form.altrecipients.data
        else:
            to_addr = msg.to_address
        to_addr = to_addr.split(',')
        error_msg = ''
        if not result['release']:
            error_msg = errors['release']
        context.addrs = to_addr
        rendertemplate(error_msg, 'release')
    if context.form.learn.data:
        # salean
        error_msg = ''
        if not result['learn']:
            error_msg = errors['learn']
        rendertemplate(error_msg, 'learn')
    if context.form.delete.data:
        # delete
        error_msg = ''
        if not result['delete']:
            error_msg = errors['delete']
        else:
            msg.isquarantined = 0
            dbsession.add(msg)
            dbsession.commit()
        rendertemplate(error_msg, 'delete')
    return '<br />'.join(html)


# @ControllerProtector(not_anonymous())
class MessagesController(BaseController):
    "Messages controller"
    def __before__(self):
        "set context"
        BaseController.__before__(self)
        if self.identity:
            c.user = self.identity['user']
        else:
            c.user = None
        c.selectedtab = 'messages'

    def _get_msg(self, msgid, archived):
        "Return message object"
        if archived:
            message = self._get_archive(msgid)
        else:
            message = self._get_message(msgid)
        return message

    def _get_archive(self, messageid):
        "utility to return message"
        try:
            cachekey = u"archiveid-%s" % messageid
            qry = Session.query(Archive).filter(Archive.id == messageid)
            if c.user.account_type != 1:
                uquery = UserFilter(Session, c.user, qry)
                qry = uquery.filter()
            qry = qry.options(FromCache('sql_cache_long', cachekey))
            if self.invalidate:
                qry.invalidate()
            message = qry.one()
        except (NoResultFound, MultipleResultsFound):
            message = None
        return message

    def _get_message(self, messageid):
        "utility to return message"
        try:
            cachekey = u"msgid-%s" % messageid
            qry = Session.query(Message).filter(Message.id == messageid)
            if not c.user.is_superadmin:
                uquery = UserFilter(Session, c.user, qry)
                qry = uquery.filter()
            qry = qry.options(FromCache('sql_cache_long', cachekey))
            if self.invalidate:
                qry.invalidate()
            message = qry.one()
        except (NoResultFound, MultipleResultsFound):
            message = None
        return message

    # pylint: disable-msg=W0622
    @ActionProtector(not_anonymous())
    def index(self, format=None):
        "return recent messages"
        num_items = session.get('msgs_num_items', 50)
        query = get_messagez().order_by(desc('timestamp'))
        if ('X-Last-Timestamp' in request.headers and
            request.headers['X-Last-Timestamp']):
            tstmp = request.headers.get('X-Last-Timestamp')
            query = query.filter(Message.timestamp > tstmp)
        uquery = UserFilter(Session, c.user, query)
        query = uquery.filter()
        items = query[:num_items]
        if format == 'json':
            response.headers['Content-Type'] = 'application/json'
            msgs = [item.json for item in items]
            tmp = dict(
                        totals=c.baruwa_totals,
                        inbound=c.baruwa_inbound,
                        outbound=c.baruwa_outbound,
                        items=msgs,
                        num_items=num_items
                    )
            if c.user.is_admin:
                tmp['status'] = c.baruwa_status
            return json.dumps(tmp)

        c.messages = items
        c.num_items = num_items
        return self.render('/messages/index.html')

    @ActionProtector(not_anonymous())
    def detail(self, msgid, archive=None, format=None):
        "return message detail"
        message = self._get_msg(msgid, archive)
        if not message:
            abort(404)

        msgstatus = Session.query(MessageStatus)\
                    .filter(MessageStatus.messageid == message.messageid)\
                    .all()
        show_trail = request.GET.get('t', None)

        c.form = ReleaseMsgForm(request.POST, csrf_context=session)
        if request.method == 'POST' and c.form.validate():
            localtmz = config.get('baruwa.timezone', 'Africa/Johannesburg')
            job = dict(release=c.form.release.data,
                        learn=c.form.learn.data,
                        salearn_as=c.form.learnas.data,
                        todelete=c.form.delete.data,
                        use_alt=c.form.usealt.data,
                        altrecipients=c.form.altrecipients.data,
                        message_id=message.messageid,
                        from_address=message.from_address,
                        date=convert_date(message.timestamp, localtmz)
                        .strftime('%Y%m%d'),
                        msgfiles=message.msgfiles,
                        to_address=message.to_address,
                        hostname=message.hostname,
                        mid=message.id,
                        issingle=True)
            try:
                task = process_quarantined_msg.apply_async(
                        args=[job],
                        routing_key=system_hostname() if
                        asbool(config.get('ms.quarantine.shared', 'false'))
                        else message.hostname)
                task.wait(30)
                if task.status == 'SUCCESS':
                    # process response
                    html = process_release_results(
                            c, message, task.result,
                            Session, self.render)
                    self.invalidate = 1
                    message = self._get_msg(msgid, archive)
                    flash(html)
                else:
                    html = _('Processing the request failed')
                    flash_alert(html)
                    log.info(html)
            except (TimeoutError, QueueNotFound):
                html = _('Processing the request failed')
                flash_alert(html)
                log.info(html)
            if format == 'json':
                flash.pop_messages()
                response.headers['Content-Type'] = 'application/json'
                return json.dumps(dict(result=html))
        elif request.method == 'POST' and not c.form.validate():
            flash_alert(_(u', '.join([unicode(c.form.errors[err][0])
                                for err in c.form.errors])))
            if format == 'json':
                html = flash.pop_messages()
                response.headers['Content-Type'] = 'application/json'
                return json.dumps(dict(result=unicode(html[0])))

        if format == 'json':
            response.headers['Content-Type'] = 'application/json'
            return json.dumps(message.tojson)
        c.msg = message
        c.archived = archive
        c.show_trail = show_trail
        c.msgstatus = msgstatus
        return self.render('/messages/detail.html')

    @ActionProtector(not_anonymous())
    def relayed_via(self, msgid, archive=None):
        "return relayed via hosts used by ajax calls"
        message = self._get_msg(msgid, archive)
        if not message:
            abort(404)

        c.msg = message
        return self.render('/messages/includes/relayedvia.html')

    # pylint: disable-msg=R0914
    @ActionProtector(not_anonymous())
    def listing(self, page=1, direction='dsc', order_by='timestamp',
                format=None):
        "message listing"
        filters = session.get('filter_by', None)
        num_items = session.get('msgs_num_items', 50)
        if direction == 'dsc':
            sort = desc(order_by)
        else:
            sort = order_by
        messages = get_messages().order_by(sort)
        query = UserFilter(Session, c.user, messages)
        messages = query.filter()
        if filters:
            msgcount = get_msg_count()
            countquery = UserFilter(Session, c.user, msgcount)
            msgcount = countquery.filter()
            dynq = DynaQuery(Message, messages, filters)
            dynmsgq = DynaQuery(Message, msgcount, filters)
            messages = dynq.generate()
            msgcount = dynmsgq.generate()
            msgcount = msgcount.count()
        else:
            countquery = MsgCount(Session, c.user)
            msgcount = countquery.count()
        c.list_all = True
        c.order_by = order_by
        c.direction = direction
        pages = paginate.Page(messages, page=int(page),
                                items_per_page=num_items,
                                item_count=msgcount)
        if format == 'json':
            response.headers['Content-Type'] = 'application/json'
            data = convert_to_json(pages,
                                    direction=direction,
                                    order_by=order_by,
                                    section=None)
            return data
        c.page = pages
        return self.render('/messages/listing.html')

    # pylint: disable-msg=R0912,R0913,R0914,R0915
    @ActionProtector(not_anonymous())
    def quarantine(self, page=1, direction='dsc', order_by='timestamp',
                    section=None, format=None):
        "quarantined messages"
        filters = session.get('filter_by', None)
        num_items = session.get('msgs_num_items', 50)
        if direction == 'dsc':
            sort = desc(order_by)
        else:
            sort = order_by
        messages = get_messages().filter(
                    Message.isquarantined == 1).order_by(sort)
        msgcount = get_msg_count().filter(
                    Message.isquarantined == 1)
        query = UserFilter(Session, c.user, messages)
        countquery = UserFilter(Session, c.user, msgcount)
        messages = query.filter()
        msgcount = countquery.filter()
        if section:
            if section == 'spam':
                messages = messages.filter(Message.spam == 1)
                msgcount = messages.filter(Message.spam == 1)
            else:
                messages = messages.filter(Message.spam == 0)
                msgcount = messages.filter(Message.spam == 0)
        if filters:
            dynq = DynaQuery(Message, messages, filters)
            dynmsgq = DynaQuery(Message, msgcount, filters)
            messages = dynq.generate()
            msgcount = dynmsgq.generate()
        c.order_by = order_by
        c.direction = direction
        c.section = section
        msgcount = msgcount.count()
        c.form = BulkReleaseForm(request.POST, csrf_context=session)
        if request.method == 'POST':
            choices = session.get('bulk_items', [])
        else:
            pages = paginate.Page(messages, page=int(page),
                                items_per_page=num_items,
                                item_count=msgcount)
            choices = [(str(message.id), message.id)
                        for message in pages.items]
            session['bulk_items'] = choices
            session.save()
        c.form.message_id.choices = choices
        if request.method == 'POST' and c.form.validate() and choices:
            msgs = Session.query(Message.id,
                    Message.messageid,
                    Message.from_address,
                    Message.timestamp, Message.to_address,
                    Message.hostname, Message.msgfiles)\
                    .filter(Message.id.in_(c.form.message_id.data))
            query = UserFilter(Session, c.user, msgs)
            msgs = query.filter()
            localtmz = config.get('baruwa.timezone', 'Africa/Johannesburg')
            formvals = (dict(release=c.form.release.data,
                            learn=c.form.learn.data,
                            salearn_as=c.form.learnas.data,
                            todelete=c.form.delete.data,
                            use_alt=c.form.usealt.data,
                            altrecipients=c.form.altrecipients.data,
                            message_id=msg.messageid,
                            from_address=msg.from_address,
                            date=convert_date(msg.timestamp, localtmz)
                            .strftime('%Y%m%d'),
                            msgfiles=msg.msgfiles,
                            to_address=msg.to_address,
                            hostname=msg.hostname,
                            mid=msg.id,
                            num=num_items)
                        for msg in msgs)

            if formvals:
                try:
                    subtasks = [process_quarantined_msg.subtask(args=[formval],
                                options=dict(routing_key=system_hostname()
                                if asbool(config.get(
                                                    'ms.quarantine.shared',
                                                    'false'))
                                else formval['hostname']))
                                for formval in formvals]
                    task = group(subtasks).apply_async()
                    task.save(backend=RBACKEND)
                    session['bulk_items'] = []
                    if 'taskids' not in session:
                        session['taskids'] = []
                    session['taskids'].append(task.id)
                    session['bulkprocess-count'] = 1
                    session.save()
                    redirect(url('messages-bulk-process',
                            taskid=task.id))
                except (QueueNotFound, OperationalError, IndexError):
                    flash_alert(_('The messages could not processed'
                                ', try again later'))
        elif request.method == 'POST' and not c.form.validate():
            try:
                flash_alert(_(u', '.join([unicode(c.form.errors[err][0])
                                            for err in c.form.errors])))
            except IndexError:
                flash_alert(_('The messages could not processed'
                            ', an Unknown error occured.'))
        pages = paginate.Page(messages, page=int(page),
                                items_per_page=num_items,
                                item_count=msgcount)
        if format == 'json':
            response.headers['Content-Type'] = 'application/json'
            data = convert_to_json(pages,
                                    direction=direction,
                                    order_by=order_by,
                                    section=section)
            return data
        c.page = pages
        return self.render('/messages/quarantine.html')

    @ActionProtector(not_anonymous())
    def archive(self, page=1, direction='dsc',
                order_by='timestamp', format=None):
        "messages archive"
        filters = session.get('filter_by', None)
        num_items = session.get('msgs_num_items', 50)
        if direction == 'dsc':
            sort = desc(order_by)
        else:
            sort = order_by
        messages = get_archived().order_by(sort)
        msgcount = get_msg_count(True)
        query = UserFilter(Session, c.user, messages, True)
        countquery = UserFilter(Session, c.user, msgcount, True)
        messages = query.filter()
        msgcount = countquery.filter()
        if filters:
            dynq = DynaQuery(Archive, messages, filters)
            dynmsgq = DynaQuery(Archive, msgcount, filters)
            messages = dynq.generate()
            msgcount = dynmsgq.generate()
        c.order_by = order_by
        c.direction = direction
        msgcount = msgcount.count()
        pages = paginate.Page(messages, page=int(page),
                                items_per_page=num_items,
                                item_count=msgcount)
        if format == 'json':
            response.headers['Content-Type'] = 'application/json'
            data = convert_to_json(pages,
                                    direction=direction,
                                    order_by=order_by,
                                    section=None)
            return data
        c.page = pages
        return self.render('/messages/archive.html')

    @ActionProtector(not_anonymous())
    def preview(self, msgid, archive=None, attachment=None, img=None,
                allowimgs=None, richformat=None):
        """Preview a message stored in the quarantine

        :param msgid: the database message id
        :param archive: optional. message archived status
        :param attachment: optional. request is for an attachmeny
        :param img: optional request is for an image
        :param allowimgs: optional allow display of remote images
        :param richformat: show html format

        """
        if archive:
            message = self._get_archive(msgid)
        else:
            message = self._get_message(msgid)
        if not message:
            abort(404)

        try:
            if message.isdangerous and c.user.is_peleb:
                raise ValueError
            localtmz = config.get('baruwa.timezone', 'Africa/Johannesburg')
            cdte = convert_date(message.timestamp, localtmz).strftime('%Y%m%d')
            args = [message.messageid,
                    cdte,
                    message.msgfiles,
                    attachment,
                    img,
                    allowimgs]
            task = preview_msg.apply_async(args=args,
                        routing_key=system_hostname() if
                        asbool(config.get('ms.quarantine.shared', 'false'))
                        else message.hostname.strip())
            task.wait(30)
            if task.result:
                if img:
                    if message.isdangerous and c.user.is_peleb:
                        abort(404)
                    response.content_type = task.result['content_type']
                    if task.result and 'img' in task.result:
                        info = MSGDOWNLOAD_MSG % dict(m=message.id,
                                                a=task.result['name'])
                        audit_log(c.user.username,
                                1, unicode(info), request.host,
                                request.remote_addr, arrow.utcnow().datetime)
                        return base64.decodestring(task.result['img'])
                    abort(404)
                if attachment:
                    info = MSGDOWNLOAD_MSG % dict(m=message.id,
                                            a=task.result['name'])
                    audit_log(c.user.username,
                            1, unicode(info), request.host,
                            request.remote_addr, arrow.utcnow().datetime)
                    response.content_type = task.result['mimetype']
                    content_disposition = 'attachment; filename="%s"' % \
                        task.result['name'].encode('ascii', 'replace')
                    response.headers['Content-Disposition'] = \
                                    str(content_disposition)
                    response.headers['Content-Length'] = \
                                    len(task.result['attachment'])
                    response.headers['Pragma'] = 'public'
                    response.headers['Cache-Control'] = 'max-age=0'
                    return base64.decodestring(task.result['attachment'])
                for part in task.result['parts']:
                    if part['type'] == 'text/html':
                        local_rf = (not task.result['is_multipart']
                                    or richformat)
                        part['content'] = image_fixups(
                                            part['content'],
                                            msgid, archive,
                                            local_rf, allowimgs)
                c.message = task.result
                info = MSGPREVIEW_MSG % dict(m=message.id)
                audit_log(c.user.username,
                        1, unicode(info), request.host,
                        request.remote_addr, arrow.utcnow().datetime)
            else:
                c.message = {}
        except (socket.error, TimeoutError, QueueNotFound):
            lmsg = _('The message could not be previewed, try again later')
            flash_alert(lmsg)
            log.info(lmsg)
            whereto = url('message-archive', msgid=msgid) if archive \
                        else url('message-detail', msgid=msgid)
            redirect(whereto)
        except ValueError:
            lmsg = _('The message/attachments are either prohibited or'
                    ' dangerous. Contact your system admin for assistance')
            flash_alert(lmsg)
            log.info(lmsg)
            whereto = url('message-archive', msgid=msgid) if archive \
                        else url('message-detail', msgid=msgid)
            redirect(whereto)
        c.messageid = message.messageid
        c.msgid = message.id
        c.archived = archive
        c.richformat = richformat
        c.isdangerous = message.isdangerous
        # print c.message
        return self.render('/messages/preview.html')

    def autorelease(self, uuid):
        "release a message without logging in"
        releasereq = get_releasereq(uuid)
        if not releasereq:
            abort(404)

        released = False
        msgid = releasereq.messageid
        to_address = _('Unknown')
        errormsg = _('The message has already been released,'
                    ' you can only use the release link once')
        if releasereq.released is False:
            try:
                msg = Session.query(Message)\
                    .filter(Message.id == releasereq.messageid)\
                    .one()
            except (NoResultFound, MultipleResultsFound):
                abort(404)

            msgid = msg.messageid
            to_address = msg.to_address
            try:
                if msg.isdangerous and c.user and c.user.is_peleb:
                    raise ValueError
                localtmz = config.get('baruwa.timezone', 'Africa/Johannesburg')
                cdte = convert_date(msg.timestamp, localtmz).strftime('%Y%m%d')
                task = release_message.apply_async(
                        args=[msg.messageid,
                            cdte,
                            msg.from_address,
                            msg.to_address.split(','),
                            msg.msgfiles],
                        routing_key=system_hostname() if
                        asbool(config.get('ms.quarantine.shared', 'false'))
                        else msg.hostname.strip())
                task.wait(30)
                if task.status == 'SUCCESS':
                    result = task.result
                    if result['success']:
                        update_autorelease.apply_async(args=[uuid])
                    errormsg = result['error']
                    released = result['success']
            except (ValueError, socket.error, TimeoutError, QueueNotFound):
                released = False
                errormsg = _('Processing of message failed')
                log.info(errormsg)
                result = dict(success=False, error=errormsg)

        c.messageid = msgid
        c.errormsg = errormsg
        c.released = released
        c.releaseaddress = to_address
        return self.render('/messages/autorelease.html')

    @ActionProtector(not_anonymous())
    def process(self, taskid, format=None):
        "process a taskset"
        result = GroupResult.restore(taskid, backend=RBACKEND)
        if (result is None or
            'taskids' not in session or
            taskid not in session['taskids']):
            if format == 'json':
                return ajax_code(404,
                        _('The task status requested '
                        'has expired or does not exist'))
            flash(_('The task status requested has expired or does not exist'))
            redirect(url(controller='messages', action='quarantine'))
        percent = "0.0"
        status = 'PROGRESS'
        results = []
        if result.ready():
            finished = True
            results = result.join_native()
        else:
            session['bulkprocess-count'] += 1
            if (session['bulkprocess-count'] >= 10 and
                result.completed_count() == 0):
                result.revoke()
                del session['bulkprocess-count']
                session.save()
                if format == 'json':
                    return ajax_code(503,
                        _('An error occured in processing, try again later'))
                flash_alert(
                        _('An error occured in processing, try again later'))
                redirect(url(controller='messages', action='quarantine'))
            finished = False
            percent = "%.1f" % ((1.0 * int(result.completed_count()) /
                                len(result)) * 100)

        if format == 'json':
            response.headers['Content-Type'] = 'application/json'
            data = dict(finished=finished,
                        results=results,
                        status=status,
                        completed=percent)
            return json.dumps(data)

        c.finished = finished
        c.results = results
        c.status = status
        c.completed = percent
        return self.render('/messages/taskstatus.html')

    @ActionProtector(not_anonymous())
    def search(self, format=None):
        "Search for messages"
        qry = request.GET.get('q', None)
        if qry is None:
            redirect(url(controller='messages', action='listing'))
        index = 'messages, messagesdelta, messages_rt'
        action = request.GET.get('a', 'listing')
        if action not in ['listing', 'quarantine', 'archive']:
            action = 'listing'
        if action == 'archive':
            index = 'archive archivedelta'
        try:
            page = int(request.GET.get('page', 1))
        except ValueError:
            page = 1
        num_items = session.get('msgs_search_num_results', 50)
        conn = SphinxClient()
        sphinxopts = extract_sphinx_opts(config['sphinx.url'])
        conn.SetServer(sphinxopts.get('host', '127.0.0.1'))
        conn.SetMatchMode(SPH_MATCH_EXTENDED2)
        if action == 'quarantine':
            conn.SetFilter('isquarantined', [True, ])
        if page == 1:
            conn.SetLimits(0, num_items, 500)
        else:
            offset = (page - 1) * num_items
            conn.SetLimits(offset, num_items, 500)
        if not c.user.is_superadmin:
            filter_sphinx(Session, c.user, conn)
        else:
            conn.SetSelect('timestamp')
        qry = clean_sphinx_q(qry)
        try:
            results = conn.Query(qry, index)
        except (socket.timeout, struct.error):
            redirect(request.path_qs)
        qry = restore_sphinx_q(qry)
        if results and results['matches']:
            ids = [hit['id'] for hit in results['matches']]
            filters = session.get('filter_by', None)
            if action == 'archive':
                messages = get_archived().filter(
                            Archive.id.in_(ids))
                query = UserFilter(Session, c.user, messages, True)
                messages = query.filter()
                if filters:
                    dynq = DynaQuery(Message, messages, filters)
                    messages = dynq.generate()
            else:
                messages = get_messages().filter(
                            Message.id.in_(ids))
                query = UserFilter(Session, c.user, messages)
                messages = query.filter()
                if filters:
                    dynq = DynaQuery(Message, messages, filters)
                    messages = dynq.generate()
            total_found = results['total']
            search_time = results['time']
            messages = messages.order_by(desc('timestamp'))
        else:
            messages = []
            results = dict(matches=[], total=0)
            total_found = 0
            search_time = 0

        pages = paginator(dict(page=page, results_per_page=num_items,
                                total=results['total'],
                                items=len(results['matches']),
                                q=qry))

        if format == 'json':
            response.headers['Content-Type'] = 'application/json'
            data = dict(action=action,
                        total_found=total_found,
                        search_time=search_time,
                        paginator=pages,
                        items=[jsonify_msg_list(msg) for msg in messages])
            return json.dumps(data)

        c.messages = messages
        c.action = action
        c.total_found = total_found
        c.search_time = search_time
        c.page = pages
        return self.render('/messages/searchresults.html')

    # pylint: disable-msg=R0201,W0613
    @ActionProtector(not_anonymous())
    def setnum(self, format=None):
        "Set num of items to return"
        num = check_num_param(request)

        if num and num in [10, 20, 50, 100]:
            session['msgs_search_num_results'] = num
            session['msgs_num_items'] = num
            session.save()
        nextpage = request.headers.get('Referer', '/')
        if '://' in nextpage:
            from_url = urlparse(nextpage)
            nextpage = from_url[2]

        params = []
        for param in request.params:
            value = request.params[param]
            if value:
                params.append('%s=%s' % (urllib2.quote(param),
                                        urllib2.quote(value)))
        if params:
            nextpage = "%s?%s" % (nextpage, '&amp;'.join(params))
        redirect(nextpage)
