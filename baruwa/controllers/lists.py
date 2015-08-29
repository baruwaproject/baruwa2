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
"Lists controller"

import socket
import struct
import logging

import arrow

from urlparse import urlparse

from pylons import request, response, session, tmpl_context as c, url, config
from pylons.controllers.util import abort, redirect
from webhelpers import paginate
from pylons.i18n.translation import _
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
from repoze.what.predicates import not_anonymous
from sphinxapi import SphinxClient, SPH_MATCH_EXTENDED2
from repoze.what.plugins.pylonshq import ControllerProtector

from baruwa.model.lists import List
from baruwa.model.meta import Session
from baruwa.lib.audit import audit_log
from baruwa.model.domains import Domain
from baruwa.lib.api import get_listitem
from baruwa.forms.lists import list_forms
from baruwa.lib.base import BaseController
from baruwa.lib.misc import convert_list_to_json
from baruwa.lib.helpers import flash, flash_alert
from baruwa.lib.backend import update_lists_backend
from baruwa.lib.audit.msgs import lists as auditmsgs
from baruwa.model.accounts import User, Address, domain_owners
from baruwa.lib.misc import check_num_param, extract_sphinx_opts
from baruwa.lib.regex import EMAIL_RE, IPV4_NET_OR_RANGE_RE, DOM_RE, IPV4_RE

log = logging.getLogger(__name__)


def make_item(form):
    "Make a list item"
    litem = List()
    litem.user = c.user
    litem.list_type = form.list_type.data
    litem.from_address = form.from_address.data
    return litem


def _set_type(obj):
    "Set type of object"
    if EMAIL_RE.match(obj.from_address):
        obj.from_addr_type = 1
        return
    if DOM_RE.match(obj.from_address):
        obj.from_addr_type = 2
        return
    if IPV4_NET_OR_RANGE_RE.match(obj.from_address):
        obj.from_addr_type = 3
        return
    if IPV4_RE.match(obj.from_address):
        obj.from_addr_type = 4
        return


@ControllerProtector(not_anonymous())
class ListsController(BaseController):
    "Lists Controller"
    def __before__(self):
        "set context"
        BaseController.__before__(self)
        if self.identity:
            c.user = self.identity['user']
        else:
            c.user = None
        c.selectedtab = 'lists'
        c.is_ajax = request.is_xhr

    def _user_addresses(self):
        "Return user addresses"
        userid = self.identity['user'].id
        query1 = Session.query(User.email.label('email'))\
                .filter_by(active=True, account_type=3, id=userid)
        query2 = Session.query(Address.address.label('email'))\
                .filter_by(enabled=True, user_id=userid)
        return query1.union(query2)

    # pylint: disable-msg=W0622,R0913,R0914,R0915
    def index(self, list_type=1, direction='dsc', order_by='id',
            page=1, format=None):
        "Page through lists"
        total_found = 0
        search_time = 0
        num_items = session.get('lists_num_items', 10)
        if direction == 'dsc':
            sort = desc(order_by)
        else:
            sort = order_by
        qry = request.GET.get('q', None)
        kwds = {}
        if qry:
            kwds['presliced_list'] = True
            conn = SphinxClient()
            sphinxopts = extract_sphinx_opts(config['sphinx.url'])
            conn.SetServer(sphinxopts.get('host', '127.0.0.1'))
            conn.SetMatchMode(SPH_MATCH_EXTENDED2)
            conn.SetFilter('list_type', [int(list_type), ])
            if not c.user.is_superadmin:
                conn.SetFilter('user_id', [c.user.id, ])
            if page == 1:
                conn.SetLimits(0, num_items, 500)
            else:
                page = int(page)
                offset = (page - 1) * num_items
                conn.SetLimits(offset, num_items, 500)

            try:
                results = conn.Query(qry, 'lists, lists_rt')
            except (socket.timeout, struct.error):
                redirect(request.path_qs)

            if results and results['matches']:
                ids = [hit['id'] for hit in results['matches']]
                total_found = results['total_found']
                search_time = results['time']
                items = Session.query(List)\
                        .filter(List.list_type == list_type)\
                        .filter(List.id.in_(ids))\
                        .order_by(sort)\
                        .all()
                listcount = total_found
            else:
                items = []
                itemcount = 0
                listcount = 0
        else:
            items = Session.query(List)\
                    .filter(List.list_type == list_type)\
                    .order_by(sort)
            itemcount = Session.query(List.id)\
                    .filter(List.list_type == list_type)
            if not c.user.is_superadmin:
                items = items.filter(List.user_id == c.user.id)
                itemcount = itemcount.filter(List.user_id == c.user.id)
            listcount = itemcount.count()

        # pylint: disable-msg=W0142
        records = paginate.Page(items,
                                page=int(page),
                                items_per_page=num_items,
                                item_count=listcount,
                                **kwds)
        if format == 'json':
            response.headers['Content-Type'] = 'application/json'
            data = convert_list_to_json(records, list_type)
            return data

        c.list_type = list_type
        c.page = records
        c.direction = direction
        c.order_by = order_by
        c.q = qry
        c.total_found = total_found
        c.search_time = search_time
        return self.render('/lists/index.html')

    # pylint: disable-msg=R0912
    def new(self):
        "Add a new list item"
        c.form = list_forms[c.user.account_type](request.POST,
                                            csrf_context=session)
        if c.user.is_domain_admin:
            orgs = [group.id for group in c.user.organizations]
            query = Session.query(Domain.name).join(domain_owners)\
                    .filter(domain_owners.c.organization_id.in_(orgs))
            options = [(domain.name, domain.name) for domain in query]
            # options.insert(0, ('any', _('All domains')))
            c.form.to_domain.choices = options
        if c.user.is_peleb:
            query = self._user_addresses()
            options = [(item.email, item.email) for item in query]
            c.form.to_address.choices = options
        if request.method == 'POST' and c.form.validate():
            item = make_item(c.form)
            _set_type(item)
            aliases = []
            if c.user.is_superadmin or c.user.is_peleb:
                if c.form.to_address.data != '':
                    item.to_address = c.form.to_address.data
                    if ('add_to_alias' in c.form and c.form.add_to_alias.data
                        and c.user.is_peleb):
                        for new_addr in options:
                            if new_addr[0] == item.to_address:
                                continue
                            newitem = make_item(c.form)
                            _set_type(newitem)
                            newitem.to_address = new_addr[0]
                            aliases.append(newitem)
                else:
                    item.to_address = 'any'
            if c.user.is_domain_admin:
                if c.form.to_address.data in ['', 'any']:
                    item.to_address = c.form.to_domain.data
                    if c.form.add_to_alias.data:
                        for dom in options:
                            if dom[0] == item.to_address:
                                continue
                            newitem = make_item(c.form)
                            _set_type(newitem)
                            newitem.to_address = dom[0]
                            aliases.append(newitem)
                else:
                    item.to_address = "%s@%s" % (c.form.to_address.data,
                    c.form.to_domain.data)
                    if c.form.add_to_alias.data:
                        for dom in options:
                            newitem = make_item(c.form)
                            _set_type(newitem)
                            newitem.to_address = "%s@%s" % \
                                        (c.form.to_address.data, dom[0])
                            if newitem.to_address == item.to_address:
                                continue
                            aliases.append(newitem)
            try:
                Session.add(item)
                Session.commit()
                for alias in aliases:
                    try:
                        Session.add(alias)
                        Session.commit()
                    except IntegrityError:
                        pass
                update_lists_backend(item.list_type)
                if item.list_type == 1:
                    listname = _('Approved senders')
                else:
                    listname = _('Banned senders')
                info = auditmsgs.LISTADD_MSG % dict(s=item.from_address,
                                                    l=listname)
                audit_log(c.user.username,
                        3, unicode(info), request.host,
                        request.remote_addr, arrow.utcnow().datetime)
                flash(_('The item has been added to the list'))
                if not request.is_xhr:
                    redirect(url('lists-index',
                            list_type=c.form.list_type.data))
            except IntegrityError:
                Session.rollback()
                flash_alert(_('The list item already exists'))
        return self.render('/lists/add.html')

    def list_delete(self, listid):
        "Delete a list item"
        item = get_listitem(listid)
        if not item:
            abort(404)

        if c.user.account_type != 1 and c.user.id != item.user_id:
            abort(403)

        c.form = list_forms[c.user.account_type](request.POST,
                                                item,
                                                csrf_context=session)
        if not c.user.is_superadmin:
            del c.form.add_to_alias
        if c.user.is_domain_admin:
            orgs = [group.id for group in c.user.organizations]
            query = Session.query(Domain.name).join(domain_owners)\
                    .filter(domain_owners.c.organization_id.in_(orgs))
            options = [(domain.name, domain.name) for domain in query]
            # options.insert(0, ('any', _('All domains')))
            c.form.to_domain.choices = options
        if c.user.is_peleb:
            query = self._user_addresses()
            options = [(addr.email, addr.email) for addr in query]
            c.form.to_address.choices = options
        c.id = item.id
        if request.method == 'POST' and c.form.validate():
            if item.list_type == 1:
                listname = _('Approved senders')
            else:
                listname = _('Banned senders')
            name = item.from_address
            list_type = item.list_type
            Session.delete(item)
            Session.commit()
            update_lists_backend(list_type)
            info = auditmsgs.LISTDEL_MSG % dict(s=name, l=listname)
            audit_log(c.user.username,
                    4, unicode(info), request.host,
                    request.remote_addr, arrow.utcnow().datetime)
            flash(_('The item has been deleted'))
            if not request.is_xhr:
                redirect(url(controller='lists'))
            else:
                c.delflag = True
        return self.render('/lists/delete.html')

    # pylint: disable-msg=W0613,R0201,W0622
    def setnum(self, format=None):
        "Set number of items returned"
        num = check_num_param(request)

        if num and int(num) in [10, 20, 50, 100]:
            num = int(num)
            session['lists_num_items'] = num
            session.save()
        nextpage = request.headers.get('Referer', '/')
        if '://' in nextpage:
            from_url = urlparse(nextpage)
            nextpage = from_url[2]
        redirect(nextpage)
