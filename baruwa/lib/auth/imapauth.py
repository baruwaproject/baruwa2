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

"""IMAP authentication repoze.who plugin"""

import socket
import imaplib

from ssl import SSLError

from zope.interface import implements
from repoze.who.utils import resolveDotted
from repoze.who.interfaces import IAuthenticator
from sqlalchemy.orm.exc import NoResultFound

from baruwa.lib.auth import check_param, check_failed_logins
from baruwa.lib.regex import USER_TEMPLATE_MAP_RE, DOM_TEMPLATE_MAP_RE


class BaruwaIMAPAuthPlugin(object):
    """Baruwa IMAP repoze.who authentication plugin"""
    implements(IAuthenticator)
    name = 'imap'

    def __init__(self, dbsession, asm, dommodel, dam):
        self.dbsession = dbsession
        self.dommodel = dommodel
        self.dam = dam
        self.asm = asm

    def authenticate(self, environ, identity):
        """authenticator"""
        try:
            if check_failed_logins(environ):
                return None

            login = identity['login']
            password = identity['password']
            username = login
            domain = None
            is_alias = False

            if '@' not in login:
                return None

            username, domain = login.split('@')

            try:
                dma = self.dbsession.query(self.dommodel.name)\
                        .join(self.dam)\
                        .filter(self.dam.name == domain).one()
                domain = dma.name
                is_alias = True
            except NoResultFound:
                pass

            imapsettings = self.dbsession.query(self.asm.port,
                            self.asm.address,
                            self.asm.split_address,
                            self.asm.user_map_template)\
                            .join(self.dommodel)\
                            .filter(self.asm.protocol == 2)\
                            .filter(self.asm.enabled == True)\
                            .filter(self.dommodel.status == True)\
                            .filter(self.dommodel.name == domain)\
                            .one()

            port, address, split_address, template = imapsettings

            if split_address:
                login = username

            if is_alias:
                identity['login'] = "%s@%s" % (username, domain)
                if not split_address:
                    login = "%s@%s" % (username, domain)

            if (template and (USER_TEMPLATE_MAP_RE.search(template) or
                DOM_TEMPLATE_MAP_RE.search(template))):
                # domain has user template
                login = USER_TEMPLATE_MAP_RE.sub(username, template)
                login = DOM_TEMPLATE_MAP_RE.sub(domain, login)

            if port == 993:
                conn = imaplib.IMAP4_SSL(address)
            elif port == 143 or port is None:
                conn = imaplib.IMAP4(address)
            else:
                conn = imaplib.IMAP4(address, port)

            conn.login(login, password)
            return identity['login']
        except (KeyError, IndexError, NoResultFound, imaplib.IMAP4.error,
                socket.error, SSLError):
            return None
        finally:
            if 'conn' in locals():
                conn.logout()
        return None


def make_imap_authenticator(dbsession, asm, dommodel, dam):
    "return imap authenticator"
    for param in [('dbsession', dbsession),
                ('asm', asm),
                ('dommodel', dommodel),
                ('dam', dam)]:
        check_param(param[0], param[1])
    session = resolveDotted(dbsession)
    authmodel = resolveDotted(asm)
    dmodel = resolveDotted(dommodel)
    damodel = resolveDotted(dam)

    authenticator = BaruwaIMAPAuthPlugin(session, authmodel, dmodel, damodel)

    return authenticator
