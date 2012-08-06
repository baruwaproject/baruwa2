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

from StringIO import StringIO

from pyrad import packet
from pyrad.client import Client, Timeout
from pyrad.dictionary import Dictionary
from zope.interface import implements
from repoze.who.utils import resolveDotted
from repoze.who.interfaces import IAuthenticator
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import func
from sqlalchemy.sql import and_, or_

from baruwa.lib.auth import check_param, check_failed_logins
from baruwa.lib.regex import USER_TEMPLATE_MAP_RE, DOM_TEMPLATE_MAP_RE

DICTIONARY = u"""
ATTRIBUTE User-Name     1 string
ATTRIBUTE User-Password 2 string encrypt=1
"""


class BaruwaRadiusAuthPlugin(object):
    """Baruwa radius repoze.who authentication plugin"""
    implements(IAuthenticator)
    name = 'radius'

    def __init__(self, dbsession, radsettingsmodel, authsettingsmodel,
                domainmodel, domainaliasmodel):
        self.dbsession = dbsession
        self.domainmodel = domainmodel
        self.aliasmodel = domainaliasmodel
        self.radsettingsmodel = radsettingsmodel
        self.authsettingsmodel = authsettingsmodel

    def authenticate(self, environ, identity):
        """authenticator"""
        try:
            if check_failed_logins(environ):
                return None

            login = identity['login'].decode('utf-8')
            password = identity['password'].decode('utf-8')
            username = login
            domain = None
            if '@' not in login:
                return None
            username, domain = login.split('@')

            and_clause = and_(self.domainmodel.id == self.aliasmodel.domain_id,
                            self.aliasmodel.name == domain,
                            self.aliasmodel.status == True)

            radiussettings = self.dbsession.query(self.radsettingsmodel,
                            self.authsettingsmodel.address,
                            self.authsettingsmodel.port,
                            self.authsettingsmodel.split_address,
                            self.authsettingsmodel.user_map_template,
                            self.domainmodel.name)\
                            .join(self.authsettingsmodel)\
                            .join(self.domainmodel)\
                            .filter(self.authsettingsmodel.enabled == True)\
                            .filter(self.domainmodel.status == True)\
                            .filter(or_(self.domainmodel.name == domain,
                                    func._(and_clause)))\
                            .all()
            settings, address, port, split_address, template, \
            domain_name = radiussettings[0]
            if not port:
                port = 1812
            radclient = Client(server=address, authport=port,
                        secret=settings.secret.encode('utf-8'),
                        dict=Dictionary(StringIO(DICTIONARY)))
            if settings.timeout:
                radclient.timeout = settings.timeout

            if split_address:
                login = username

            if domain != domain_name:
                identity['login'] = "%s@%s" % (username, domain_name)
                if not split_address:
                    login = "%s@%s" % (username, domain_name)

            if (template and (USER_TEMPLATE_MAP_RE.search(template) or
                DOM_TEMPLATE_MAP_RE.search(template))):
                # domain has user template
                login = USER_TEMPLATE_MAP_RE.sub(username, template)
                login = DOM_TEMPLATE_MAP_RE.sub(domain, login)

            request = radclient.CreateAuthPacket(code=packet.AccessRequest,
                        User_Name=login)
            request["User-Password"] = request.PwCrypt(password)
            reply = radclient.SendPacket(request)
            if reply.code == packet.AccessAccept:
                return identity['login']
        except (KeyError, IndexError, NoResultFound, Timeout):
            return None
        return None


def make_rad_authenticator(dbsession, radsettingsmodel, authsettingsmodel,
                            domainmodel, domainaliasmodel):
    "return radius authenticator"
    for param in [('dbsession', dbsession),
                ('radsettingsmodel', radsettingsmodel),
                ('authsettingsmodel', authsettingsmodel),
                ('domainmodel', domainmodel),
                ('domainaliasmodel', domainaliasmodel)]:
        check_param(param[0], param[1])
    session = resolveDotted(dbsession)
    radmodel = resolveDotted(radsettingsmodel)
    authmodel = resolveDotted(authsettingsmodel)
    dmodel = resolveDotted(domainmodel)
    damodel = resolveDotted(domainaliasmodel)

    authenticator = BaruwaRadiusAuthPlugin(session, radmodel,
                                        authmodel, dmodel,
                                        damodel)

    return authenticator
