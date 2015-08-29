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
"Accounts controller"
# pylint: disable-msg=C0302
import os
import shutil
import socket
import struct
import urllib2
import logging
import hashlib

import ldap
import arrow

from urllib import unquote
from urlparse import urlparse
from datetime import timedelta

from pylons import request, response, session, tmpl_context as c, url, config
from pylons.controllers.util import redirect, abort
from pylons.i18n.translation import _
from webhelpers import paginate
from celery.result import AsyncResult
from sqlalchemy.sql import and_
from sqlalchemy.sql.expression import false
from sqlalchemy.orm.exc import NoResultFound
from marrow.mailer import Message as Msg, Mailer
from sqlalchemy.exc import IntegrityError, DataError
# pylint: disable-msg=E0611
from repoze.what.predicates import All, not_anonymous
# pylint: disable-msg=E0611
from repoze.what.plugins.pylonshq import ActionProtector
from sphinxapi import SphinxClient, SPH_MATCH_EXTENDED2

from baruwa.model.meta import Session
from baruwa.model.domains import Domain
from baruwa.lib.misc import check_language, iscsv, convert_acct_to_json
from baruwa.lib.misc import check_num_param, mkpasswd, extract_sphinx_opts
from baruwa.lib.base import BaseController
from baruwa.lib.caching_query import FromCache
from baruwa.lib.audit import audit_log
from baruwa.commands import get_conf_options
from baruwa.lib.backend import backend_user_update
from baruwa.lib.regex import URL_PREFIX_RE
from baruwa.tasks.accounts import importaccounts, exportaccounts
from baruwa.lib.query import clean_sphinx_q, restore_sphinx_q
from baruwa.lib.helpers import flash, flash_info, flash_alert
from baruwa.lib.auth.predicates import OwnsDomain
from baruwa.lib.auth.predicates import OnlyAdminUsers, CanAccessAccount
from baruwa.forms.organizations import ImportCSVForm
from baruwa.forms.accounts import EditUserForm, AddressForm
from baruwa.forms.accounts import ChangePasswordForm, UserPasswordForm
from baruwa.forms.accounts import BulkDelUsers, ResetPwForm
from baruwa.model.accounts import User, domain_users
from baruwa.model.accounts import domain_owners as dom_owns
from baruwa.model.accounts import organizations_admins as oas, ResetToken
from baruwa.lib.audit.msgs import accounts as auditmsgs
from baruwa.lib.api import create_user, user_add_form, update_changed, \
    user_update_form, update_user, delete_user, create_address, \
    update_address, delete_address, get_address, user_address_update, \
    add_user, update_login, change_user_pw

log = logging.getLogger(__name__)

FORM_FIELDS = ['username', 'firstname', 'lastname', 'email', 'active',
    'send_report', 'spam_checks', 'low_score', 'high_score', 'domains',
    'timezone']


# pylint: disable-msg=R0904
class AccountsController(BaseController):
    "Accounts controller"

    def __before__(self):
        "set context"
        BaseController.__before__(self)
        if self.identity:
            c.user = self.identity['user']
        else:
            c.user = None
        c.selectedtab = 'accounts'

    def login(self):
        "login"
        if request.remote_addr in session:
            if session[request.remote_addr] > arrow.utcnow().datetime:
                msg = _('You have been banned after'
                            ' several failed logins')
                log.info(msg)
                abort(409, msg)
            else:
                del session[request.remote_addr]
                session.save()

        identity = request.environ.get('repoze.who.identity')
        came_from = unquote(str(request.GET.get('came_from', '')))
        if not came_from or ' ' in came_from:
            came_from = url('home')
        if '://' in came_from:
            from_url = urlparse(came_from)
            came_from = from_url[2]

        if identity:
            redirect(url(came_from))
        else:
            c.came_from = came_from
            c.login_counter = request.environ['repoze.who.logins']
            if c.login_counter >= 3:
                ban_until = arrow.utcnow().datetime + timedelta(minutes=5)
                if request.remote_addr not in session:
                    session[request.remote_addr] = ban_until
                    session.save()
                else:
                    if arrow.utcnow().datetime > session[request.remote_addr]:
                        del session[request.remote_addr]
                        session.save()
            c.form = ResetPwForm(request.POST, csrf_context=session)
            return self.render('/accounts/login.html')

    def loggedin(self):
        "Landing page"
        came_from = (unquote(str(request.params.get('came_from', ''))) or
                    url('/'))
        if not self.identity:
            if 'repoze.who.logins' in request.environ:
                login_counter = request.environ['repoze.who.logins'] + 1
            else:
                abort(409)
            redirect(url('/accounts/login',
                    came_from=came_from,
                    __logins=login_counter))
        userid = self.identity['repoze.who.userid']
        user = self.identity['user']
        if user is None:
            try:
                user, local_part, domain, domains = add_user(userid)
                msg = _('First time Login from external auth,'
                        ' your local account was created')
                user_address_update(user, local_part, domain,
                                    domains, self.identity)
            except IntegrityError:
                Session.rollback()
                redirect(url('/logout'))
            except ldap.LDAPError:
                pass
        else:
            if not user.active:
                redirect(url('/logout'))
            msg = _('Login successful, Welcome back %(username)s !' %
                    dict(username=userid))
        update_login(user)
        if user.is_peleb:
            for domain in user.domains:
                if check_language(domain.language):
                    session['lang'] = domain.language
                    session.save()
                    break
        session['taskids'] = []
        session.save()
        info = auditmsgs.ACCOUNTLOGIN_MSG % dict(u=user.username)
        audit_log(user.username,
                6, unicode(info), request.host,
                request.remote_addr, arrow.utcnow().datetime)
        flash(msg)
        log.info(msg)
        redirect(url(came_from))

    # pylint: disable-msg=R0201
    def loggedout(self):
        "Logged out page"
        session.clear()
        if 'theme' in session:
            del session['theme']
        session.save()
        came_from = (unquote(str(request.params.get('came_from', '')))
                    or url('/accounts/login'))
        redirect(url(came_from))

    def passwdreset(self):
        """Render password reset page"""
        c.came_from = '/'
        c.login_counter = 0
        c.form = ResetPwForm(request.POST, csrf_context=session)
        if request.method == 'POST' and c.form.validate():
            key_seed = '%s%s' % (c.form.email.data, arrow.utcnow().ctime())
            token = hashlib.sha1(key_seed).hexdigest()
            user = Session.query(User)\
                            .filter(User.email == c.form.email.data)\
                            .one()
            if not user.local:
                flash(_('The account %s is an external account, use your'
                        ' External systems to change the password. '
                        'Contact your system adminstrator if you do not '
                        'know which external systems you authenticate to')
                        % user.email)
                redirect(url('/accounts/login'))
            rtoken = Session\
                    .query(ResetToken.used)\
                    .filter(ResetToken.used == false())\
                    .filter(ResetToken.user_id == user.id)\
                    .all()
            if not rtoken:
                rtoken = ResetToken(token, user.id)
                Session.add(rtoken)
                Session.commit()
                host = URL_PREFIX_RE.sub('', request.host_url)
                c.username = user.username
                c.firstname = user.firstname or user.username
                c.reset_url = url('accounts-pw-token-reset',
                                token=token,
                                host=host)
                text = self.render('/email/pwreset.txt')
                mailer = Mailer(get_conf_options(config))
                mailer.start()
                sdrnme = config.get('baruwa.custom.name', 'Baruwa')
                email = Msg(author=[(sdrnme,
                            config.get('baruwa.reports.sender'))],
                            to=[('', c.form.email.data)],
                            subject=_("[%s] Password reset request") % sdrnme)
                email.plain = text
                mailer.send(email)
                mailer.stop()
            flash(_('An email has been sent to the address provided, '
                    'please follow the instructions in that email to '
                    'reset your password.'))
            redirect(url('/accounts/login'))
        return self.render('/accounts/login.html')

    def pwtokenreset(self, token):
        """Reset password using token"""
        try:
            token = Session.query(ResetToken)\
                    .filter(ResetToken.token == token)\
                    .filter(ResetToken.used == false()).one()
            threshold = token.timestamp + timedelta(minutes=20)
            if arrow.utcnow().datetime > threshold:
                Session.delete(token)
                Session.commit()
                raise NoResultFound
            user = self._get_user(token.user_id)
            if not user or user.is_superadmin:
                raise NoResultFound
            passwd = mkpasswd()
            user.set_password(passwd)
            Session.add(user)
            Session.delete(token)
            Session.commit()
            c.passwd = passwd
            c.firstname = user.firstname or user.username
            text = self.render('/email/pwchanged.txt')
            mailer = Mailer(get_conf_options(config))
            mailer.start()
            sdrnme = config.get('baruwa.custom.name', 'Baruwa')
            email = Msg(author=[(sdrnme,
                        config.get('baruwa.reports.sender'))],
                        to=[('', user.email)],
                        subject=_("[%s] Password reset") % sdrnme)
            email.plain = text
            mailer.send(email)
            mailer.stop()
            flash(_('The password has been reset, check your email for'
                    ' the temporary password you should use to login.'))
        except NoResultFound:
            msg = _('The token used is invalid or does not exist')
            flash_alert(msg)
            log.info(msg)
        redirect(url('/accounts/login'))

    @ActionProtector(All(not_anonymous(), OnlyAdminUsers(),
    CanAccessAccount()))
    def pwchange(self, userid):
        """Reset a user password"""
        user = self._get_user(userid)
        if not user:
            abort(404)
        c.form = ChangePasswordForm(request.POST, csrf_context=session)
        if request.method == 'POST' and c.form.validate():
            if user.local and not user.is_superadmin:
                change_user_pw(user, c.user, c.form.password1.data,
                                request.host, request.remote_addr)
                msg = _('The account password for %(name)s has been reset') \
                        % dict(name=user.username)
                flash(msg)
            else:
                if user.is_superadmin:
                    flash(_('Admin accounts can not be modified via the web'))
                else:
                    flash(_('This is an external account, use'
                        ' external system to reset the password'))
            redirect(url('account-detail', userid=user.id))
        c.id = userid
        c.username = user.username
        c.posturl = 'accounts-pw-change'
        return self.render('/accounts/pwchange.html')

    @ActionProtector(not_anonymous())
    def upwchange(self, userid):
        """User change own password"""
        user = self._get_user(userid)
        if not user:
            abort(404)
        if user.id != c.user.id or c.user.is_superadmin:
            abort(403)
        c.form = UserPasswordForm(request.POST, csrf_context=session)
        if (request.method == 'POST' and c.form.validate() and
            user.validate_password(c.form.password3.data)):
            if user.local:
                user.set_password(c.form.password1.data)
                Session.add(user)
                Session.commit()
                flash(_('The account password for %(name)s has been reset')
                    % dict(name=user.username))
                info = auditmsgs.PASSWORDCHANGE_MSG % dict(u=user.username)
                audit_log(c.user.username,
                        2, unicode(info), request.host,
                        request.remote_addr, arrow.utcnow().datetime)
            else:
                flash(_('This is an external account, use'
                    ' external system to reset the password'))
            redirect(url('account-detail', userid=user.id))
        elif (request.method == 'POST' and not
                user.validate_password(c.form.password3.data)
                and not c.form.password3.errors):
            flash_alert(_('The old password supplied does'
                        ' not match our records'))
        c.id = userid
        c.username = user.username
        c.posturl = 'accounts-pw-uchange'
        return self.render('/accounts/pwchange.html')

    # pylint: disable-msg=W0622
    @ActionProtector(All(not_anonymous(), OnlyAdminUsers()))
    def index(self, page=1, orgid=None, domid=None, format=None):
        """GET /accounts/: Paginate items in the collection"""
        num_items = session.get('accounts_num_items', 10)
        c.form = BulkDelUsers(request.POST, csrf_context=session)
        if request.method == 'POST':
            if c.form.accountid.data and \
                str(c.user.id) in c.form.accountid.data:
                c.form.accountid.data.remove(str(c.user.id))
            if c.form.accountid.data and c.form.whatdo.data == 'disable':
                Session.query(User)\
                    .filter(User.id.in_(c.form.accountid.data))\
                    .update({'active': False}, synchronize_session='fetch')
                Session.commit()
            if c.form.accountid.data and c.form.whatdo.data == 'enable':
                Session.query(User)\
                        .filter(User.id.in_(c.form.accountid.data))\
                        .update({'active': True}, synchronize_session='fetch')
                Session.commit()
            if c.form.accountid.data and c.form.whatdo.data == 'delete':
                session['bulk_account_delete'] = c.form.accountid.data
                session.save()
                # redirect for confirmation
                redirect(url('accounts-confirm-delete'))
        users = Session.query(User.id, User.username, User.firstname,
                            User.lastname, User.email, User.active,
                            User.local, User.account_type).order_by(User.id)
        usrcount = Session.query(User.id)
        if c.user.is_domain_admin:
            users = users.join(domain_users, (dom_owns,
                                domain_users.c.domain_id ==
                                dom_owns.c.domain_id),
                                (oas,
                                dom_owns.c.organization_id ==
                                oas.c.organization_id))\
                                .filter(oas.c.user_id == c.user.id)
            usrcount = usrcount.join(domain_users, (dom_owns,
                                    domain_users.c.domain_id ==
                                    dom_owns.c.domain_id),
                                    (oas,
                                    dom_owns.c.organization_id ==
                                    oas.c.organization_id))\
                                    .filter(oas.c.user_id == c.user.id)
        if domid:
            users = users.filter(and_(domain_users.c.domain_id == domid,
                                domain_users.c.user_id == User.id))
            usrcount = usrcount.filter(and_(domain_users.c.domain_id == domid,
                                domain_users.c.user_id == User.id))
        if orgid:
            users = users.filter(and_(domain_users.c.user_id == User.id,
                            domain_users.c.domain_id == dom_owns.c.domain_id,
                            dom_owns.c.organization_id == orgid,))
            usrcount = usrcount.filter(and_(domain_users.c.user_id == User.id,
                            domain_users.c.domain_id == dom_owns.c.domain_id,
                            dom_owns.c.organization_id == orgid,))

        users = users.distinct(User.id)
        usrcount = usrcount.distinct(User.id)

        pages = paginate.Page(users, page=int(page),
                                items_per_page=num_items,
                                item_count=usrcount.count())
        if format == 'json':
            response.headers['Content-Type'] = 'application/json'
            data = convert_acct_to_json(pages, orgid)
            return data

        c.page = pages
        c.domid = domid
        c.orgid = orgid
        return self.render('/accounts/index.html')

    # pylint: disable-msg=R0914,W0142,W0613
    @ActionProtector(All(not_anonymous(), OnlyAdminUsers()))
    def search(self, format=None):
        "Search for accounts"
        total_found = 0
        search_time = 0
        num_items = session.get('accounts_num_items', 10)
        qry = request.GET.get('q', '')
        doms = request.GET.get('d', None)
        kwds = {'presliced_list': True}
        page = int(request.GET.get('p', 1))
        conn = SphinxClient()
        sphinxopts = extract_sphinx_opts(config['sphinx.url'])
        conn.SetServer(sphinxopts.get('host', '127.0.0.1'))
        conn.SetMatchMode(SPH_MATCH_EXTENDED2)
        conn.SetFieldWeights(dict(username=50, email=30,
                                firstname=10, lastname=10))
        if page == 1:
            conn.SetLimits(0, num_items, 500)
        else:
            page = int(page)
            offset = (page - 1) * num_items
            conn.SetLimits(offset, num_items, 500)
        if doms:
            conn.SetFilter('domains', [int(doms), ])
        if c.user.is_domain_admin:
            # crcs = get_dom_crcs(Session, c.user)
            domains = Session.query(Domain.id).join(dom_owns,
                        (oas, dom_owns.c.organization_id ==
                        oas.c.organization_id))\
                        .filter(oas.c.user_id == c.user.id)
            conn.SetFilter('domains', [domain[0] for domain in domains])
        qry = clean_sphinx_q(qry)
        try:
            results = conn.Query(qry, 'accounts, accounts_rt')
        except (socket.timeout, struct.error):
            redirect(request.path_qs)
        qry = restore_sphinx_q(qry)
        if results and results['matches']:
            ids = [hit['id'] for hit in results['matches']]
            total_found = results['total_found']
            search_time = results['time']
            users = Session.query(User.id,
                                    User.username,
                                    User.firstname,
                                    User.lastname,
                                    User.email,
                                    User.active,
                                    User.local,
                                    User.account_type)\
                                .filter(User.id.in_(ids))\
                                .order_by(User.id)\
                                .all()
            usercount = total_found
        else:
            users = []
            usercount = 0
        c.q = qry
        c.d = doms
        c.total_found = total_found
        c.search_time = search_time
        c.page = paginate.Page(users, page=int(page),
                                items_per_page=num_items,
                                item_count=usercount, **kwds)
        return self.render('/accounts/searchresults.html')

    @ActionProtector(All(not_anonymous(), CanAccessAccount()))
    def detail(self, userid):
        """GET /accounts/userid/ Show a specific item"""
        user = self._get_user(userid)
        if not user:
            abort(404)
        c.account = user
        return self.render('/accounts/account.html')

    @ActionProtector(All(not_anonymous(), OnlyAdminUsers()))
    def add(self):
        """/accounts/new"""
        c.form = user_add_form(c.user, request.POST, session)
        if request.method == 'POST' and c.form.validate():
            try:
                user = create_user(c.form, c.user.username, request.host,
                                    request.remote_addr)
                flash(_('The account: %(user)s was created successfully') %
                        {'user': user.username})
                redirect(url('account-detail', userid=user.id))
            except IntegrityError:
                Session.rollback()
                flash_alert(
                    _('Either the username or email address already exist'))
        return self.render('/accounts/new.html')

    @ActionProtector(All(not_anonymous(), CanAccessAccount()))
    def edit(self, userid):
        """GET /accounts/edit/id: Form to edit an existing item"""
        user = self._get_user(userid)
        if not user:
            abort(404)

        c.form = user_update_form(user, c.user, request.POST, session)
        if request.method == 'POST' and c.form.validate():
            kwd = dict(userid=user.id)
            if update_changed(c.form, FORM_FIELDS, user):
                try:
                    update_user(user, c.user, request.host,
                                request.remote_addr)
                    flash(_('The account has been updated'))
                    kwd['uc'] = 1
                except IntegrityError:
                    Session.rollback()
                    flash_alert(
                        _('The account: %(acc)s could not be updated') %
                        dict(acc=user.username))
                if (user.id == c.user.id and c.form.active and
                    c.form.active.data is False):
                    redirect(url('/logout'))
            else:
                flash_info(_('No changes made to the account'))
            redirect(url(controller='accounts', action='detail', **kwd))
        c.fields = FORM_FIELDS
        c.id = userid
        return self.render('/accounts/edit.html')

    @ActionProtector(All(not_anonymous(), OnlyAdminUsers(),
    CanAccessAccount()))
    def delete(self, userid):
        """/accounts/delete/id"""
        user = self._get_user(userid)
        if not user:
            abort(404)

        c.form = EditUserForm(request.POST, user, csrf_context=session)
        del c.form.domains
        if request.method == 'POST':
            if c.form.validate():
                delete_user(user, c.user, request.host, request.remote_addr)
                flash(_('The account has been deleted'))
                redirect(url(controller='accounts', action='index'))
        else:
            flash_info(_('The account: %(a)s and all associated data'
                ' will be deleted, This action is not reversible.') %
                dict(a=user.username))
        c.fields = FORM_FIELDS
        c.id = userid
        return self.render('/accounts/delete.html')

    @ActionProtector(not_anonymous())
    def confirm_delete(self):
        "Confirm mass delete"
        accountids = session.get('bulk_account_delete', [])
        if not accountids:
            redirect(url(controller='accounts', action='index'))

        num_items = 10
        if len(accountids) > num_items and len(accountids) <= 20:
            num_items = 20
        if len(accountids) > num_items and len(accountids) <= 50:
            num_items = 50
        if len(accountids) > num_items and len(accountids) <= 100:
            num_items = 100

        users = Session.query(User).filter(User.id.in_(accountids))
        usrcount = Session.query(User.id)

        if c.user.is_domain_admin and usrcount:
            users = users.join(domain_users, (dom_owns,
                    domain_users.c.domain_id == dom_owns.c.domain_id),
                    (oas, dom_owns.c.organization_id == oas.c.organization_id))\
                    .filter(oas.c.user_id == c.user.id)
            usrcount = usrcount.join(domain_users, (dom_owns,
                        domain_users.c.domain_id == dom_owns.c.domain_id),
                        (oas, dom_owns.c.organization_id ==
                        oas.c.organization_id))\
                        .filter(oas.c.user_id == c.user.id)

        if request.method == 'POST':
            tasks = []
            # try:
            for account in users.all():
                info = auditmsgs.DELETEACCOUNT_MSG % dict(u=account.username)
                Session.delete(account)
                tasks.append([c.user.username,
                            4,
                            unicode(info),
                            request.host,
                            request.remote_addr,
                            arrow.utcnow().datetime])
            Session.commit()
            del session['bulk_account_delete']
            session.save()
            backend_user_update(None, True)
            for task in tasks:
                audit_log(*task)
            flash(_('The accounts have been deleted'))
            redirect(url(controller='accounts'))
        else:
            flash(_('The following accounts are about to be deleted,'
                    ' this action is not reversible, Do you wish to '
                    'continue ?'))

        try:
            c.page = paginate.Page(users, page=1,
                                    items_per_page=num_items,
                                    item_count=usrcount.count())
        except DataError:
            msg = _('An error occured try again')
            flash_alert(msg)
            log.info(msg)
            redirect(url(controller='accounts', action='index'))
        return self.render('/accounts/confirmbulkdel.html')

    @ActionProtector(All(not_anonymous(), OnlyAdminUsers(),
    CanAccessAccount()))
    def addaddress(self, userid):
        "Add address"
        user = self._get_user(userid)
        if not user:
            abort(404)

        c.form = AddressForm(request.POST, csrf_context=session)
        if request.method == 'POST' and c.form.validate():
            try:
                addr = create_address(c.form, user, c.user,
                                    request.host, request.remote_addr)
                flash(
                    _('The alias address %(address)s was successfully created.'
                    % dict(address=addr.address)))
            except IntegrityError:
                Session.rollback()
                msg = _('The address %(addr)s already exists') % \
                        dict(addr=c.form.address.data)
                flash_alert(msg)
                log.info(msg)
            except NoResultFound:
                domain = c.form.address.data.split('@')[1]
                msg = _('Domain: %(d)s does not belong to you') % \
                        dict(d=domain)
                flash(msg)
                log.info(msg)
            redirect(url(controller='accounts', action='detail',
                    userid=userid))
        c.id = userid
        return self.render('/accounts/addaddress.html')

    @ActionProtector(All(not_anonymous(), OnlyAdminUsers(),
    CanAccessAccount()))
    def editaddress(self, addressid):
        "Edit address"
        address = get_address(addressid)
        if not address:
            abort(404)

        c.form = AddressForm(request.POST, address, csrf_context=session)
        if request.method == 'POST' and c.form.validate():
            try:
                if (address.address != c.form.address.data or
                    address.enabled != c.form.enabled.data):
                    update_address(c.form, address, c.user,
                                request.host, request.remote_addr)
                    flash(_('The alias address has been updated'))
                else:
                    flash_info(_('No changes were made to the address'))
            except IntegrityError:
                Session.rollback()
                msg = _('The address %(addr)s already exists') % \
                        dict(addr=c.form.address.data)
                flash_alert(msg)
                log.info(msg)
            except NoResultFound:
                domain = c.form.address.data.split('@')[1]
                msg = _('Domain: %(d)s does not belong to you') % \
                        dict(d=domain)
                flash(msg)
                log.info(msg)
            redirect(url(controller='accounts', action='detail',
            userid=address.user_id))
        c.id = addressid
        c.userid = address.user_id
        return self.render('/accounts/editaddress.html')

    @ActionProtector(All(not_anonymous(), OnlyAdminUsers(),
    CanAccessAccount()))
    def deleteaddress(self, addressid):
        "Delete address"
        address = get_address(addressid)
        if not address:
            abort(404)

        c.form = AddressForm(request.POST, address, csrf_context=session)
        if request.method == 'POST' and c.form.validate():
            user_id = delete_address(address, c.user,
                            request.host, request.remote_addr)
            flash(_('The address has been deleted'))
            redirect(url(controller='accounts', action='detail',
            userid=user_id))
        c.id = addressid
        c.userid = address.user_id
        return self.render('/accounts/deleteaddress.html')

    def set_language(self):
        "Set the language"
        nextpage = request.params.get('next', None)
        if not nextpage:
            nextpage = request.headers.get('Referer', None)
        if not nextpage:
            nextpage = '/'
        if '://' in nextpage:
            from_url = urlparse(nextpage)
            nextpage = from_url[2]
        lang_code = request.params.get('language', None)
        if lang_code and check_language(lang_code):
            session['lang'] = lang_code
            session.save()
        params = []
        for param in request.params:
            if param not in ['language', 'amp']:
                value = request.params[param]
                if value:
                    if (param == 'came_from' and
                        '://' in urllib2.unquote(value)):
                        urlparts = urlparse(urllib2.unquote(value))
                        value = urlparts[2] or '/'
                    params.append('%s=%s' % (urllib2.quote(param),
                                            urllib2.quote(value)))
        if 'lc=1' not in params:
            params.append('lc=1')
        if params:
            nextpage = "%s?%s" % (nextpage, '&amp;'.join(params))
        redirect(nextpage)

    @ActionProtector(All(not_anonymous(), OwnsDomain()))
    def import_accounts(self, domainid):
        "import accounts"
        try:
            cachekey = u'domain-%s' % domainid
            domain = Session.query(Domain.id, Domain.name)\
                    .filter(Domain.id == domainid)\
                    .options(FromCache('sql_cache_med', cachekey)).one()
        except NoResultFound:
            abort(404)

        c.form = ImportCSVForm(request.POST, csrf_context=session)
        if request.method == 'POST' and c.form.validate():
            basedir = config['pylons.cache_dir']
            csvdata = request.POST['csvfile']
            if hasattr(csvdata, 'filename'):
                dstfile = os.path.join(basedir, 'uploads',
                            csvdata.filename.lstrip(os.sep))
                if not os.path.exists(dstfile) and iscsv(csvdata.file):
                    csvfile = open(dstfile, 'w')
                    shutil.copyfileobj(csvdata.file, csvfile)
                    csvdata.file.close()
                    csvfile.close()
                    task = importaccounts.apply_async(args=[
                            domainid,
                            dstfile,
                            c.form.skipfirst.data,
                            c.user.id])
                    session['taskids'].append(task.task_id)
                    session['acimport-count'] = 1
                    session['acimport-file'] = dstfile
                    session.save()
                    msg = _('File uploaded, and is being processed, this page'
                            ' will automatically refresh to show the status')
                    flash(msg)
                    log.info(msg)
                    redirect(url('accounts-import-status',
                            taskid=task.task_id))
                else:
                    filename = csvdata.filename.lstrip(os.sep)
                    if not iscsv(csvdata.file):
                        msg = _('The file: %s is not a CSV file') % filename
                        flash_alert(msg)
                        log.info(msg)
                    else:
                        msg = _('The file: %s already exists and'
                                ' is being processed.') % filename
                        flash_alert(msg)
                        log.info(msg)
                    csvdata.file.close()
            else:
                msg = _('No CSV was file uploaded, try again')
                flash_alert(msg)
                log.info(msg)

        c.domain = domain
        return self.render('/accounts/importaccounts.html')

    @ActionProtector(All(not_anonymous(), OnlyAdminUsers()))
    def import_status(self, taskid):
        "import status"
        result = AsyncResult(taskid)
        if result is None or taskid not in session['taskids']:
            msg = _('The task status requested has expired or does not exist')
            flash(msg)
            log.info(msg)
            redirect(url(controller='accounts', action='index'))

        if result.ready():
            finished = True
            flash.pop_messages()
            if isinstance(result.result, Exception):
                if c.user.is_superadmin:
                    msg = _('Error occured in processing %s') % result.result
                    flash_alert(msg)
                    log.info(msg)
                else:
                    flash_alert(_('Backend error occured during processing.'))
                redirect(url(controller='accounts'))
            backend_user_update(None, True)
            audit_log(c.user.username,
                    3, unicode(auditmsgs.ACCOUNTIMPORT_MSG),
                    request.host,
                    request.remote_addr,
                    arrow.utcnow().datetime)
        else:
            session['acimport-count'] += 1
            if (session['acimport-count'] >= 10 and
                result.state in ['PENDING', 'RETRY', 'FAILURE']):
                result.revoke()
                try:
                    os.unlink(session['acimport-file'])
                except OSError:
                    pass
                del session['acimport-count']
                session.save()
                msg = _('The import could not be processed,'
                        ' try again later')
                flash_alert(msg)
                log.info(msg)
                redirect(url(controller='accounts'))
            finished = False

        c.finished = finished
        c.results = result.result
        c.success = result.successful()
        return self.render('/accounts/importstatus.html')

    @ActionProtector(All(not_anonymous(), OnlyAdminUsers()))
    def export_accounts(self, domainid=None, orgid=None):
        "export domains"
        task = exportaccounts.apply_async(args=[
                domainid, c.user.id, orgid])
        if 'taskids' not in session:
            session['taskids'] = []
        session['taskids'].append(task.task_id)
        session['acexport-count'] = 1
        session.save()
        msg = _('Accounts export is being processed')
        flash(msg)
        log.info(msg)
        redirect(url('accounts-export-status', taskid=task.task_id))

    @ActionProtector(All(not_anonymous(), OnlyAdminUsers()))
    def export_status(self, taskid):
        "export status"
        result = AsyncResult(taskid)
        if result is None or taskid not in session['taskids']:
            msg = _('The task status requested has expired or does not exist')
            flash(msg)
            log.info(msg)
            redirect(url(controller='accounts', action='index'))

        if result.ready():
            finished = True
            flash.pop_messages()
            if isinstance(result.result, Exception):
                msg = _('Error occured in processing %s') % result.result
                if c.user.is_superadmin:
                    flash_alert(msg)
                    log.info(msg)
                else:
                    flash_alert(_('Backend error occured during processing.'))
                    log.info(msg)
                redirect(url(controller='accounts', action='index'))
            results = dict(
                        f=True if not result.result['global_error'] else False,
                        id=taskid, global_error=result.result['global_error'])
            audit_log(c.user.username,
                    5, unicode(auditmsgs.ACCOUNTEXPORT_MSG), request.host,
                    request.remote_addr, arrow.utcnow().datetime)
        else:
            try:
                session['acexport-count'] += 1
            except KeyError:
                session['acexport-count'] = 1
            session.save()
            if (session['acexport-count'] >= 10 and
                result.state in ['PENDING', 'RETRY', 'FAILURE']):
                result.revoke()
                del session['acexport-count']
                session.save()
                msg = _('The export could not be processed, try again later')
                flash_alert(msg)
                log.info(msg)
                redirect(url(controller='accounts', action='index'))
            finished = False
            results = dict(f=None, global_error=None)

        c.finished = finished
        c.results = results
        c.success = result.successful()
        dwn = request.GET.get('d', None)
        if finished and (dwn and dwn == 'y'):
            response.content_type = 'text/csv'
            response.headers['Cache-Control'] = 'max-age=0'
            csvdata = result.result['f']
            disposition = 'attachment; filename=accounts-export-%s.csv' % \
                            taskid
            response.headers['Content-Disposition'] = str(disposition)
            response.headers['Content-Length'] = len(csvdata)
            return csvdata
        return self.render('/accounts/exportstatus.html')

    # pylint: disable-msg=R0201,W0613
    @ActionProtector(All(not_anonymous(), OnlyAdminUsers()))
    def setnum(self, format=None):
        "Set number of account items returned"
        num = check_num_param(request)

        if num and num in [10, 20, 50, 100]:
            session['accounts_num_items'] = num
            session.save()
        nextpage = request.headers.get('Referer', '/')
        if '://' in nextpage:
            from_url = urlparse(nextpage)
            nextpage = from_url[2]
        redirect(nextpage)
