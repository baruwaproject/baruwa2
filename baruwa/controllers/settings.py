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
"Settings controller"

import os
import logging

from urlparse import urlparse

from pylons import request, response, session, config, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from webhelpers import paginate
from pylons.i18n.translation import _
from sqlalchemy import desc
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError, DatabaseError
from repoze.what.predicates import not_anonymous
from repoze.what.plugins.pylonshq import ActionProtector
from repoze.what.plugins.pylonshq import ControllerProtector

from baruwa.lib.dates import now
from baruwa.lib.base import BaseController, render
from baruwa.lib.regex import CONFIG_RE
from baruwa.lib.auth.predicates import OwnsDomain
from baruwa.lib.auth.predicates import OnlySuperUsers
from baruwa.lib.auth.predicates import CanAccessAccount
from baruwa.lib.misc import check_num_param
from baruwa.lib.misc import convert_settings_to_json
from baruwa.lib.ssl import make_key_pair
from baruwa.lib.audit import audit_log
from baruwa.model.meta import Session
from baruwa.model.settings import Server, ConfigSettings
from baruwa.model.settings import DomSignature, UserSignature, DKIMKeys
from baruwa.tasks.settings import delete_sig, save_dom_sig, save_user_sig
from baruwa.tasks.settings import update_serial, save_dkim_key
from baruwa.tasks.settings import delete_dkim_key, reload_exim
from baruwa.lib.helpers import flash, flash_info, flash_alert
from baruwa.forms.settings import ServerForm, settings_forms
from baruwa.forms.settings import SigForm, global_settings_dict, DKIMForm
from baruwa.lib.audit.msgs.settings import *

log = logging.getLogger(__name__)

CONFIG_SECTIONS = {
    1: 'General Settings',
    2: 'Message Processing Settings',
    3: 'Virus checks Settings',
    4: 'Content checks Settings',
    5: 'Reporting Settings',
    6: 'Notice Settings',
    7: 'Spam checks Settings',
    8: 'Logging Settings'
}


@ControllerProtector(not_anonymous())
class SettingsController(BaseController):
    #@ActionProtector(not_anonymous())
    def __before__(self):
        "set context"
        BaseController.__before__(self)
        if self.identity:
            c.user = self.identity['user']
        else:
            c.user = None
        c.selectedtab = 'settings'

    def _get_server(self, serverid):
        "returns server object"
        try:
            server = Session.query(Server).get(serverid)
        except NoResultFound:
            server = None
        return server

    def _get_setting(self, server, name):
        "return a configsettings object"
        try:
            conf_setting = Session.query(ConfigSettings)\
                            .filter_by(
                                        server_id=server,
                                        internal=name
                            ).one()
        except NoResultFound:
            conf_setting = None
        return conf_setting

    def _get_domsign(self, sigid):
        "domain signature"
        try:
            sign = Session.query(DomSignature).get(sigid)
        except NoResultFound:
            sign = None
        return sign

    def _get_usrsign(self, sigid):
        "user signature"
        try:
            sign = Session.query(UserSignature).get(sigid)
        except NoResultFound:
            sign = None
        return sign

    @ActionProtector(OnlySuperUsers())
    def index(self, page=1, format=None):
        "Index"
        num_items = session.get('settings_num_items', 10)
        servers = Session.query(Server).filter(
                                        Server.hostname != 'default'
                                        ).order_by(desc('id')).all()
        items = paginate.Page(servers,
                            page=int(page),
                            items_per_page=num_items)
        if format == 'json':
            response.headers['Content-Type'] = 'application/json'
            data = convert_settings_to_json(items)
            return data

        c.page = items
        return render('/settings/index.html')

    @ActionProtector(OnlySuperUsers())
    def new_server(self):
        "Add scan server"
        c.form = ServerForm(request.POST, csrf_context=session)
        if request.POST and c.form.validate():
            try:
                server = Server(
                    hostname=c.form.hostname.data,
                    enabled=c.form.enabled.data
                )
                Session.add(server)
                Session.commit()
                info = HOSTADD_MSG % dict(n=server.hostname)
                audit_log(c.user.username,
                        3, unicode(info), request.host,
                        request.remote_addr, now())
                flash(_('The scanning server has been added'))
                redirect(url(controller='settings'))
            except IntegrityError:
                Session.rollback()
                flash_info(_('The server already exists'))

        return render('/settings/addserver.html')

    @ActionProtector(OnlySuperUsers())
    def edit_server(self, serverid):
        "Edit scan server"
        server = self._get_server(serverid)
        if not server:
            abort(404)

        c.form = ServerForm(request.POST, server, csrf_context=session)
        c.id = server.id
        if request.POST and c.form.validate():
            if (server.hostname != c.form.hostname.data or
                server.enabled != c.form.enabled.data):
                try:
                    server.hostname = c.form.hostname.data
                    server.enabled = c.form.enabled.data
                    Session.add(server)
                    Session.commit()
                    update_serial.delay()
                    info = HOSTUPDATE_MSG % dict(n=server.hostname)
                    audit_log(c.user.username,
                            2, unicode(info), request.host,
                            request.remote_addr, now())
                    flash(_('The scanning server has been updated'))
                except IntegrityError:
                    Session.rollback()
                    flash(_('Update of server failed'))
            else:
                flash_info(_('No changes were made to the server'))
            redirect(url(controller='settings'))
        return render('/settings/editserver.html')

    @ActionProtector(OnlySuperUsers())
    def delete_server(self, serverid):
        "Delete a scan server"
        server = self._get_server(serverid)
        if not server:
            abort(404)

        c.form = ServerForm(request.POST, server, csrf_context=session)
        c.id = server.id
        if request.POST and c.form.validate():
            hostname = server.hostname
            Session.delete(server)
            Session.commit()
            update_serial.delay()
            info = HOSTDELETE_MSG % dict(n=hostname)
            audit_log(c.user.username,
                    4, unicode(info), request.host,
                    request.remote_addr, now())
            flash(_('The scanning server has been deleted'))
            redirect(url(controller='settings'))
        return render('/settings/deleteserver.html')

    @ActionProtector(OnlySuperUsers())
    def section(self, serverid=1, sectionid='1'):
        "Settings section"
        server = self._get_server(serverid)
        if not server:
            abort(404)

        if not int(sectionid) in CONFIG_SECTIONS:
            abort(404)

        c.serverid = serverid
        c.sectionid = sectionid
        c.scanner = server
        c.sections = CONFIG_SECTIONS
        c.form = settings_forms[sectionid](request.POST, csrf_context=session)
        if not request.POST:
            for field in c.form:
                if (sectionid == '1' and '_' in field.name
                    and not field.name == 'csrf_token'):
                    internal = global_settings_dict[field.name]
                else:
                    internal = field.name
                conf = self._get_setting(serverid, internal)
                if conf:
                    attr = getattr(c.form, field.name)
                    attr.data = conf.value

        updated = None
        if request.POST and c.form.validate():
            for field in c.form:
                if field.data and not field.name == 'csrf_token':
                    if sectionid == '1':
                        if '_' in field.name:
                            external = global_settings_dict[field.name]
                            internal = external
                        else:
                            external = CONFIG_RE.sub(u'', unicode(field.label.text))
                            internal = field.name
                    else:
                        external = CONFIG_RE.sub(u'', unicode(field.label.text))
                        internal = field.name
                    conf = self._get_setting(serverid, internal)
                    if conf is None:
                        if field.data != field.default:
                            conf = ConfigSettings(
                                        internal=internal,
                                        external=external,
                                        section=sectionid
                                    )
                            conf.value = field.data
                            conf.server = server
                            updated = True
                            Session.add(conf)
                            Session.commit()
                            subs = dict(svr=server.hostname,
                                        s=external,
                                        a=conf.value)
                            info = HOSTSETTING_MSG % subs
                            audit_log(c.user.username,
                                    3, unicode(info), request.host,
                                    request.remote_addr, now())
                    else:
                        if conf.value != field.data:
                            conf.value = field.data
                            updated = True
                            Session.add(conf)
                            Session.commit()
                            subs = dict(svr=conf.server.hostname,
                                        s=external,
                                        a=conf.value)
                            info = HOSTSETTING_MSG % subs
                            audit_log(c.user.username,
                                    2, unicode(info), request.host,
                                    request.remote_addr, now())
            if updated:
                flash(_('%(settings)s updated') % dict(
                settings=CONFIG_SECTIONS[int(sectionid)]))
                update_serial.delay()
            else:
                flash_info(_('No configuration changes made'))
            #redirect(url('settings-scanner', serverid=serverid))
        return render('/settings/section.html')

    @ActionProtector(OwnsDomain())
    def domain_settings(self, domainid):
        "Domain settings landing"
        domain = self._get_domain(domainid)
        if not domain:
            abort(404)
        c.domain = domain
        return render('/settings/domain_settings.html')

    @ActionProtector(OwnsDomain())
    def domain_dkim(self, domainid):
        "Domain DKIM settings"
        domain = self._get_domain(domainid)
        if not domain:
            abort(404)
        c.domain = domain
        return render('/settings/domain_dkim.html')

    @ActionProtector(OwnsDomain())
    def domain_dkim_generate(self, domainid):
        "Domain DKIM generate keys"
        domain = self._get_domain(domainid)
        if not domain:
            abort(404)
        pub_key, pri_key = make_key_pair()
        if domain.dkimkeys:
            dkimkeys = domain.dkimkeys[0]
        else:
            dkimkeys = DKIMKeys()
        dkimkeys.pub_key = pub_key
        dkimkeys.pri_key = pri_key
        try:
            if domain.dkimkeys:
                domain.dkimkeys[0] = dkimkeys
            else:
                domain.dkimkeys.append(dkimkeys)
            Session.add(dkimkeys)
            Session.add(domain)
            Session.commit()
            info = DKIMGEN_MSG % dict(d=domain.name)
            audit_log(c.user.username,
                    3, unicode(info), request.host,
                    request.remote_addr, now())
            flash(_('DKIM keys successfully generated'))
        except DatabaseError:
            flash_alert(_('Generation of DKIM keys failed'))
        redirect(url('domain-dkim', domainid=domain.id))

    @ActionProtector(OwnsDomain())
    def domain_dkim_enable(self, domainid):
        "Enable or disable DKIM signing"
        domain = self._get_domain(domainid)
        if not domain or not domain.dkimkeys:
            abort(404)
        c.form = DKIMForm(request.POST, domain.dkimkeys[0],
                            csrf_context=session)
        if request.POST and c.form.validate():
            dkimkeys = domain.dkimkeys[0]
            if dkimkeys.enabled != c.form.enabled.data:
                dkimkeys.enabled = c.form.enabled.data
                Session.add(dkimkeys)
                Session.commit()
                if c.form.enabled.data:
                    state = _('enabled')
                    save_dkim_key.apply_async(args=[domain.name,
                                            dkimkeys.pri_key],
                                            queue='msbackend')
                    info = DKIMENABLED_MSG % dict(d=domain.name)
                else:
                    info = DKIMDISABLED_MSG % dict(d=domain.name)
                    delete_dkim_key.apply_async(args=[domain.name],
                                            queue='msbackend')
                    state = _('disabled')
                audit_log(c.user.username,
                        2, unicode(info), request.host,
                        request.remote_addr, now())
                reload_exim.delay()
                flash(_('DKIM signing for: %s has been %s') %
                        (domain.name, state))
            else:
                flash(_('DKIM signing status: No changes made'))
            redirect(url('domain-dkim', domainid=domain.id))
        c.domain = domain
        return render('/settings/domain_dkim_enable.html')

    @ActionProtector(OwnsDomain())
    def domain_sigs(self, domainid):
        "Domain signatures landing"
        domain = self._get_domain(domainid)
        if not domain:
            abort(404)
        c.domain = domain
        return render('/settings/domain_sigs.html')

    @ActionProtector(OwnsDomain())
    def domain_rules(self, domainid):
        "Domain rulesets"
        domain = self._get_domain(domainid)
        if not domain:
            abort(404)
        c.domain = domain
        return render('/settings/domain_rules.html')

    @ActionProtector(OwnsDomain())
    def add_domain_sigs(self, domainid):
        "Add domain signature"
        domain = self._get_domain(domainid)
        if not domain:
            abort(404)

        c.form = SigForm(request.POST, csrf_context=session)
        if request.POST and c.form.validate():
            try:
                sig = DomSignature()
                for field in c.form:
                    if field.name != 'csrf_token':
                        setattr(sig, field.name, field.data)
                domain.signatures.append(sig)
                Session.add(sig)
                Session.add(domain)
                Session.commit()
                save_dom_sig.apply_async(args=[sig.id], queue='msbackend')
                info = ADDDOMSIG_MSG % dict(d=domain.name)
                audit_log(c.user.username,
                        3, unicode(info), request.host,
                        request.remote_addr, now())
                flash(_('The signature has been created'))
                redirect(url('domain-settings-sigs', domainid=domainid))
            except IntegrityError:
                Session.rollback()
                flash(_('This signature type already exists'))
        c.domain = domain
        return render('/settings/domain_addsig.html')

    @ActionProtector(OwnsDomain())
    def edit_domain_sigs(self, sigid):
        "Edit domain signatures"
        sign = self._get_domsign(sigid)
        if not sign:
            abort(404)

        c.form = SigForm(request.POST, sign, csrf_context=session)
        del c.form['signature_type']
        if request.POST and c.form.validate():
            try:
                updated = False
                for field in c.form:
                    if (field.name != 'csrf_token' and
                        field.data != getattr(sign, field.name)):
                        updated = True
                        setattr(sign, field.name, field.data)
                if updated:
                    Session.add(sign)
                    Session.commit()
                    save_dom_sig.apply_async(args=[sigid], queue='msbackend')
                    info = UPDATEDOMSIG_MSG % dict(d=sign.domain.name)
                    audit_log(c.user.username,
                            2, unicode(info), request.host,
                            request.remote_addr, now())
                    flash(_('The signature has been updated'))
                else:
                    flash(_('No changes made, signature not updated'))
                redirect(url('domain-settings-sigs', domainid=sign.domain_id))
            except IntegrityError:
                Session.rollback()
                flash(_('Error occured updating the signature'))
        c.sign = sign
        return render('/settings/domain_editsig.html')

    @ActionProtector(OwnsDomain())
    def delete_domain_sigs(self, sigid):
        "Delete domain signature"
        sign = self._get_domsign(sigid)
        if not sign:
            abort(404)

        c.form = SigForm(request.POST, sign, csrf_context=session)
        del c.form['signature_type']
        if request.POST and c.form.validate():
            domain_id = sign.domain_id
            domain_name = sign.domain.name
            files = []
            basedir = config.get('ms.signatures.base',
                        '/etc/MailScanner/signatures')
            if sign.signature_type == 1:
                domain = self._get_domain(domain_id)
                if domain:
                    sigfile = os.path.join(basedir,
                                            'domains',
                                            domain.name,
                                            'sig.txt')
                    files.append(sigfile)
            else:
                if sign.image:
                    imgfile = os.path.join(basedir,
                                            'domains',
                                            domain.name,
                                            sign.image.name)
                    files.append(imgfile)
                sigfile = os.path.join(basedir, 'domains',
                                        domain.name,
                                        'sig.html')
                files.append(sigfile)
            Session.delete(sign)
            Session.commit()
            delete_sig.apply_async(args=[files], queue='msbackend')
            info = DELETEDOMSIG_MSG % dict(d=domain_name)
            audit_log(c.user.username,
                    4, unicode(info), request.host,
                    request.remote_addr, now())
            flash(_('The signature has been deleted'))
            redirect(url('domain-settings-sigs', domainid=domain_id))
        c.sign = sign
        return render('/settings/domain_deletesig.html')

    @ActionProtector(CanAccessAccount())
    def add_account_sigs(self, userid):
        "Add account signature"
        account = self._get_user(userid)
        if not account:
            abort(404)

        c.form = SigForm(request.POST, csrf_context=session)
        if request.POST and c.form.validate():
            try:
                sig = UserSignature()
                for field in c.form:
                    if field.name != 'csrf_token':
                        setattr(sig, field.name, field.data)
                account.signatures.append(sig)
                Session.add(sig)
                Session.add(account)
                Session.commit()
                save_user_sig.apply_async(args=[sig.id], queue='msbackend')
                info = ADDACCSIG_MSG % dict(u=account.username)
                audit_log(c.user.username,
                        3, unicode(info), request.host,
                        request.remote_addr, now())
                flash(_('The signature has been created'))
                redirect(url('account-detail', userid=userid))
            except IntegrityError:
                Session.rollback()
                flash(_('This signature type already exists'))
        c.account = account
        return render('/settings/account_addsig.html')

    @ActionProtector(CanAccessAccount())
    def edit_account_sigs(self, sigid):
        "Edit account signatures"
        sign = self._get_usrsign(sigid)
        if not sign:
            abort(404)

        c.form = SigForm(request.POST, sign, csrf_context=session)
        del c.form['signature_type']
        if request.POST and c.form.validate():
            try:
                updated = False
                for field in c.form:
                    if (field.name != 'csrf_token' and
                        field.data != getattr(sign, field.name)):
                        updated = True
                        setattr(sign, field.name, field.data)
                if updated:
                    Session.add(sign)
                    Session.commit()
                    save_user_sig.apply_async(args=[sigid], queue='msbackend')
                    info = UPDATEACCSIG_MSG % dict(u=sign.user.username)
                    audit_log(c.user.username,
                            2, unicode(info), request.host,
                            request.remote_addr, now())
                    flash(_('The signature has been updated'))
                else:
                    flash(_('No changes made, signature not updated'))
                redirect(url('account-detail', userid=sign.user_id))
            except IntegrityError:
                Session.rollback()
                flash(_('Error occured updating the signature'))
        c.sign = sign
        return render('/settings/account_editsig.html')

    @ActionProtector(CanAccessAccount())
    def delete_account_sigs(self, sigid):
        "Delete account signatures"
        sign = self._get_usrsign(sigid)
        if not sign:
            abort(404)

        c.form = SigForm(request.POST, sign, csrf_context=session)
        del c.form['signature_type']
        if request.POST and c.form.validate():
            user_id = sign.user_id
            user_name = sign.user.username
            files = []
            basedir = config.get('ms.signatures.base',
                                '/etc/MailScanner/signatures')
            if sign.signature_type == 1:
                user = self._get_user(user_id)
                if user:
                    sigfile = os.path.join(basedir,
                                            'users',
                                            user.username,
                                            'sig.txt')
                    files.append(sigfile)
            else:
                if sign.image:
                    imgfile = os.path.join(basedir,
                                            'users',
                                            user.username,
                                            sign.image.name)
                    files.append(imgfile)
                sigfile = os.path.join(basedir, 'users',
                                        user.username,
                                        'sig.html')
                files.append(sigfile)
            Session.delete(sign)
            Session.commit()
            delete_sig.apply_async(args=[files], queue='msbackend')
            info = DELETEACCSIG_MSG % dict(u=user_name)
            audit_log(c.user.username,
                    4, unicode(info), request.host,
                    request.remote_addr, now())
            flash(_('The signature has been deleted'))
            redirect(url('account-detail', userid=user_id))
        c.sign = sign
        return render('/settings/account_deletesig.html')

    @ActionProtector(OnlySuperUsers())
    def setnum(self, format=None):
        "Set number of items returned"
        num = check_num_param(request)

        if num and num in [10, 20, 50, 100]:
            session['settings_num_items'] = num
            session.save()
        nextpage = request.headers.get('Referer', '/')
        if '://' in nextpage:
            from_url = urlparse(nextpage)
            nextpage = from_url[2]
        redirect(nextpage)

