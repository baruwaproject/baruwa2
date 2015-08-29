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
# pylint: disable-msg=C0302
"API Helper functions"
import os
import arrow

from copy import deepcopy

from sqlalchemy import func, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.expression import true
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import joinedload, joinedload_all

from baruwa.model.lists import List
from baruwa.model.meta import Session
from baruwa.lib.audit import audit_log
from baruwa.lib.net import system_hostname
from baruwa.lib.auth.ldapauth import make_ldap_uri
from baruwa.lib.regex import PROXY_ADDR_RE, RENAME_RE
from baruwa.model.auth import LDAPSettings, RadiusSettings
from baruwa.lib.directory import LDAPAttributes, get_user_dn
from baruwa.lib.audit.msgs import accounts as acc_auditmsgs
from baruwa.lib.audit.msgs import domains as dom_auditmsgs
from baruwa.model.domains import Domain, AuthServer, DeliveryServer, \
    DomainAlias
from baruwa.forms.domains import EditDomainForm
from baruwa.forms.organizations import OrgForm, DelOrgForm
from baruwa.forms.accounts import AddUserForm, EditUserForm
from baruwa.model.settings import Policy, Rule, PolicySettings, \
    DomainPolicy, MTASettings, Server
from baruwa.model.messages import Message, Archive, Release, SARule
from baruwa.model.accounts import domain_owners as dom_owns
from baruwa.model.accounts import organizations_admins as oas
from baruwa.lib.audit.msgs import organizations as org_auditmsgs
from baruwa.lib.audit.msgs import settings as settings_auditmsgs
from baruwa.lib.backend import (backend_user_update, update_domain_backend,
    update_relay_backend, update_destination_backend, update_auth_backend,
    get_ruleset_data, backend_create_content_rules,
    backend_create_content_ruleset, backend_create_mta_settings,
    backend_create_local_scores)
from baruwa.model.accounts import User, Address, Group, Relay, domain_users
from baruwa.lib import POLICY_URL_MAP, POLICY_FILE_MAP, POLICY_SETTINGS_MAP


def pager_filter(qry, count_qry, domainid, user):
    """Filter domain based query"""
    qry = qry\
            .filter(dom_owns.c.organization_id == oas.c.organization_id)\
            .filter(oas.c.user_id == user.id)\
            .filter(dom_owns.c.domain_id == domainid)
    count_qry = count_qry\
            .filter(dom_owns.c.organization_id == oas.c.organization_id)\
            .filter(oas.c.user_id == user.id)\
            .filter(dom_owns.c.domain_id == domainid)
    return qry, count_qry


def update_login(model):
    """Update last_login on API Client"""
    model.last_login = arrow.utcnow().datetime
    Session.add(model)
    Session.commit()


def change_user_pw(user, apiuser, password, host, remote_addr):
    """Change users password"""
    user.set_password(password)
    Session.add(user)
    Session.commit()
    info = acc_auditmsgs.PASSWORDCHANGE_MSG % dict(u=user.username)
    audit_log(apiuser.username, 2, unicode(info), host, remote_addr,
                arrow.utcnow().datetime)


def add_user(userid):
    """Add a user to the DB"""
    user = User(username=userid, email=userid)
    user.active = True
    local_part, domain = userid.split('@')
    domains = Session.query(Domain)\
            .filter(Domain.name == domain)\
            .all()
    user.domains = domains
    user.timezone = domains[0].timezone
    Session.add(user)
    Session.commit()
    return user, local_part, domain, domains


# pylint: disable-msg=R0912,R0914,R0915
def user_address_update(user, local_part, domain, domains, identity):
    """Update users assoc addrs"""
    addresses = []
    if ('tokens' in identity and 'ldap' in identity['tokens']):
        lsettings = Session.query(AuthServer.address,
                        AuthServer.port, LDAPSettings.binddn,
                        LDAPSettings.bindpw,
                        LDAPSettings.usetls)\
                        .join(LDAPSettings)\
                        .join(Domain)\
                        .filter(AuthServer.enabled == true())\
                        .filter(Domain.name == domain)\
                        .all()
        lsettings = lsettings[0]
        lurl = make_ldap_uri(lsettings.address, lsettings.port)
        base_dn = get_user_dn(identity['tokens'][1])
        attributes = ['sn', 'givenName', 'proxyAddresses', 'mail',
                    'memberOf']
        ldapattributes = LDAPAttributes(
                                    lurl,
                                    base_dn,
                                    attributes=attributes,
                                    bind_dn=lsettings.binddn,
                                    bind_pass=lsettings.bindpw,
                                    start_tls=lsettings.usetls)
        ldapattributes()
        attrmap = {
                    'sn': 'lastname',
                    'givenName': 'firstname',
                    'mail': 'email'}

        update_attrs = False

        doms = [domains[0].name]
        doms.extend([alias.name for alias in domains[0].aliases])

        for attr in attrmap:
            if attr == 'mail':
                for mailattr in ldapattributes[attr]:
                    mailattr = mailattr.lower()
                    if (mailattr != user.email and
                        '@' in mailattr and
                        mailattr.split('@')[1] in doms):
                        address = Address(mailattr)
                        address.user = user
                        addresses.append(address)
                continue
            if attr in ldapattributes:
                setattr(user,
                        attrmap[attr],
                        ldapattributes[attr][0])
                update_attrs = True

        if update_attrs:
            Session.add(user)
            Session.commit()

        # accounts aliases
        if 'proxyAddresses' in ldapattributes:
            for mailaddr in ldapattributes['proxyAddresses']:
                try:
                    if mailaddr.startswith('SMTP:'):
                        continue
                    clean_addr = PROXY_ADDR_RE.sub('', mailaddr)
                    clean_addr = clean_addr.lower()
                    if (mailaddr.startswith('smtp:') and
                        clean_addr.split('@')[1] in doms):
                        # Only add domain if we host it
                        address = Address(clean_addr)
                        address.user = user
                        addresses.append(address)
                except IndexError:
                    pass
        # accounts groups
        if 'memberOf' in ldapattributes:
            for group_dn in ldapattributes['memberOf']:
                groupattributes = LDAPAttributes(
                                    lurl,
                                    group_dn,
                                    attributes=['proxyAddresses'],
                                    bind_dn=lsettings.binddn,
                                    bind_pass=lsettings.bindpw,
                                    start_tls=lsettings.usetls)
                groupattributes()
                if 'proxyAddresses' not in groupattributes:
                    continue
                for mailaddr in groupattributes['proxyAddresses']:
                    try:
                        mailaddr = mailaddr.lower()
                        clean_addr = PROXY_ADDR_RE.sub('', mailaddr)
                        if (mailaddr.startswith('smtp:') and
                            clean_addr.split('@')[1] in doms):
                            address = Address(clean_addr)
                            address.user = user
                            addresses.append(address)
                    except IndexError:
                        pass
    else:
        for alias in domains[0].aliases:
            address = Address('%s@%s' % (local_part, alias.name))
            address.user = user
            addresses.append(address)
    for unsaved in addresses:
        try:
            Session.add(unsaved)
            Session.commit()
        except IntegrityError:
            Session.rollback()


def set_policy_form_opts(form):
    """Set PolicySettingsForm options"""
    def setup_opts(policy_type):
        """set opts"""
        policies = get_policies(policy_type, True)
        data = [('0', 'Use Default')]
        pdata = [(str(policy.id), policy.name) for policy in policies]
        return data + pdata
    form.archive_filename.choices = setup_opts(1)
    form.archive_filetype.choices = setup_opts(2)
    form.filename.choices = setup_opts(3)
    form.filetype.choices = setup_opts(4)


def save_policy_settings(form, settings, current_user, host, remote_addr):
    """Create or update policy settings"""
    if not settings:
        settings = PolicySettings()
    for field in form:
        if field.name in ['csrf_token']:
            continue
        setattr(settings, field.name, field.data)
    Session.add(settings)
    Session.commit()
    backend_create_content_ruleset()
    info = settings_auditmsgs.POLICYSETTINGS_MSG
    audit_log(current_user.username, 2, unicode(info), host,
            remote_addr, arrow.utcnow().datetime)


# pylint: disable-msg=R0913
def save_domain_policy_settings(form, settings, domain_id, current_user,
                                host, remote_addr):
    """Create or update Domain policy settings"""
    if not settings:
        settings = DomainPolicy()
    for field in form:
        if field.name in ['csrf_token']:
            continue
        setattr(settings, field.name, field.data)
    settings.domain_id = domain_id
    Session.add(settings)
    Session.commit()
    backend_create_content_ruleset()
    info = settings_auditmsgs.DOMPOLICYSETTINGS_MSG
    audit_log(current_user.username, 2, unicode(info), host,
            remote_addr, arrow.utcnow().datetime)


def disable_domain_policies(policy_type, policy_id):
    """Get domain policy settings by type"""
    policies = Session.query(DomainPolicy)\
                    .filter(getattr(DomainPolicy, policy_type) == policy_id)
    for policy in policies:
        setattr(policy, policy_type, 0)
        Session.add(policy)
        Session.commit()


def get_listitem(itemid):
    "Get a list item"
    try:
        item = Session.query(List).get(itemid)
    except NoResultFound:
        item = None
    return item


def get_address(addressid, user=None):
    "return address"
    try:
        qry = Session.query(Address).filter(Address.id == addressid)
        if user and not user.is_superadmin:
            qry = qry\
                    .filter(Address.user_id == domain_users.c.user_id)\
                    .filter(domain_users.c.domain_id == dom_owns.c.domain_id)\
                    .filter(dom_owns.c.organization_id ==
                        oas.c.organization_id)\
                    .filter(oas.c.user_id == user.id)
        address = qry.one()
    except NoResultFound:
        address = None
    return address


def get_organizations(orgid=None):
    "return organization or all organizations query"
    query = Session.query(Group)
    if orgid:
        query = query.filter(Group.id == orgid)
    return query


def get_org(orgid):
    "Get organization"
    try:
        org = Session.query(Group).options(joinedload('domains')).get(orgid)
    except NoResultFound:
        org = None
    return org


def get_domain(domainid, user):
    """Get a domain based on user"""
    try:
        qry = Session.query(Domain)\
                    .filter(Domain.id == domainid)\
                    .options(joinedload_all(Domain.servers),
                            joinedload_all(Domain.aliases),
                            joinedload_all(Domain.authservers))
        if not user.is_superadmin:
            qry = qry.join(dom_owns, (oas, dom_owns.c.organization_id ==
                            oas.c.organization_id))\
                    .filter(dom_owns.c.organization_id ==
                        oas.c.organization_id)\
                    .filter(oas.c.user_id == user.id)\
                    .filter(dom_owns.c.domain_id == domainid)
        domain = qry.one()
    except NoResultFound:
        domain = None
    return domain


def get_domain_alias(aliasid, domainid, user):
    """Get a domain alias based on domain and user"""
    try:
        qry = Session.query(DomainAlias)\
                    .filter(DomainAlias.id == aliasid)\
                    .filter(DomainAlias.domain_id == domainid)
        if not user.is_superadmin:
            qry = qry\
                    .filter(dom_owns.c.organization_id ==
                        oas.c.organization_id)\
                    .filter(oas.c.user_id == user.id)\
                    .filter(dom_owns.c.domain_id == domainid)
        alias = qry.one()
    except NoResultFound:
        alias = None
    return alias


def get_domain_aliases(domainid, user):
    """Get a domains aliases"""
    qry = Session.query(DomainAlias)\
                .filter(DomainAlias.domain_id == domainid)
    count_qry = Session.query(DomainAlias.id)\
                .filter(DomainAlias.domain_id == domainid)
    if not user.is_superadmin:
        qry, count_qry = pager_filter(qry, count_qry, domainid, user)
    return qry, count_qry


def get_delivery_server(domainid, serverid, user):
    """Get a delivery server"""
    try:
        qry = Session.query(DeliveryServer)\
                    .filter(DeliveryServer.domain_id == domainid)\
                    .filter(DeliveryServer.id == serverid)
        if not user.is_superadmin:
            qry = qry\
                    .filter(dom_owns.c.organization_id ==
                        oas.c.organization_id)\
                    .filter(oas.c.user_id == user.id)\
                    .filter(dom_owns.c.domain_id == domainid)
        server = qry.one()
    except NoResultFound:
        server = None
    return server


def get_delivery_servers(domainid, user):
    """Get delivery servers queries for paginate"""
    qry = Session.query(DeliveryServer)\
                .filter(DeliveryServer.domain_id == domainid)
    count_qry = Session.query(DeliveryServer)\
                .filter(DeliveryServer.domain_id == domainid)
    if not user.is_superadmin:
        qry, count_qry = pager_filter(qry, count_qry, domainid, user)
    return qry, count_qry


def get_authserver(domainid, serverid, user):
    """Get an authentication server based on domain and user"""
    try:
        qry = Session.query(AuthServer)\
                    .filter(AuthServer.domain_id == domainid)\
                    .filter(AuthServer.id == serverid)
        if not user.is_superadmin:
            qry = qry\
                    .filter(dom_owns.c.organization_id ==
                        oas.c.organization_id)\
                    .filter(oas.c.user_id == user.id)\
                    .filter(dom_owns.c.domain_id == domainid)
        server = qry.one()
    except NoResultFound:
        server = None
    return server


def get_authservers(domainid, user):
    """Get auth servers pager queries"""
    qry = Session.query(AuthServer)\
                .filter(AuthServer.domain_id == domainid)
    count_qry = Session.query(AuthServer)\
                .filter(AuthServer.domain_id == domainid)
    if not user.is_superadmin:
        qry, count_qry = pager_filter(qry, count_qry, domainid, user)
    return qry, count_qry


def get_ldap_settings(domainid, authid, settingsid, user):
    """Get LDAP settings based on domain, auth server and user"""
    try:
        qry = Session.query(LDAPSettings)\
                    .filter(LDAPSettings.id == settingsid)\
                    .filter(LDAPSettings.auth_id == authid)\
                    .filter(AuthServer.domain_id == domainid)\
                    .filter(AuthServer.id == authid)
        if not user.is_superadmin:
            qry = qry\
                    .filter(dom_owns.c.organization_id ==
                        oas.c.organization_id)\
                    .filter(oas.c.user_id == user.id)\
                    .filter(dom_owns.c.domain_id == domainid)
        settings = qry.one()
    except NoResultFound:
        settings = None
    return settings


def get_radius_settings(domainid, authid, settingsid, user):
    """Get Radius settins based on domain, auth server and user"""
    try:
        qry = Session.query(RadiusSettings)\
                    .filter(RadiusSettings.id == settingsid)\
                    .filter(RadiusSettings.auth_id == authid)\
                    .filter(AuthServer.domain_id == domainid)\
                    .filter(AuthServer.id == authid)
        if not user.is_superadmin:
            qry = qry\
                    .filter(dom_owns.c.organization_id ==
                        oas.c.organization_id)\
                    .filter(oas.c.user_id == user.id)\
                    .filter(dom_owns.c.domain_id == domainid)
        settings = qry.one()
    except NoResultFound:
        settings = None
    return settings


def get_relay(relay_id):
    "Get relay settings"
    try:
        setting = Session.query(Relay)\
                        .options(joinedload('org'))\
                        .get(relay_id)
    except NoResultFound:
        setting = None
    return setting


def get_user(userid, user):
    """Get a user based on the requester"""
    try:
        if user.id == userid:
            return user
        qry = Session.query(User).filter(User.id == userid)\
                .options(joinedload('addresses'))
        if not user.is_superadmin:
            qry = qry.join(domain_users,
                            (dom_owns, domain_users.c.domain_id ==
                                        dom_owns.c.domain_id),
                            (oas, dom_owns.c.organization_id ==
                                        oas.c.organization_id))\
                    .filter(oas.c.user_id == user.id)
        user = qry.one()
    except NoResultFound:
        user = None
    return user


def get_messages():
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


def get_messagez():
    "Return message query object"
    return Session.query(Message)


def get_msg_count(archived=None):
    "return message query for count"
    if archived:
        return Session.query(Archive.id)
    else:
        return Session.query(Message.id)


def get_archived():
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


def get_releasereq(uuid):
    "return a release request object"
    try:
        msg = Session.query(Release).filter(Release.uuid == uuid)\
                    .one()
    except NoResultFound:
        msg = None
    return msg


def get_policy_setting():
    """Get the global policy settings"""
    try:
        settings = Session.query(PolicySettings).get(1)
    except NoResultFound:
        settings = None
    return settings


def get_domain_policy_settings(domain_id):
    """Get domain policy setting"""
    try:
        settings = Session.query(DomainPolicy)\
                        .filter(DomainPolicy.domain_id == domain_id)\
                        .one()
    except NoResultFound:
        settings = None
    return settings


def get_policy(policy_id):
    """Get a Policy object"""
    try:
        policy = Session.query(Policy).get(policy_id)
    except NoResultFound:
        policy = None
    return policy


def get_policies(policy_type, only_enabled=None):
    """Get Policies"""
    if only_enabled:
        return Session.query(Policy)\
                            .filter(Policy.policy_type == policy_type)\
                            .filter(Policy.enabled == true())\
                            .order_by(desc('id'))
    else:
        return Session.query(Policy)\
                            .filter(Policy.policy_type == policy_type)\
                            .order_by(desc('id'))


def get_policy_rules(policy_id, only_enabled=None):
    """Get a policies rules"""
    if only_enabled:
        return Session.query(Rule)\
                        .filter(Rule.policy_id == policy_id)\
                        .filter(Rule.enabled == true())\
                        .order_by(desc('ordering'))\
                        .all()
    else:
        return Session.query(Rule)\
                    .filter(Rule.policy_id == policy_id)\
                    .order_by(desc('ordering'))\
                    .all()


def get_rule(rule_id):
    """Get a rule object"""
    try:
        rule = Session.query(Rule).get(rule_id)
    except NoResultFound:
        rule = None
    return rule


def get_mta_settings(settings_type):
    """Get MTA Settings"""
    return Session.query(MTASettings)\
                        .filter(MTASettings.address_type == settings_type)


def get_mta_setting(setting_id):
    """Get MTA Setting"""
    try:
        setting = Session.query(MTASettings).get(setting_id)
    except NoResultFound:
        setting = None
    return setting


def get_local_scores(filtered=None):
    """Get Local scores"""
    if filtered:
        return Session.query(SARule)\
                .filter(SARule.local_score != 0)\
                .filter(SARule.local_score != SARule.score)\
                .order_by(SARule.id)
    else:
        return Session.query(SARule).order_by(SARule.id)


def get_local_score(score_id):
    """Get a local score"""
    try:
        score = Session.query(SARule).get(score_id)
    except NoResultFound:
        score = None
    return score


def update_changed(form, fields, obj):
    "Update object if has been changed"
    update = False
    for attr in fields:
        field = getattr(form, attr)
        if field and field.data != getattr(obj, attr):
            setattr(obj, attr, field.data)
            update = True
    return update


def update_if_changed(form, obj):
    "Update an objected based on a form"
    updated = False
    for field in form:
        if field.name == 'csrf_token':
            continue
        if field.data != getattr(obj, field.name):
            setattr(obj, field.name, field.data)
            updated = True
    return updated


def domain_update_if_changed(form, obj):
    "Update domain if changed"
    updated = False
    for field in form:
        if field.name == 'csrf_token':
            continue
        intfields = ['spam_actions', 'highspam_actions',
                    'delivery_mode', 'report_every',
                    'virus_actions']
        if (field.name in intfields and
            int(field.data) == getattr(obj, field.name)):
            continue
        if field.data != getattr(obj, field.name):
            if field.name == 'name':
                try:
                    from baruwa.tasks.invite import delete_mx_records
                    from baruwa.tasks.invite import create_mx_records
                    delete_mx_records.apply_async(args=[obj.name])
                    create_mx_records.apply_async(args=[field.name])
                except ImportError:
                    pass
            setattr(obj, field.name, field.data)
            updated = True
    return updated


def auth_update_if_changed(form, obj):
    "Update auth if changed"
    updated = False
    for field in form:
        if field.name == 'protocol' or field.name == 'csrf_token':
            continue
        if (field.data != getattr(obj, field.name) and field.data != ''):
            setattr(obj, field.name, field.data)
            updated = True
        if (field.name == 'user_map_template' and
            field.data != getattr(obj, field.name)):
            setattr(obj, field.name, field.data)
            updated = True
    return updated


def relay_update_if_changed(form, relay):
    """Update if changed"""
    updated = False
    for field in form:
        if field.name == 'csrf_token':
            continue
        if (field.name not in ['password1', 'password2'] and
            field.data != getattr(relay, field.name)):
            setattr(relay, field.name, field.data)
            updated = True
        if field.name == 'password1' and field.data != '':
            relay.set_password(field.data)
            updated = True
    return updated


def token_update_if_changed(field, obj):
    """Update if changed"""
    if field.data != unicode(obj.scopes).strip('{}').split(','):
        set1 = set(field.data)
        set2 = set(obj.client.scopes.strip('{}').split(','))
        if set1.issubset(set2):
            return True
    return False


def apiclient_update_if_changed(form, obj):
    """Update if changed"""
    updated = False
    for field in form:
        if field.name == 'csrf_token':
            continue
        if field.name == 'scopes':
            if field.data != unicode(obj.scopes).strip('{}').split(','):
                setattr(obj, field.name, field.data)
                updated = True
            continue
        if field.data != getattr(obj, field.name):
            setattr(obj, field.name, field.data)
            updated = True
    return updated


def ldap_update_if_changed(form, obj):
    """Update if changed"""
    updated = False
    for field in form:
        if field.name == 'csrf_token':
            continue
        if field.name == 'bindpw' and field.data == '':
            continue
        if getattr(obj, field.name) != field.data:
            if field.name == 'bindpw' and field.data == 'None':
                setattr(obj, field.name, '')
            else:
                setattr(obj, field.name, field.data)
            updated = True
    return updated


def user_add_form(user, post_data, session):
    "Create user add form"
    form = AddUserForm(post_data, csrf_context=session)
    if user.is_domain_admin:
        account_types = (('3', 'User'),)
        form.account_type.choices = account_types
        form.domains.query = Session.query(Domain).join(dom_owns,
                                (oas, dom_owns.c.organization_id ==
                                oas.c.organization_id))\
                                .filter(oas.c.user_id == user.id)
    else:
        form.domains.query = Session.query(Domain)
    return form


def user_update_form(user, current_user, post_data, session):
    "Update a user account"
    form = EditUserForm(post_data, user, csrf_context=session)
    form.domains.query = Session.query(Domain)
    if current_user.is_domain_admin:
        form.domains.query = Session.query(Domain).join(dom_owns,
                                (oas, dom_owns.c.organization_id ==
                                oas.c.organization_id))\
                                .filter(oas.c.user_id == current_user.id)

    if user.account_type != 3 or current_user.is_peleb:
        del form.domains
    if current_user.is_peleb:
        del form.username
        del form.email
        del form.active
    return form


def domain_update_form(current_user, post_data, domain, qry, session):
    "Create domain update form"
    form = EditDomainForm(post_data, domain, csrf_context=session)
    if current_user.is_superadmin:
        form.organizations.query_factory = qry
    else:
        del form.organizations
    return form


def org_add_form(post_data, session, obj=None):
    """Add an organization"""
    if obj:
        form = OrgForm(post_data, obj, csrf_context=session)
    else:
        form = OrgForm(post_data, csrf_context=session)
    form.domains.query = Session.query(Domain)
    form.admins.query = Session.query(User)\
                                .filter(User.account_type == 2)
    return form


def org_delete_form(post_data, session, org):
    """Delete org"""
    form = DelOrgForm(post_data, org, csrf_context=session)
    form.domains.query = Session.query(Domain)
    form.admins.query = Session.query(User)\
                                .filter(User.account_type == 2)
    return form


def create_user(form, current_user, host, remote_addr):
    "Create user account"
    user = User(username=form.username.data,
            email=form.email.data)
    for attr in ['firstname', 'lastname', 'email', 'active',
        'account_type', 'send_report', 'spam_checks',
        'low_score', 'high_score', 'timezone']:
        setattr(user, attr, getattr(form, attr).data)
    user.local = True
    user.set_password(form.password1.data)
    if int(user.account_type) == 3:
        user.domains = form.domains.data
    Session.add(user)
    Session.commit()
    backend_user_update(user)
    info = acc_auditmsgs.ADDACCOUNT_MSG % dict(u=user.username)
    audit_log(current_user, 3, unicode(info), host,
            remote_addr, arrow.utcnow().datetime)
    return user


def update_user(user, current_user, host, remote_addr):
    "Update user account"
    Session.add(user)
    Session.commit()
    backend_user_update(user)
    info = acc_auditmsgs.UPDATEACCOUNT_MSG % dict(u=user.username)
    audit_log(current_user.username, 2, unicode(info), host,
            remote_addr, arrow.utcnow().datetime)


def delete_user(user, current_user, host, remote_addr):
    "Delete user account"
    temp = deepcopy(user)
    Session.delete(user)
    Session.commit()
    backend_user_update(temp)
    info = acc_auditmsgs.DELETEACCOUNT_MSG % dict(u=temp.username)
    audit_log(current_user.username, 4, unicode(info), host,
            remote_addr, arrow.utcnow().datetime)


def create_address(form, user, current_user, host, remote_addr):
    "Create and Address"
    if current_user.is_domain_admin:
        # check if they own the domain
        domain = form.address.data.split('@')[1]
        try:
            Session.query(Domain.name).join(
                    dom_owns, (oas,
                    dom_owns.c.organization_id ==
                    oas.c.organization_id))\
                    .filter(oas.c.user_id == current_user.id)\
                    .filter(Domain.name == domain).one()
        except NoResultFound:
            Session.query(DomainAlias.name).join(Domain).join(
                    dom_owns, (oas,
                    dom_owns.c.organization_id ==
                    oas.c.organization_id))\
                    .filter(oas.c.user_id == current_user.id)\
                    .filter(DomainAlias.name == domain).one()
    addr = Address(address=form.address.data)
    addr.enabled = form.enabled.data
    addr.user = user
    Session.add(addr)
    Session.commit()
    backend_user_update(user)
    info = acc_auditmsgs.ADDRADD_MSG % dict(a=addr.address,
                                        ac=user.username)
    audit_log(current_user.username, 3, unicode(info), host,
            remote_addr, arrow.utcnow().datetime)
    return addr


def update_address(form, address, current_user, host, remote_addr):
    "Update an Address"
    if current_user.is_domain_admin:
        # check if they own the domain
        domain = form.address.data.split('@')[1]
        try:
            Session.query(Domain.name).join(
                    dom_owns, (oas,
                    dom_owns.c.organization_id ==
                    oas.c.organization_id))\
                    .filter(oas.c.user_id == current_user.id)\
                    .filter(Domain.name == domain).one()
        except NoResultFound:
            Session.query(DomainAlias.name).join(Domain).join(
                    dom_owns, (oas,
                    dom_owns.c.organization_id ==
                    oas.c.organization_id))\
                    .filter(oas.c.user_id == current_user.id)\
                    .filter(DomainAlias.name == domain).one()
    address.address = form.address.data
    address.enabled = form.enabled.data
    Session.add(address)
    Session.commit()
    backend_user_update(address.user)
    info = acc_auditmsgs.ADDRUPDATE_MSG % dict(a=address.address,
                                ac=address.user.username)
    audit_log(current_user.username, 2, unicode(info), host,
            remote_addr, arrow.utcnow().datetime)


def delete_address(address, current_user, host, remote_addr):
    "Delete an Address"
    addr = address.address
    user = deepcopy(address.user)
    Session.delete(address)
    Session.commit()
    backend_user_update(user)
    info = acc_auditmsgs.ADDRDELETE_MSG % dict(a=addr, ac=user.username)
    audit_log(current_user.username, 4, unicode(info), host,
          remote_addr, arrow.utcnow().datetime)
    return user.id


def create_domain(form, current_user, host, remote_addr):
    "Create a domain"
    domain = Domain()
    domain.from_form(form)
    Session.add(domain)
    Session.commit()
    update_domain_backend(domain)
    info = dom_auditmsgs.ADDDOMAIN_MSG % dict(d=domain.name)
    audit_log(current_user.username, 3, unicode(info), host,
            remote_addr, arrow.utcnow().datetime)
    return domain


def update_domain(domain, current_user, host, remote_addr):
    "Update a domain"
    Session.add(domain)
    Session.commit()
    update_domain_backend(domain, True)
    info = dom_auditmsgs.UPDATEDOMAIN_MSG % dict(d=domain.name)
    audit_log(current_user.username, 2, unicode(info), host,
            remote_addr, arrow.utcnow().datetime)


def delete_domain(domain, current_user, host, remote_addr):
    "Delete a domain"
    name = domain.name
    tdomain = deepcopy(domain)
    Session.delete(domain)
    Session.commit()
    update_domain_backend(tdomain)
    info = dom_auditmsgs.DELETEDOMAIN_MSG % dict(d=name)
    audit_log(current_user.username, 4, unicode(info), host,
            remote_addr, arrow.utcnow().datetime)
    try:
        from baruwa.tasks.invite import delete_mx_records
        delete_mx_records.apply_async(args=[name])
    except ImportError:
        pass


def create_destination(domain, server, current_user, host, remote_addr):
    """Create a destination"""
    domain.servers.append(server)
    Session.add(server)
    Session.add(domain)
    Session.commit()
    info = dom_auditmsgs.ADDDELSVR_MSG % dict(d=domain.name,
                                        ds=server.address)
    audit_log(current_user.username, 3, unicode(info), host,
            remote_addr, arrow.utcnow().datetime)
    update_destination_backend(server.protocol)


def update_destination(server, current_user, host, remote_addr):
    """Update a destination"""
    Session.add(server)
    Session.commit()
    info = (dom_auditmsgs.UPDATEDELSVR_MSG %
            dict(d=server.domains.name, ds=server.address))
    audit_log(current_user.username, 2, unicode(info), host,
            remote_addr, arrow.utcnow().datetime)
    update_destination_backend(server.protocol)


def delete_destination(server, current_user, host, remote_addr):
    """Delete a destination"""
    name = server.domains.name
    server_addr = server.address
    domainid = server.domain_id
    protocol = server.protocol
    Session.delete(server)
    Session.commit()
    info = dom_auditmsgs.DELETEDELSVR_MSG % dict(d=name, ds=server_addr)
    audit_log(current_user.username, 4, unicode(info), host,
            remote_addr, arrow.utcnow().datetime)
    update_destination_backend(protocol)
    return domainid


def create_auth(domain, server, current_user, host, remote_addr):
    """Create Auth server"""
    domain.authservers.append(server)
    Session.add(server)
    Session.add(domain)
    Session.commit()
    info = dom_auditmsgs.ADDAUTHSVR_MSG % dict(d=domain.name,
                                        ds=server.address)
    audit_log(current_user.username, 3, unicode(info), host,
            remote_addr, arrow.utcnow().datetime)
    update_auth_backend(server.protocol)


def edit_auth(server, current_user, host, remote_addr):
    """Edit auth"""
    Session.add(server)
    Session.commit()
    info = dom_auditmsgs.UPDATEAUTHSVR_MSG % dict(
                                    d=server.domains.name,
                                    ds=server.address)
    audit_log(current_user.username, 2, unicode(info), host,
            remote_addr, arrow.utcnow().datetime)
    update_auth_backend(server.protocol)


def delete_auth(server, current_user, host, remote_addr):
    """Delete auth"""
    name = server.domains.name
    server_addr = server.address
    protocol = server.protocol
    Session.delete(server)
    Session.commit()
    info = dom_auditmsgs.DELETEAUTHSVR_MSG % dict(d=name, ds=server_addr)
    audit_log(current_user.username, 4, unicode(info), host,
            remote_addr, arrow.utcnow().datetime)
    update_auth_backend(protocol)


def create_alias(domain, alias, current_user, host, remote_addr):
    """Create domain alias"""
    domain.aliases.append(alias)
    Session.add(alias)
    Session.add(domain)
    Session.commit()
    update_domain_backend(domain)
    info = dom_auditmsgs.ADDDOMALIAS_MSG % dict(d=alias.name)
    audit_log(current_user.username, 3, unicode(info), host,
            remote_addr, arrow.utcnow().datetime)


def edit_alias(alias, current_user, host, remote_addr):
    """Edit domain alias"""
    Session.add(alias)
    Session.commit()
    update_domain_backend(alias.domain)
    info = dom_auditmsgs.UPDATEDOMALIAS_MSG % dict(d=alias.name)
    audit_log(current_user.username, 2, unicode(info), host,
            remote_addr, arrow.utcnow().datetime)


def delete_alias(alias, current_user, host, remote_addr):
    """Delete domain alias"""
    domainid = alias.domain_id
    aliasname = alias.name
    tdomain = deepcopy(alias.domain)
    Session.delete(alias)
    Session.commit()
    update_domain_backend(tdomain)
    info = dom_auditmsgs.DELETEDOMALIAS_MSG % dict(d=aliasname)
    audit_log(current_user.username, 4, unicode(info), host,
            remote_addr, arrow.utcnow().datetime)
    return domainid, aliasname


def create_org(form, current_user, host, remote_addr):
    """Add an org"""
    org = Group()
    org.from_form(form)
    Session.add(org)
    Session.commit()
    info = org_auditmsgs.ADDORG_MSG % dict(o=org.name)
    audit_log(current_user.username, 3, unicode(info), host,
            remote_addr, arrow.utcnow().datetime)
    return org


def edit_org(org, current_user, host, remote_addr):
    """Edit org"""
    Session.add(org)
    Session.commit()
    info = org_auditmsgs.UPDATEORG_MSG % dict(o=org.name)
    audit_log(current_user.username, 2, unicode(info), host,
            remote_addr, arrow.utcnow().datetime)


def delete_org(form, org, current_user, host, remote_addr):
    """Delete org"""
    org_name = org.name
    if hasattr(form, 'delete_domains'):
        delete_domains = form.delete_domains.data
    else:
        delete_domains = form

    if delete_domains:
        for domain in org.domains:
            Session.delete(domain)
    Session.delete(org)
    Session.commit()
    info = org_auditmsgs.DELETEORG_MSG % dict(o=org_name)
    audit_log(current_user.username, 4, unicode(info), host,
            remote_addr, arrow.utcnow().datetime)


def add_relay(form, org, current_user, host, remote_addr):
    """Add relay"""
    outbound = Relay()
    for field in form:
        if field.name in ['csrf_token', 'password1', 'password2']:
            continue
        setattr(outbound, field.name, field.data)
    outbound.org = org
    if form.password1.data:
        outbound.set_password(form.password1.data)
    Session.add(outbound)
    Session.commit()
    update_relay_backend(outbound)
    relay_name = form.address.data or form.username.data
    info = org_auditmsgs.ADDRELAY_MSG % dict(r=relay_name)
    audit_log(current_user.username, 3, unicode(info), host,
            remote_addr, arrow.utcnow().datetime)
    return outbound


def edit_relay(relay, current_user, host, remote_addr):
    """Edit relay"""
    relayname = relay.address or relay.username
    Session.add(relay)
    Session.commit()
    update_relay_backend(relay)
    info = org_auditmsgs.UPDATERELAY_MSG % dict(r=relayname)
    audit_log(current_user.username, 2, unicode(info), host,
            remote_addr, arrow.utcnow().datetime)


def delete_relay(relay, current_user, host, remote_addr):
    """Delete relay"""
    relayname = relay.address or relay.username
    Session.delete(relay)
    Session.commit()
    update_relay_backend(None, True)
    info = org_auditmsgs.DELETERELAY_MSG % dict(r=relayname)
    audit_log(current_user.username, 4, unicode(info), host,
            remote_addr, arrow.utcnow().datetime)


def get_node_hostname():
    """Get a scanning node hostname"""
    try:
        hostq = Session\
                .query(Server.hostname)\
                .filter(Server.hostname != 'default')[0]
        hostname = hostq.hostname
    except IndexError:
        hostname = system_hostname()
    return hostname


# pylint: disable-msg=R0913
def add_policy(form, policy_type, current_user, host, remote_addr,
        respond=None):
    """Add a Policy"""
    policy = Policy()
    policy.name = form.name.data
    policy.policy_type = policy_type
    policy.enabled = False
    Session.add(policy)
    Session.commit()
    settings = dict(u=policy.name, t=POLICY_URL_MAP[str(policy_type)])
    info = settings_auditmsgs.POLICYADD_MSG % settings
    audit_log(current_user.username, 3, unicode(info), host,
            remote_addr, arrow.utcnow().datetime)
    if respond:
        return policy


def update_policy(form, policy, current_user, host, remote_addr):
    """Update the policy"""
    if policy.name != form.name.data or (form.enabled is not None and
            policy.enabled != form.enabled.data):
        policy.name = form.name.data
        policy.enabled = form.enabled.data
        if not policy.enabled:
            settings = get_policy_setting()
            field = POLICY_SETTINGS_MAP[policy.policy_type]
            if getattr(settings, field) == policy.id:
                setattr(settings, field, 0)
            Session.add(settings)
            Session.commit()
            disable_domain_policies(field, policy.id)
        Session.add(policy)
        Session.commit()
        settings = dict(u=policy.name,
                    t=POLICY_URL_MAP[str(policy.policy_type)])
        info = settings_auditmsgs.POLICYUPDATE_MSG % settings
        audit_log(current_user.username, 2, unicode(info), host,
                remote_addr, arrow.utcnow().datetime)
        if policy.enabled:
            backend_create_content_rules(policy.id, policy.name)
        else:
            backend_create_content_rules(policy.id, policy.name, True)
            backend_create_content_ruleset()
        return True
    else:
        return False


def delete_policy(policy, current_user, host, remote_addr):
    """Delete the policy"""
    policy_name = policy.name
    policy_type = policy.policy_type
    backend_create_content_rules(policy.id, policy.name, True)
    settings = get_policy_setting()
    field = POLICY_SETTINGS_MAP[policy.policy_type]
    if getattr(settings, field) == policy.id:
        setattr(settings, field, 0)
    disable_domain_policies(field, policy.id)
    backend_create_content_ruleset()
    Session.add(settings)
    Session.commit()
    Session.delete(policy)
    Session.commit()
    settings = dict(u=policy_name, t=POLICY_URL_MAP[str(policy_type)])
    info = settings_auditmsgs.POLICYDEL_MSG % settings
    audit_log(current_user.username, 4, unicode(info), host,
            remote_addr, arrow.utcnow().datetime)


def clone_policy(form, policy_type, current_user, host, remote_addr):
    """Clone the default policy"""
    policy = add_policy(form, policy_type, current_user, host, remote_addr,
            True)
    name = "%s.conf" % POLICY_FILE_MAP[policy.policy_type]
    filename = os.path.join('/etc/MailScanner', name)
    hostname = get_node_hostname()
    rules = get_ruleset_data(filename, hostname)
    for index, rule in enumerate(rules):
        ruleobj = Rule()
        if rule['action'].startswith('rename to '):
            ruleobj.action = 'renameto'
            match = RENAME_RE.match(rule['action'])
            if not match:
                ruleobj = None
                continue
            ruleobj.options = match.groupdict()['options']
        elif '@' in rule['action']:
            ruleobj.action = 'email-addresses'
            ruleobj.options = rule['action']
        else:
            ruleobj.action = rule['action']
        ruleobj.expression = rule['expression']
        ruleobj.description = rule['logtext']
        ruleobj.enabled = True
        ruleobj.ordering = index
        ruleobj.policy_id = policy.id
        Session.add(ruleobj)
        Session.commit()
        settings = dict(r=ruleobj.description, p=policy.name)
        info = settings_auditmsgs.RULEADD_MSG % settings
        audit_log(current_user.username, 3, unicode(info), host,
                remote_addr, arrow.utcnow().datetime)


def process_default_rules(policy_type):
    """Process default rules"""
    name = "%s.conf" % POLICY_FILE_MAP[int(policy_type)]
    filename = os.path.join('/etc/MailScanner', name)
    hostname = get_node_hostname()
    drules = get_ruleset_data(filename, hostname)
    if drules:
        def process_line(rule):
            """process rule"""
            if rule['action'].startswith('rename to '):
                match = RENAME_RE.match(rule['action'])
                if match:
                    rule['options'] = match.groupdict()['options']
                else:
                    rule['options'] = ''
                rule['action'] = 'renameto'
            elif '@' in rule['action']:
                rule['options'] = rule['action']
                rule['action'] = 'email-addresses'
            else:
                rule['options'] = ''
            return rule
        drules.reverse()
        rules = (process_line(rule) for rule in drules)
        return rules
    else:
        return []


def add_rule(form, policy, current_user, host, remote_addr):
    """Add a Rule"""
    ordering = Session.query(func.max(Rule.ordering).label('max_ordering'))\
                        .filter(Rule.policy_id == policy.id)\
                        .one()
    if ordering.max_ordering is None:
        order = 0
    else:
        order = ordering.max_ordering + 1
    rule = Rule()
    for field in form:
        if field.name in ['csrf_token']:
            continue
        setattr(rule, field.name, field.data)
    rule.ordering = order
    rule.policy_id = policy.id
    Session.add(rule)
    Session.commit()
    settings = dict(r=rule.description, p=policy.name)
    info = settings_auditmsgs.RULEADD_MSG % settings
    audit_log(current_user.username, 3, unicode(info), host,
            remote_addr, arrow.utcnow().datetime)
    backend_create_content_rules(rule.policy.id, rule.policy.name)


def update_rule(form, rule, current_user, host, remote_addr):
    """Update a Rule"""
    updated = False
    for field in form:
        if field.name in ['csrf_token']:
            continue
        if field.data != getattr(rule, field.name):
            setattr(rule, field.name, field.data)
            updated = True
    if updated:
        if not rule.enabled and len(rule.policy.rules) == 1:
            rule.policy.enabled = False
            Session.add(rule.policy)
            Session.commit()
            settings = get_policy_setting()
            field = POLICY_SETTINGS_MAP[rule.policy.policy_type]
            if getattr(settings, field) == rule.policy.id:
                setattr(settings, field, 0)
                Session.add(settings)
                Session.commit()
            backend_create_content_rules(rule.policy.id,
                                        rule.policy.name,
                                        True)
            disable_domain_policies(field, rule.policy.id)
            backend_create_content_ruleset()
        else:
            backend_create_content_rules(rule.policy.id,
                                        rule.policy.name)
        Session.add(rule)
        Session.commit()
        settings = dict(r=rule.description, p=rule.policy.name)
        info = settings_auditmsgs.RULEUPDATE_MSG % settings
        audit_log(current_user.username, 2, unicode(info), host,
                remote_addr, arrow.utcnow().datetime)
    return updated


def delete_rule(rule, current_user, host, remote_addr):
    """Delete a Rule"""
    if len(rule.policy.rules) == 1:
        rule.policy.enabled = False
        Session.add(rule.policy)
        Session.commit()
        settings = get_policy_setting()
        field = POLICY_SETTINGS_MAP[rule.policy.policy_type]
        if getattr(settings, field) == rule.policy.id:
            setattr(settings, field, 0)
            Session.add(settings)
            Session.commit()
        disable_domain_policies(field, rule.policy.id)
        backend_create_content_rules(rule.policy.id,
                                    rule.policy.name,
                                    True)
        backend_create_content_ruleset()
    description = rule.description
    policy_name = rule.policy.name
    policy_id = rule.policy.id
    policy_name = rule.policy.name
    Session.delete(rule)
    Session.commit()
    settings = dict(r=description, p=policy_name)
    info = settings_auditmsgs.RULEDELETE_MSG % settings
    audit_log(current_user.username, 4, unicode(info), host,
            remote_addr, arrow.utcnow().datetime)
    backend_create_content_rules(policy_id, policy_name)


def create_mta_setting(form, setting_type, current_user, host, remote_addr):
    """Create MTA Settings"""
    settings = MTASettings()
    for field in form:
        if field.name in ['csrf_token']:
            continue
        setattr(settings, field.name, field.data)
    # settings.address_type = setting_type
    Session.add(settings)
    Session.commit()
    mdict = dict(s=settings.address, t=setting_type)
    info = settings_auditmsgs.MTASETTINGADD_MSG % mdict
    audit_log(current_user.username, 4, unicode(info), host,
            remote_addr, arrow.utcnow().datetime)
    backend_create_mta_settings(setting_type)


def update_mta_setting(form, settings, current_user, host, remote_addr):
    """Update MTA Settings"""
    updated = False
    for field in form:
        if field.name in ['csrf_token']:
            continue
        if field.data != getattr(settings, field.name):
            setattr(settings, field.name, field.data)
            updated = True
    if updated:
        Session.add(settings)
        Session.commit()
        mdict = dict(s=settings.address, t=settings.address_type)
        info = settings_auditmsgs.MTASETTINGUPDATE_MSG % mdict
        audit_log(current_user.username, 2, unicode(info), host,
                remote_addr, arrow.utcnow().datetime)
        backend_create_mta_settings(settings.address_type)
    return updated


def delete_mta_setting(settings, current_user, host, remote_addr):
    """Delete MTA Settings"""
    address_type = settings.address_type
    mdict = dict(s=settings.address, t=address_type)
    info = settings_auditmsgs.MTASETTINGDELETE_MSG % mdict
    Session.delete(settings)
    Session.commit()
    audit_log(current_user.username, 4, unicode(info), host,
            remote_addr, arrow.utcnow().datetime)
    backend_create_mta_settings(address_type)


def update_local_score(form, score, current_user, host, remote_addr):
    """update local score"""
    if score.local_score != form.local_score.data:
        score.local_score = form.local_score.data
        Session.add(score)
        Session.commit()
        mdict = dict(s=score.id, l=score.local_score)
        info = settings_auditmsgs.LOCALSCOREUPDATE_MSG % mdict
        audit_log(current_user.username, 2, unicode(info), host,
                remote_addr, arrow.utcnow().datetime)
        backend_create_local_scores()
