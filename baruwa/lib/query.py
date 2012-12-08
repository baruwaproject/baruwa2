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

"Query functions"

import MySQLdb

from sqlalchemy import func, desc
from sqlalchemy.sql import and_, or_, case

from baruwa.model.meta import Session
from baruwa.lib.dates import now
from baruwa.model.messages import Message, Archive
from baruwa.model.domains import Domain
from baruwa.model.status import MailQueueItem
from baruwa.lib.caching_query import FromCache
from baruwa.model.accounts import domain_owners as downs
from baruwa.model.accounts import organizations_admins as oa
from baruwa.model.reports import MessageTotals, SrcMessageTotals
from baruwa.model.reports import DstMessageTotals
from baruwa.lib.misc import REPORTS, crc32
from baruwa.lib.regex import CLEANQRE, EXIM_MSGID_RE, SQL_URL_RE


class DynaQuery(object):
    "dynamic queries"
    def __init__(self, model, query, filters):
        "init"
        self.query = query
        self.filters = filters
        self.addclauses = []
        self.orclauses = {}
        self.kwargs = {}
        self.lkwargs = {}
        self.model = model

    def _load_keys(self, key, expr):
        "load keys"
        if key in self.kwargs:
            if not key in self.orclauses:
                self.orclauses[key] = []
            self.orclauses[key].append(expr)
            self.orclauses[key].append(self.kwargs[key])
            self.lkwargs.update({key: expr})
            del self.kwargs[key]
        else:
            if key in self.lkwargs:
                if not key in self.orclauses:
                    self.orclauses[key] = []
                self.orclauses[key].append(expr)
            else:
                self.kwargs.update({key: expr})

    def generate(self):
        "generate query"
        for filt in self.filters:
            attr = getattr(self.model, filt['field'])
            if filt['filter'] == '1':
                key = "%s_equal" % filt['field']
                expr = attr == filt['value']
                self._load_keys(key, expr)
            if filt['filter'] == '2':
                key = "%s_notequal" % filt['field']
                expr = attr != filt['value']
                self._load_keys(key, expr)
            if filt['filter'] == '3':
                key = "%s_greaterthan" % filt['field']
                expr = attr > filt['value']
                self._load_keys(key, expr)
            if filt['filter'] == '4':
                key = "%s_lessthan" % filt['field']
                expr = attr < filt['value']
                self._load_keys(key, expr)
            if filt['filter'] == '5':
                key = "%s_contains" % filt['field']
                expr = attr.ilike('%' + filt['value'] + '%')
                self._load_keys(key, expr)
            if filt['filter'] == '6':
                key = "%s_ncontains" % filt['field']
                expr = ~attr.ilike('%' + filt['value'] + '%')
                self._load_keys(key, expr)
            if filt['filter'] == '7':
                key = "%s_regex" % filt['field']
                expr = attr.op('regexp')(filt['value'])
                self._load_keys(key, expr)
            if filt['filter'] == '8':
                key = "%s_nregex" % filt['field']
                expr = ~attr.op('regexp')(filt['value'])
                self._load_keys(key, expr)
            if filt['filter'] == '9':
                key = "%s_isnull" % filt['field']
                expr = attr == None
                self._load_keys(key, expr)
            if filt['filter'] == '10':
                key = "%s_nisnull" % filt['field']
                expr = attr != None
                self._load_keys(key, expr)
            if filt['filter'] == '11':
                key = "%s_istrue" % filt['field']
                expr = attr > 0
                self._load_keys(key, expr)
            if filt['filter'] == '12':
                key = "%s_isfalse" % filt['field']
                expr = attr <= 0
                self._load_keys(key, expr)
        self.addclauses.extend(self.kwargs.values())
        if self.addclauses or self.orclauses:
            if self.addclauses and self.orclauses:
                orlist = [or_(*self.orclauses[key])
                        for key in self.orclauses]
                query = self.query.filter(
                and_(and_(*self.addclauses), *orlist))
            else:
                if self.addclauses:
                    query = self.query.filter(and_(*self.addclauses))
                if self.orclauses:
                    orlist = [or_(*self.orclauses[key])
                            for key in self.orclauses]
                    query = self.query.filter(and_(*orlist))
            return query
        return self.query


class UserFilter(object):
    "filter user query"
    def __init__(self, dbsession, user, query, archived=None, model=None):
        "Init"
        self.dbsession = dbsession
        self.user = user
        self.query = query
        if model is None:
            self.model = Message
        else:
            self.model = model
        self.direction = None
        if archived:
            self.model = Archive

    def __call__(self):
        "Set filters"
        return self.filter()

    def setdirection(self, direction):
        "set direction"
        self.direction = direction

    def filter(self):
        "Set filters"
        if self.user.is_domain_admin:
            dquery = self.dbsession.query(Domain.name).join(downs,
                    (oa, downs.c.organization_id == oa.c.organization_id))\
                    .filter(Domain.status == True)\
                    .filter(oa.c.user_id == self.user.id).all()
            domains = [domain.name for domain in dquery]
            if not domains:
                domains.append('xx')
            if self.direction and self.direction == 'in':
                self.query = self.query\
                            .filter(self.model.to_domain.in_(domains))
            elif self.direction and self.direction == 'out':
                self.query = self.query\
                            .filter(self.model.from_domain.in_(domains))
            else:
                self.query = self.query.filter(
                            func._(or_(self.model.to_domain.in_(domains),
                            self.model.from_domain.in_(domains))))
        if self.user.is_peleb:
            addrs = [addr.address for addr in self.user.addresses]
            addrs.append(self.user.email)
            if self.direction and self.direction == 'in':
                self.query = self.query\
                            .filter(self.model.to_address.in_(addrs))
            elif self.direction and self.direction == 'out':
                self.query = self.query\
                            .filter(self.model.from_address.in_(addrs))
            else:
                self.query = self.query\
                            .filter(func._(
                                or_(self.model.to_address.in_(addrs),
                                self.model.from_address.in_(addrs))))
        return self.query


class MailQueue(object):
    def __init__(self, dbsession, user):
        "init"
        self.dbsession = dbsession
        self.user = user
        self.query = self.dbsession.query(func.count(MailQueueItem.id))
        if self.user.is_domain_admin:
            dquery = self.dbsession.query(Domain.name).join(downs,
                    (oa, downs.c.organization_id == oa.c.organization_id))\
                    .filter(Domain.status == True)\
                    .filter(oa.c.user_id == self.user.id).all()
            domains = [domain.name for domain in dquery]
            if not domains:
                domains.append('xx')
            self.query = self.query.filter(
                            func._(or_(MailQueueItem.to_domain.in_(domains),
                            MailQueueItem.from_domain.in_(domains))))
        if self.user.is_peleb:
            addrs = [addr.address for addr in self.user.addresses]
            addrs.append(self.user.email)
            self.query = self.query\
                        .filter(func._(
                        or_(MailQueueItem.to_address.in_(addrs),
                        MailQueueItem.from_address.in_(addrs))))

    def get(self, direction=1, hostname=None):
        "return mailq"
        cachekey = 'mq-%s-%s-%s' % (self.user.username,
                                    str(hostname),
                                    str(direction))
        if hostname:
            query = self.query.filter(MailQueueItem.hostname == hostname)
        else:
            query = self.query
        query = query.filter(MailQueueItem.direction == direction)
        try:
            query = query.options(FromCache('sql_cache_short', cachekey))
        except ValueError:
            pass
        return query.one()


class DailyTotals(object):
    def __init__(self, dbsession, user):
        self.dbsession = dbsession
        self.user = user
        self.query = self.dbsession.query(
            func.count(Message.id).label('total'),
            func.sum(case([(and_(Message.virusinfected == 0,
                Message.nameinfected == 0, Message.otherinfected == 0,
                Message.spam == 0, Message.highspam == 0), 1)],
                else_=0)).label('clean'),
            func.sum(case([(Message.virusinfected > 0, 1)],
                else_=0)).label('virii'),
            func.sum(case([(and_(Message.highspam == 0,
                Message.spam == 0, Message.virusinfected == 0,
                or_(Message.nameinfected > 0, Message.otherinfected > 0)), 1)],
                else_=0)).label('infected'),
            func.sum(case([(and_(Message.virusinfected == 0,
                Message.otherinfected == 0, Message.nameinfected == 0,
                or_(Message.spam > 0, Message.highspam > 0)), 1)],
                else_=0)).label('spam'),
            func.sum(case([(and_(Message.virusinfected == 0,
                Message.otherinfected == 0, Message.nameinfected == 0,
                Message.spam > 0, Message.highspam == 0), 1)],
                else_=0)).label('lowspam'),
            func.sum(case([(and_(Message.virusinfected == 0,
                Message.otherinfected == 0, Message.nameinfected == 0,
                Message.highspam > 0), 1)],
                else_=0)).label('highspam'))\
                .filter(Message.date == now().date())

    def get(self, hostname=None):
        if not hostname is None:
            self.query = self.query.filter(Message.hostname == hostname)
        if self.user.is_domain_admin:
            dquery = self.dbsession.query(Domain.name).join(downs,
                    (oa, downs.c.organization_id == oa.c.organization_id))\
                    .filter(Domain.status == True)\
                    .filter(oa.c.user_id == self.user.id).all()
            if not dquery:
                dquery.append('xx')
            self.query = self.query.filter(func._(
                        or_(Message.to_domain.in_(dquery),
                        Message.from_domain.in_(dquery))))
        if self.user.is_peleb:
            addrs = [addr.address for addr in self.user.addresses]
            addrs.append(self.user.email)
            self.query = self.query.filter(
                        func._(or_(Message.to_address.in_(addrs),
                        Message.from_address.in_(addrs))))
        cachekey = 'dailytotals-%s-%s' % (self.user.username, hostname)
        self.query = self.query.options(FromCache('sql_cache_short', cachekey))
        return self.query.one()


class ReportQuery(object):
    def __init__(self, user, reportid, filters=None):
        "Init"
        self.dbsession = Session
        self.user = user
        self.reportid = reportid
        self.model = None
        self.isaggr = False
        self.filters = filters

        queryfield = getattr(Message, REPORTS[self.reportid]['address'])
        orderby = REPORTS[reportid]['sort']
        if (self.reportid in ['3', '4', '7', '8']
            and self.user.is_superadmin
            and not self.filters):
            # domains
            self.isaggr = True
            if self.reportid in ['3', '4']:
                #src
                self.model = SrcMessageTotals
                self.query = self.dbsession\
                            .query(SrcMessageTotals.id.label('address'),
                            SrcMessageTotals.total.label('count'),
                            SrcMessageTotals.volume.label('size'))\
                            .order_by(desc(orderby))
            else:
                #dst
                self.model = DstMessageTotals
                self.query = self.dbsession\
                            .query(DstMessageTotals.id.label('address'),
                            DstMessageTotals.total.label('count'),
                            DstMessageTotals.volume.label('size'))\
                            .order_by(desc(orderby))
        else:
            # emails & relays
            self.query = self.dbsession.query(queryfield.label('address'),
                                    func.count(queryfield).label('count'),
                                    func.sum(Message.size).label('size'))
            if self.reportid != '10':
                self.query = self.query.filter(queryfield != u'')\
                            .group_by(queryfield).order_by(desc(orderby))
            else:
                self.query = self.query.filter(queryfield != u'127.0.0.1')\
                            .group_by(queryfield).order_by(desc(orderby))
        if self.isaggr:
            uquery = AggrFilter(self.query)
        else:
            uquery = UserFilter(self.dbsession,
                                self.user,
                                self.query)
        if not self.reportid in ['5', '6', '7', '8']:
            self.query = uquery()
        if self.reportid in ['5', '6', '7', '8']:
            if not self.user.is_superadmin:
                uquery.setdirection('in')
                self.query = uquery()
            else:
                flf = self.model.id if self.isaggr else Message.to_domain
                self.query = self.query.filter(flf\
                            .in_(self.dbsession.query(Domain.name)\
                            .filter(Domain.status == True)))

    def __call__(self):
        "Return report query"
        return self.get()

    def get(self):
        "Return report query"
        if self.filters:
            dynq = DynaQuery(Message, self.query, self.filters)
            self.query = dynq.generate()
        return self.query


class AggrFilter(object):
    "dummy filter"

    def __init__(self, query):
        self.query = query

    def __call__(self):
        return self.query


class MsgCount(object):
    "message count"

    def __init__(self, dbsession, user):
        "Init"
        self.dbsession = dbsession
        self.user = user
        if not self.user.is_peleb:
            self.query = self.dbsession\
                        .query(func.sum(MessageTotals.runtotal)\
                        .label('total'))
        else:
            self.query = self.dbsession\
                        .query(func.count(Message.id)\
                        .label('total'))

    def __call__(self):
        "return count"
        return self.count()

    def count(self):
        "Get the count"
        if self.user.is_domain_admin:
            dquery = self.dbsession.query(Domain.name).join(downs,
                    (oa, downs.c.organization_id == oa.c.organization_id))\
                    .filter(Domain.status == True)\
                    .filter(oa.c.user_id == self.user.id).all()
            domains = [domain.name for domain in dquery]
            self.query = self.query.filter(MessageTotals.id.in_(domains))
        elif self.user.is_peleb:
            addrs = [addr.address for addr in self.user.addresses]
            addrs.append(self.user.email)
            self.query = self.query.filter(func._(or_(Message\
                                .to_address.in_(addrs),
                                Message.from_address.in_(addrs))))
        value = self.query.one()
        return int(value.total or 0)


def sa_scores(dbsession, user):
    "SA scores query"
    query = dbsession.query(func.round(Message.sascore).label('score'),
            func.count('score').label('count'))\
            .filter(Message.scaned == 1)\
            .filter(Message.whitelisted != 1)\
            .group_by('score').order_by('score')

    #cachekey = u'sascores-%s' % user.username
    uquery = UserFilter(dbsession, user, query)
    query = uquery.filter()
    #query = query.options(FromCache('sql_cache_short', cachekey))
    return query


def message_totals(dbsession, user):
    "Message totals query"
    query = dbsession.query(Message.date,
                            func.count(Message.date).label('mail_total'),
                            func.sum(case([(Message.virusinfected > 0, 1)],
                                else_=0)).label('virus_total'),
                            func.sum(case([(and_(Message.virusinfected == 0,
                                Message.spam > 0), 1)],
                                else_=0)).label('spam_total'),
                            func.sum(Message.size).label('total_size')
                                ).group_by(Message.date).order_by(
                                desc(Message.date))
    uquery = UserFilter(dbsession, user, query)
    query = uquery.filter()
    return query


def get_dom_crcs(dbsession, user):
    "Calc CRC32 for domains"
    domains = dbsession.query(Domain.name).join(downs,
                (oa, downs.c.organization_id == oa.c.organization_id))\
                .filter(oa.c.user_id == user.id)
    crcs = [crc32(domain[0]) for domain in domains]
    return crcs


def filter_sphinx(dbsession, user, conn):
    "Set Sphinx filters"
    if user.is_domain_admin:
        crcs = get_dom_crcs(dbsession, user)
        if not crcs:
            crcs.append(crc32('xx'))
        addrs = ', '.join([str(crc) for crc in crcs])
        select = 'IN(from_dom,%s) OR IN(to_dom,%s) AS cond2' % (addrs, addrs)
        conn.SetSelect(str(select))
        conn.SetFilter('cond2', [1])
    if user.is_peleb:
        crcs = [str(crc32(address.address)) for address in user.addresses]
        crcs.append(str(crc32(user.email)))
        addrs = ', '.join(crcs)
        select = 'IN(from_addr,%s) OR IN(to_addr,%s) AS cond1' % (addrs, addrs)
        conn.SetSelect(str(select))
        conn.SetFilter('cond1', [1])


def clean_sphinx_q(query):
    "reformat special chars"
    if '@' in query and not CLEANQRE.match(query):
        query = query.replace('@', '\@')
    if EXIM_MSGID_RE.match(query):
        query = query.replace('-', '\-')
    return query


def restore_sphinx_q(query):
    "restore for display"
    return query.replace('\@', '@').replace('\-', '-')


def make_conn_dict(url):
    "Make a dict that can be used by mysqldb"
    match = SQL_URL_RE.match(url)
    if match:
        conndict = match.groupdict()
        conndict['port'] = int(conndict['port'])
        conndict['use_unicode'] = True
        del conndict['db']
        del conndict['name']
    else:
        conndict = dict(host='127.0.0.1',
                        port=9306,
                        use_unicode=True,
                        user='root')
    return conndict


def format_sphinx_ids(length):
    "Format ids as string to add to SQL query"
    mstr = '%s,' * length
    mstr = mstr.rstrip(',')
    return mstr


def sphinx_connection(url):
    "Make a connection to sphinx return connection object"
    conn = MySQLdb.connect(**make_conn_dict(url))
    return conn

    