# -*- coding: utf-8 -*-
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
"""Repoze predicates
"""

from repoze.what.predicates import Predicate
from pylons.i18n.translation import _
from pylons.controllers.util import abort
from sqlalchemy.orm.exc import NoResultFound

from baruwa.model.meta import Session
from baruwa.model.accounts import User, domain_owners
from baruwa.model.settings import DomSignature, UserSignature
from baruwa.model.accounts import organizations_admins, Address
from baruwa.model.domains import Domain, DeliveryServer, AuthServer


class OnlySuperUsers(Predicate):
    """Check if is super user"""
    message = _('Only System Administrators can access this page')

    def evaluate(self, environ, credentials):
        "Evaluate"
        identity = environ.get('repoze.who.identity')
        user = identity['user']
        if not user.is_superadmin:
            self.unmet()


class OnlyAdminUsers(Predicate):
    """Check if is admin user"""
    message = _('Only Administrators can access this page')

    def evaluate(self, environ, credentials):
        identity = environ.get('repoze.who.identity')
        user = identity['user']
        if not user.is_admin:
            self.unmet()

def check_domain_ownership(user_id, domain_id):
    "Check domain ownership"
    domain = Session.query(Domain.name)\
            .join(domain_owners, (organizations_admins,
            domain_owners.c.organization_id == \
            organizations_admins.c.organization_id))\
            .filter(organizations_admins.c.user_id == user_id)\
            .filter(domain_owners.c.domain_id == domain_id).all()
    if domain:
        return True
    return False


class OwnsDomain(Predicate):
    """Check if owns domain"""
    message = _('Only Administrators or owners can view domain details')

    def evaluate(self, environ, credentials):
        "Evaluate"
        identity = environ.get('repoze.who.identity')
        user = identity['user']
        if not user.is_superadmin:
            try:
                varbs = self.parse_variables(environ)
                if 'domainid' in varbs['named_args']:
                    domainid = varbs['named_args'].get('domainid')
                if 'destinationid' in varbs['named_args']:
                    destinationid = varbs['named_args'].get('destinationid')
                    dest = Session.query(DeliveryServer.domain_id)\
                                .filter(DeliveryServer.id == destinationid)\
                                .one()
                    domainid = dest.domain_id
                if 'authid' in varbs['named_args']:
                    authid = varbs['named_args'].get('authid')
                    authsvr = Session.query(AuthServer.domain_id)\
                                .filter(AuthServer.id == authid).one()
                    domainid = authsvr.domain_id
                if 'sigid' in varbs['named_args']:
                    sigid = varbs['named_args'].get('sigid')
                    sig = Session.query(DomSignature.domain_id)\
                            .filter(DomSignature.id == sigid).one()
                    domainid = sig.domain_id
                if not check_domain_ownership(user.id, domainid):
                    self.unmet()
            except NoResultFound:
                self.unmet()


class CanAccessAccount(Predicate):
    """Check if can access account"""
    message = _('Only Administrators or owners can view account details')

    def evaluate(self, environ, credentials):
        "Evaluate"
        identity = environ.get('repoze.who.identity')
        user = identity['user']
        if not user.is_superadmin:
            try:
                varbs = self.parse_variables(environ)
                accountid = varbs['named_args'].get('userid')
                if accountid is None and varbs['named_args'].get('addressid'):
                    addressid = varbs['named_args'].get('addressid')
                    acct = Session.query(Address.user_id)\
                            .filter(Address.id == addressid).one()
                    accountid = acct.user_id
                if accountid is None and varbs['named_args'].get('sigid'):
                    sigid = varbs['named_args'].get('sigid')
                    sig = Session.query(UserSignature.user_id)\
                        .filter(UserSignature.id == sigid).one()
                    accountid = sig.user_id
                if accountid is None:
                    self.unmet()
                requested_account = Session.query(User).get(accountid)
                if not requested_account:
                    abort(404)
                    self.unmet()
                if requested_account.is_superadmin:
                    self.unmet()
                if user.is_peleb:
                    if requested_account.id != user.id:
                        self.unmet()
                if user.is_domain_admin:
                    if accountid and user.id == int(accountid):
                        return
                    orgs = [org.id for org in user.organizations]
                    if not orgs:
                        self.unmet()
                    doms = Session.query(Domain.name)\
                            .join(domain_owners)\
                            .filter(domain_owners.c.organization_id.in_(orgs))\
                            .all()
                    domains = [dom.name for dom in doms]
                    if not domains:
                        self.unmet()
                    addrs = [requested_account.email.split('@')[1]]
                    if '@' in requested_account.username:
                        addrs.append(requested_account.username.split('@')[1])
                    [addrs.append(addr.address.split('@')[1])
                    for addr in requested_account.addresses]
                    for addr in addrs:
                        if addr in domains:
                            return
                    self.unmet()
            except NoResultFound:
                self.unmet()


def check_dom_access(orgs, udomains):
    "Check if an org owns the domains"
    doms = Session.query(Domain.id).join(domain_owners)\
         .filter(domain_owners.c.organization_id.in_(orgs)).all()
    domains = [dom.id for dom in doms]
    dset = set(domains)
    uset = set(udomains)
    return dset.intersection(uset)
