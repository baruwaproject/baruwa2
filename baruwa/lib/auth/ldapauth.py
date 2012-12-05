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
"""Baruwa LDAP auth"""

import ldap

from zope.interface import implements
from repoze.who.utils import resolveDotted
from sqlalchemy.orm.exc import NoResultFound
from repoze.who.interfaces import IAuthenticator
from ldap.filter import escape_filter_chars, filter_format
from repoze.who.plugins.ldap.plugins import make_ldap_connection

from baruwa.lib.auth import check_param, check_failed_logins


# def build_search_filters(kwds, search_scope,
#                         searchfilter, domain,
#                         login, username):
#     "Build LDAP filter"
#     kwds['search_scope'] = search_scope
#     if searchfilter != '':
#         params = []
#         domaindn = ','.join(['dc=' + part
#                             for part in domain.split('.')])
#         mapping = {
#                     '%n':login,
#                     '%u':username,
#                     '%d':domain,
#                     '%D': domaindn
#                     }
#         searchfilter = escape_filter_chars(searchfilter)
#         for key in ['%n', '%u', '%d', '%D']:
#             for run in searchfilter.count(key):
#                 searchfilter = searchfilter.replace(key, '%s', 1)
#                 params.append(mapping[run])
#         searchfilter = filter_format(searchfilter, params)
#         kwds['filterstr'] = searchfilter

def make_ldap_uri(addr, portno):
    "Return LDAP URI"
    nport = ''
    if (portno and portno != 636 and portno != 389):
        nport = ":%s" % str(portno)

    scheme = 'ldaps://' if portno == 636 else 'ldap://'
    ldapdict = dict(address=addr, port=nport, scheme=scheme,)
    return "%(scheme)s%(address)s%(port)s" % ldapdict


class BaruwaLDAPAuthPlugin(object):
    """Baruwa LDAP auth plugin
    Hooks into repoze.who.plugin.ldap
    """
    implements(IAuthenticator)
    name = 'ldap'

    def __init__(self, dbsession, lsm, asm, dommodel, dam,
        returned_id='login'):
        "init"
        self.dbsession = dbsession
        self.lsm = lsm
        self.asm = asm
        self.dommodel = dommodel
        self.dam = dam
        self.naming_attribute = 'uid'
        self.returned_id = returned_id

    def __repr__(self):
        "Repr"
        return '<%s %s>' % (self.__class__.__name__, id(self))

    def authenticate(self, environ, identity):
        "Authenticate identity"
        try:
            if check_failed_logins(environ):
                raise TypeError

            login = identity['login']
            username, domain = login.split('@')

            try:
                dma = self.dbsession.query(self.dommodel.name)\
                        .join(self.dam)\
                        .filter(self.dam.name == domain).one()
                domain = dma.name
            except NoResultFound:
                pass

            ldapsettings = self.dbsession.query(self.lsm,
                            self.asm.address,
                            self.asm.port,
                            self.asm.split_address)\
                            .join(self.asm)\
                            .join(self.dommodel)\
                            .filter(self.asm.enabled == True)\
                            .filter(self.dommodel.status == True)\
                            .filter(self.dommodel.name == domain)\
                            .one()
            settings, address, port, split_address = ldapsettings

            ldap.set_option(ldap.OPT_NETWORK_TIMEOUT, 5)
            ldap_uri = make_ldap_uri(address, port)
            ldap_connection = make_ldap_connection(ldap_uri)

            kwargs = dict(naming_attribute=settings.nameattribute,
                        returned_id=self.returned_id,
                        bind_dn=settings.binddn,
                        bind_pass=settings.bindpw,
                        start_tls=settings.usetls)

            # if domain != domain_name:
            #     # override alias domain
            #     domain = domain_name

            if settings.usesearch:
                ldap_module = 'LDAPSearchAuthenticatorPlugin'
                # build_search_filters(kwargs, settings.search_scope,
                #                     settings.searchfilter, domain,
                #                     login, username)
                kwargs['search_scope'] = settings.search_scope
                if settings.searchfilter != '':
                    params = []
                    domaindn = ','.join(['dc=' + part
                                        for part in domain.split('.')])
                    mapping = {
                                '%n':login,
                                '%u':username,
                                '%d':domain,
                                '%D': domaindn
                                }
                    searchfilter = escape_filter_chars(settings.searchfilter)
                    for key in ['%n', '%u', '%d', '%D']:
                        for _ in xrange(searchfilter.count(key)):
                            searchfilter = searchfilter.replace(key, '%s', 1)
                            params.append(mapping[key])
                    searchfilter = filter_format(searchfilter, params)
                    kwargs['filterstr'] = searchfilter
            else:
                ldap_module = 'LDAPAuthenticatorPlugin'

            if split_address:
                identity['login'] = username
            else:
                # use main domain name not alias reset above
                identity['login'] = "%s@%s" % (username, domain)

            auth = resolveDotted('repoze.who.plugins.ldap:%s' % ldap_module)
            ldap_auth = auth(ldap_connection, settings.basedn, **kwargs)
            userid = ldap_auth.authenticate(environ, identity)
            fulladdr = "%s@%s" % (username, domain)
            return userid if userid is None or '@' in userid else fulladdr
        except (KeyError, TypeError, ValueError, AttributeError,
                NoResultFound, IndexError, ldap.LDAPError):
            return None


def make_ldap_authenticator(dbsession, lsm, asm, dommodel, dam):
    "return ldap authenticator"
    for param in [('dbsession', dbsession),
                ('lsm', lsm),
                ('asm', asm),
                ('dommodel', dommodel),
                ('dam', dam)]:
        check_param(param[0], param[1])
    session = resolveDotted(dbsession)
    ldapmodel = resolveDotted(lsm)
    authmodel = resolveDotted(asm)
    dmodel = resolveDotted(dommodel)
    damodel = resolveDotted(dam)

    authenticator = BaruwaLDAPAuthPlugin(session,
                                        ldapmodel,
                                        authmodel,
                                        dmodel,
                                        damodel)

    return authenticator
