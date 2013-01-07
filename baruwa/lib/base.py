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
"""The base Controller API

Provides the BaseController class for subclassing.
"""

from pytz import timezone
from babel.util import UTC
from pylons import request, session
from pylons import tmpl_context as c
from pylons.i18n.translation import set_lang
from pylons.controllers import WSGIController
from pylons.templating import render_mako as render
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import joinedload_all, joinedload

from baruwa.model.meta import Session
from baruwa.lib.misc import check_language
from baruwa.lib.cluster import cluster_status
from baruwa.lib.query import DailyTotals, MailQueue
from baruwa.lib.caching_query import FromCache
from baruwa.model.domains import Domain
from baruwa.model.accounts import User


class BaseController(WSGIController):

    def __before__(self):
        "before"
        if 'lang' in session:
            set_lang(session['lang'])
        else:
            try:
                languages = [lang.split('-')[0] for lang in request.languages
                        if check_language(lang.split('-')[0])]
                set_lang(languages)
            except AttributeError:
                set_lang(['en'])
        self.invalidate = request.GET.get('uc', None)
        self.langchange = request.GET.get('lc', None)

    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        def check_url():
            if ('format' in environ['pylons.routes_dict'] and
                environ['pylons.routes_dict']['format'] in ['csv', 'pdf']):
                return False
            if environ['PATH_INFO'] == '/jsi18n.js':
                return False
            return True

        self.identity = environ.get('repoze.who.identity')
        # raise ValueError(self.identity)
        # if 'baruwa.auth.plugin' in self.identity:
        #     session['baruwa.auth.plugin'] = self.identity['baruwa.auth.plugin']
        #     session.save()
        if (not self.identity is None and 'user' in self.identity and
            environ['pylons.routes_dict']['controller'] != 'error' and
            check_url()):

            if self.identity['user']:
                totals = DailyTotals(Session, self.identity['user'])
                mailq = MailQueue(Session, self.identity['user'])
                c.baruwa_totals = totals.get()
                c.baruwa_inbound = mailq.get(1)[0]
                c.baruwa_outbound = mailq.get(2)[0]
                if self.identity['user'].is_admin:
                    c.baruwa_status = cluster_status()

                tzinfo = self.identity['user'].timezone or UTC
                if isinstance(tzinfo, basestring):
                    tzinfo = timezone(tzinfo)

                c.tzinfo = tzinfo
        try:
            return WSGIController.__call__(self, environ, start_response)
        finally:
            Session.remove()

    def _get_domain(self, domainid):
        "utility to return domain"
        try:
            cachekey = 'domain-%s' % domainid
            q = Session.query(Domain).filter(Domain.id==domainid)\
                    .options(joinedload_all(Domain.servers),
                            joinedload_all(Domain.aliases),
                            joinedload_all(Domain.authservers))\
                    .options(FromCache('sql_cache_med', cachekey))
            if self.invalidate:
                q.invalidate()
            domain = q.one()
        except NoResultFound:
            domain = None
        return domain

    def _get_user(self, userid):
        "utility to return user"
        try:
            cachekey = 'user-%s' % userid
            q = Session.query(User).filter(User.id == userid)\
                    .options(joinedload('addresses'))\
                    .options(FromCache('sql_cache_med', cachekey))
            if self.invalidate:
                q.invalidate()
            user = q.one()
        except NoResultFound:
            user = None
        return user
