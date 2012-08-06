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

"Baruwa LDAP functions"

import ldap

from base64 import b64decode
from repoze.who.plugins.ldap.plugins import make_ldap_connection

from baruwa.lib.regex import USER_DN_RE


def get_user_dn(userdata):
    "Get a users DN"
    udn = ''
    match = USER_DN_RE.match(userdata)
    if match:
        udn = b64decode(match.group('b64dn'))

    return udn


class LDAPAttributes(dict):
    "Get LDAP attributes"

    def __init__(self, ldap_connection, base_dn, attributes=None,
                 searchfilter='(objectClass=*)', start_tls=None,
                 bind_dn='', bind_pass=''):
        "init"
        dict.__init__(self)
        if hasattr(attributes, 'split'):
            attributes = attributes.split(',')
        elif hasattr(attributes, '__iter__'):
            attributes = list(attributes)
        elif attributes is not None:
            raise ValueError('The needed LDAP attributes are not valid')
        self.conn = make_ldap_connection(ldap_connection)
        if start_tls:
            try:
                self.conn.start_tls_s()
            except:
                raise ValueError('Cannot upgrade the connection')

        self.bind_dn   = bind_dn
        self.bind_pass = bind_pass
        self.base_dn = base_dn
        self.attributes = attributes
        self.searchfilter = searchfilter

    def __call__(self):
        "Call"
        if self.bind_dn:
            self.conn.bind_s(self.bind_dn, self.bind_pass)

        attributes = self.conn.search_s(self.base_dn,
                                    ldap.SCOPE_BASE,
                                    self.searchfilter,
                                    self.attributes)
        self.update(attributes[0][1])
