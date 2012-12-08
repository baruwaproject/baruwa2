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
import socket
import urllib2

from urlparse import urlparse

from pylons import config
from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from pylons.i18n.translation import _
from webhelpers import paginate
from sqlalchemy import desc
from celery.task.sets import TaskSet
from celery.result import TaskSetResult
from webhelpers.html import literal
from webhelpers.html.tags import link_to
from lxml.html import fromstring, tostring, iterlinks
from repoze.what.predicates import not_anonymous
from repoze.what.plugins.pylonshq import ActionProtector
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sphinxapi import SphinxClient, SPH_MATCH_EXTENDED2 #, SPH_SORT_EXTENDED
from celery.backends.database import DatabaseBackend
from celery.exceptions import TimeoutError, QueueNotFound

from baruwa.lib.dates import now, convert_date
from baruwa.lib.base import BaseController, render
from baruwa.lib.misc import check_num_param
from baruwa.lib.misc import jsonify_msg_list, convert_to_json
from baruwa.lib.helpers import flash, flash_alert
from baruwa.lib.query import DynaQuery, UserFilter, filter_sphinx
from baruwa.lib.query import clean_sphinx_q, restore_sphinx_q, MsgCount
from baruwa.lib.pagination import paginator
from baruwa.lib.caching_query import FromCache
from baruwa.lib.templates.helpers import media_url
from baruwa.lib.audit import audit_log #, msg_audit_log
from baruwa.tasks import preview_msg, update_autorelease
from baruwa.tasks import release_message, process_quarantined_msg
from baruwa.model.meta import Session
from baruwa.model.messages import Message, Archive, Release, MessageStatus
from baruwa.forms.messages import ReleaseMsgForm, BulkReleaseForm
from baruwa.lib.audit.msgs.messages import MSGDOWNLOAD_MSG, MSGPREVIEW_MSG

# celery backend
dbbackend = DatabaseBackend(dburi=Session.bind.url,
                            engine_options={'echo': True})


def ajax_code(code, msg):
    "Return AJAX coded message"
    #response.headers['Content-Type'] = 'application/json'
    response.status = code
    response.body = msg
    return response


def process_release_results(context, msg, result, session):
    "Process the results of a release task"
    html = []
    context.id = msg.messageid
    errors = dict(result['errors'])
    templates = dict(
                    release='/messages/includes/released.html',
                    learn='/messages/includes/salearn.html',
                    delete='/messages/includes/delete.html'
                    )
    def rendertemplate(error_msg, action):
        "Render template"
        context.msg = error_msg
        context.success =  error_msg == ''
        html.append(render(templates[action]))

    if context.form.release.data:
        #release
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
        #salean
        error_msg = ''
        if not result['learn']:
            ['learn']
            error_msg = errors['learn']
        rendertemplate(error_msg, 'learn')
    if context.form.delete.data:
        #delete
        error_msg = ''
        if not result['delete']:
            error_msg = errors['delete']
        else:
            msg.isquarantined = True
            session.add(msg)
            session.commit()
        rendertemplate(error_msg, 'delete')
    return '<br />'.join(html)


# @ControllerProtector(not_anonymous())
class MessagesController(BaseController):
    def __before__(self):
        "set context"
        BaseController.__before__(self)
        if self.identity:
            c.user = self.identity['user']
        else:
            c.user = None
        c.selectedtab = 'messages'

    def _get_msg(self, id, archived):
        "Return message object"
        if archived:
            message = self._get_archive(id)
        else:
            message = self._get_message(id)
        return message

    def _get_archive(self, messageid):
        "utility to return message"
        try:
            cachekey = u"archiveid-%s" % messageid
            q = Session.query(Archive).filter(Archive.id == messageid)
            if c.user.account_type != 1:
                uquery = UserFilter(Session, c.user, q)
                q = uquery.filter()
            q = q.options(FromCache('sql_cache_long', cachekey))
            if self.invalidate:
                q.invalidate()
            message = q.one()
        except (NoResultFound, MultipleResultsFound):
            message = None
        return message

    def _get_message(self, messageid):
        "utility to return message"
        try:
            cachekey = u"msgid-%s" % messageid
            q = Session.query(Message).filter(Message.id == messageid)
            if not c.user.is_superadmin:
                uquery = UserFilter(Session, c.user, q)
                q = uquery.filter()
            q = q.options(FromCache('sql_cache_long', cachekey))
            if self.invalidate:
                q.invalidate()
            message = q.one()
        except (NoResultFound, MultipleResultsFound):
            message = None
        return message

    def _get_messages(self):
        "Return messages query object"
        return Session.query(Message.id, Message.from_address,
                        Message.to_address, Message.subject,
                        Message.size, Message.sascore,
                        Message.spam, Message.highspam,
                        Message.whitelisted, Message.blacklisted,
                        Message.scaned, Message.nameinfected,
                        Message.otherinfected, Message.virusinfected,
                        Message.timestamp, Message.isquarantined,
                        Message.spam)

    def _get_messagez(self):
        "Return message query object"
        return Session.query(Message)

    def _get_msg_count(self, archived=None):
        "return message query for count"
        if archived:
            return Session.query(Archive.id)
        else:
            return Session.query(Message.id)

    def _get_archived(self):
        "Return archived messages query object"
        return Session.query(Archive.id, Archive.from_address,
                        Archive.to_address, Archive.subject,
                        Archive.size, Archive.sascore,
                        Archive.spam, Archive.highspam,
                        Archive.whitelisted, Archive.blacklisted,
                        Archive.scaned, Archive.nameinfected,
                        Archive.otherinfected, Archive.virusinfected,
                        Archive.timestamp, Archive.isquarantined,
                        Archive.spam)

    def _get_releasereq(self, uuid):
        "return a release request object"
        try:
            msg = Session.query(Release).filter(Release.uuid==uuid)\
                        .one()
        except NoResultFound:
            msg = None
        # except MultipleResultsFound:
        #     msg = releasereq.all()[0]
        return msg

    @ActionProtector(not_anonymous())
    def index(self, format=None):
        "return recent messages"
        num_items = session.get('msgs_num_items', 50)
        query = self._get_messagez().order_by(desc('timestamp'))
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
        return render('/messages/index.html')

    @ActionProtector(not_anonymous())
    def detail(self, id, archive=None, format=None):
        "return message detail"
        message = self._get_msg(id, archive)
        if not message:
            abort(404)

        msgstatus = Session.query(MessageStatus)\
                    .filter(MessageStatus.messageid==message.messageid)\
                    .all()
        show_trail = request.GET.get('t', None)

        c.form = ReleaseMsgForm(request.POST, csrf_context=session)
        if request.POST and c.form.validate():
            localtmz = config.get('baruwa.timezone', 'Africa/Johannesburg')
            job = dict(release=c.form.release.data,
                        learn=c.form.learn.data, 
                        salearn_as=c.form.learnas.data,
                        todelete=c.form.delete.data,
                        use_alt=c.form.usealt.data,
                        altrecipients=c.form.altrecipients.data,
                        message_id=message.messageid,
                        from_address=message.from_address,
                        date=convert_date(message.timestamp, localtmz).strftime('%Y%m%d'),
                        to_address=message.to_address,
                        hostname=message.hostname,
                        mid=message.id)
            try:
                task = process_quarantined_msg.apply_async(
                        args=[job], queue=message.hostname)
                task.wait(30)
                if task.status == 'SUCCESS':
                    # process response
                    html = process_release_results(
                            c, message, task.result,
                            Session)
                    self.invalidate = 1
                    message = self._get_msg(id, archive)
                    flash(html)
                else:
                    html = _('Processing the request failed')
                    flash_alert(html)
            except (TimeoutError, QueueNotFound):
                html = _('Processing the request failed')
                flash_alert(html)
            if format == 'json':
                flash.pop_messages()
                response.headers['Content-Type'] = 'application/json'
                return json.dumps(dict(result=html))
        elif request.POST and not c.form.validate():
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
        return render('/messages/detail.html')

    @ActionProtector(not_anonymous())
    def relayed_via(self, id, archive=None):
        "return relayed via hosts used by ajax calls"
        message = self._get_msg(id, archive)
        if not message:
            abort(404)

        c.msg = message
        return render('/messages/includes/relayedvia.html')

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
        messages = self._get_messages().order_by(sort)
        # msgcount = self._get_msg_count()
        query = UserFilter(Session, c.user, messages)
        # countquery = UserFilter(Session, c.user, msgcount)
        messages = query.filter()
        # msgcount = countquery.filter()
        if filters:
            msgcount = self._get_msg_count()
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
        return render('/messages/listing.html')

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
        messages = self._get_messages().filter(
                    Message.isquarantined == 1).order_by(sort)
        msgcount = self._get_msg_count().filter(
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
        if request.POST:
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
        if request.POST and c.form.validate() and choices:
            msgs = Session.query(Message.id,
                    Message.messageid,
                    Message.from_address,
                    Message.timestamp, Message.to_address,
                    Message.hostname)\
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
                            date=convert_date(msg.timestamp, localtmz).strftime('%Y%m%d'),
                            to_address=msg.to_address,
                            hostname=msg.hostname,
                            mid=msg.id)
                        for msg in msgs)

            taskset = TaskSet(tasks=(
                                process_quarantined_msg.subtask(
                                    args=[formval],
                                    options=dict(queue=formval['hostname'])
                                ) for formval in formvals
                                )
                            )
            if formvals:
                try:
                    task = taskset.apply_async()
                    task.save(dbbackend)
                    session['bulk_items'] = []
                    if not 'taskids' in session:
                        session['taskids'] = []
                    session['taskids'].append(task.taskset_id)
                    session['bulkprocess-count'] = 1
                    session.save()
                    redirect(url('messages-bulk-process',
                            taskid=task.taskset_id))
                except QueueNotFound:
                    flash_alert(_('The messages could not processed'
                                ', try again later'))
        elif request.POST and not c.form.validate():
            flash_alert(_(u', '.join([unicode(c.form.errors[err][0])
                                    for err in c.form.errors])))
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
        return render('/messages/quarantine.html')

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
        messages = self._get_archived().order_by(sort)
        msgcount = self._get_msg_count(True)
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
        return render('/messages/archive.html')

    @ActionProtector(not_anonymous())
    def preview(self, id, archive=None, attachment=None, img=None,
                allowimgs=None):
        """Preview a message stored in the quarantine
        
        :param id: the database message id
        :param archive: optional. message archived status
        :param attachment: optional. request is for an attachmeny
        :param img: optional request is for an image
        :param allowimgs: optional allow display of remote images
        
        """
        if archive:
            message = self._get_archive(id)
        else:
            message = self._get_message(id)
        if not message:
            abort(404)

        try:
            localtmz = config.get('baruwa.timezone', 'Africa/Johannesburg')
            args = [message.messageid,
                    convert_date(message.timestamp, localtmz).strftime('%Y%m%d'),
                    attachment,
                    img,
                    allowimgs]
            task = preview_msg.apply_async(args=args,
                    queue=message.hostname.strip())
            task.wait(30)
            if task.result:
                if img:
                    response.content_type = task.result['content_type']
                    if task.result and 'img' in task.result:
                        info = MSGDOWNLOAD_MSG % dict(m=message.id,
                                                a=task.result['name'])
                        audit_log(c.user.username,
                                1, unicode(info), request.host,
                                request.remote_addr, now())
                        return base64.decodestring(task.result['img'])
                    abort(404)
                if attachment:
                    info = MSGDOWNLOAD_MSG % dict(m=message.id,
                                            a=task.result['name'])
                    audit_log(c.user.username,
                            1, unicode(info), request.host,
                            request.remote_addr, now())
                    response.content_type = task.result['mimetype']
                    content_disposition = 'attachment; filename="%s"' % \
                        task.result['name'].encode('ascii', 'replace')
                    response.headers['Content-Disposition'] = str(content_disposition)
                    response.headers['Content-Length'] = len(task.result['attachment'])
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
                                    url('message-preview-archived-with-imgs', id=id) \
                                    if archive else url('message-preview-with-imgs', id=id),
                                    class_='uline')))
                            else:
                                imgname = link.replace('cid:', '')
                                element.attrib['src'] = url('messages-preview-archived-img', img=imgname.replace('/', '__xoxo__'), id=id) \
                                if archive else url('messages-preview-img', img=imgname.replace('/', '__xoxo__'), id=id)
                        part['content'] = tostring(html)
                c.message = task.result
                info = MSGPREVIEW_MSG % dict(m=message.id)
                audit_log(c.user.username,
                        1, unicode(info), request.host,
                        request.remote_addr, now())
            else:
                c.message = {}
        except (socket.error, TimeoutError, QueueNotFound):
            flash_alert(_('The message could not be previewed, try again later'))
            whereto = url('message-archive', id=id) if archive else url('message-detail', id=id)
            redirect(whereto)
        c.messageid = message.messageid
        c.id = message.id
        c.archived = archive
        return render('/messages/preview.html')

    def autorelease(self, uuid):
        "release a message without logging in"
        releasereq = self._get_releasereq(uuid)
        if not releasereq:
            abort(404)

        released = False
        msgid = releasereq.messageid
        to_address = _('Unknown')
        errormsg = _('The message has already been released,'
                    ' you can only use the release link once')
        if releasereq.released == False:
            try:
                msg = Session.query(Message)\
                    .filter(Message.id == releasereq.messageid)\
                    .one()
            except (NoResultFound, MultipleResultsFound):
                abort(404)

            msgid = msg.messageid
            to_address = msg.to_address
            try:
                localtmz = config.get('baruwa.timezone', 'Africa/Johannesburg')
                task = release_message.apply_async(
                        args=[msg.messageid,
                            convert_date(msg.timestamp, localtmz).strftime('%Y%m%d'),
                            msg.from_address,
                            msg.to_address.split(',')],
                        queue=msg.hostname)
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
                result = dict(success=False, error=errormsg)

        c.messageid = msgid
        c.errormsg = errormsg
        c.released = released
        c.releaseaddress = to_address
        return render('/messages/autorelease.html')

    @ActionProtector(not_anonymous())
    def process(self, taskid, format=None):
        "process a taskset"
        result = TaskSetResult.restore(taskid, backend=dbbackend)
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
        #print '=' * 20, result.completed_count(), result.total, result.ready()
        if result.ready():
            finished = True
            results = result.join()
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
                flash_alert(_('An error occured in processing, try again later'))
                redirect(url(controller='messages', action='quarantine'))
            finished = False
            percent = "%.1f" % ((1.0 * int(result.completed_count()) /
                                int(result.total)) * 100)

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
        return render('/messages/taskstatus.html')

    @ActionProtector(not_anonymous())
    def search(self, format=None):
        "Search for messages"
        q = request.GET.get('q', None)
        if q is None:
            redirect(url(controller='messages', action='listing'))
        index = 'messages, messagesdelta, messages_rt'
        action = request.GET.get('a', 'listing')
        if not action in ['listing', 'quarantine', 'archive']:
            action = 'listing'
        if action == 'archive':
            index = 'archive archivedelta'
        try:
            page = int(request.GET.get('page', 1))
        except ValueError:
            page = 1
        num_items = session.get('msgs_search_num_results', 50)
        conn = SphinxClient()
        conn.SetMatchMode(SPH_MATCH_EXTENDED2)
        #conn.SetSortMode(SPH_SORT_EXTENDED, "timestamp DESC")
        if action == 'quarantine':
            conn.SetFilter('isquarantined', [True,])
        if page == 1:
            conn.SetLimits(0, num_items, 500)
        else:
            offset = (page - 1) * num_items
            conn.SetLimits(offset, num_items, 500)
        if not c.user.is_superadmin:
            filter_sphinx(Session, c.user, conn)
        else:
            conn.SetSelect('timestamp')
        q = clean_sphinx_q(q)
        results = conn.Query(q, index)
        q = restore_sphinx_q(q)
        if results and results['matches']:
            #import pprint
            #pprint.pprint(results)
            ids = [hit['id'] for hit in results['matches']]
            filters = session.get('filter_by', None)
            if index == 'archive':
                messages = self._get_archived().filter(
                            Archive.id.in_(ids))
                query = UserFilter(Session, c.user, messages, True)
                messages = query.filter()
                if filters:
                    dynq = DynaQuery(Message, messages, filters)
                    messages = dynq.generate()
            else:
                messages = self._get_messages().filter(
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
            print '=' * 100
            print conn.GetLastError()
            messages = []
            results = dict(matches=[], total=0)
            total_found = 0
            search_time = 0

        pages = paginator(dict(page=page, results_per_page=num_items,
                                total=results['total'],
                                items=len(results['matches']),
                                q=q))

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
        return render('/messages/searchresults.html')

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
