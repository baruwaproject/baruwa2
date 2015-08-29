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
"Settings controller"

import os
import logging

import arrow

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

from baruwa.lib.mq import FANOUT_XCHG
from baruwa.lib.base import BaseController
from baruwa.lib.regex import CONFIG_RE
from baruwa.lib.auth.predicates import OwnsDomain
from baruwa.lib.auth.predicates import OnlySuperUsers
from baruwa.lib.auth.predicates import CanAccessAccount
from baruwa.lib.misc import check_num_param
from baruwa.lib.misc import convert_settings_to_json
from baruwa.lib.crypto import make_key_pair
from baruwa.lib.audit import audit_log
from baruwa.model.meta import Session
from baruwa.lib.api import POLICY_URL_MAP, add_policy, get_policy, \
    delete_policy, update_policy, get_policy_rules, add_rule, get_rule, \
    update_rule, delete_rule, clone_policy, process_default_rules, \
    get_policy_setting, get_policies, set_policy_form_opts, \
    save_policy_settings, get_domain, get_domain_policy_settings, \
    save_domain_policy_settings, get_mta_settings, create_mta_setting, \
    update_mta_setting, delete_mta_setting, get_mta_setting, \
    get_local_scores, get_local_score, update_local_score
from baruwa.model.settings import Server, ConfigSettings
from baruwa.model.settings import DomSignature, UserSignature, DKIMKeys
from baruwa.tasks.settings import delete_sig, save_dom_sig, save_user_sig
from baruwa.tasks.settings import update_serial, save_dkim_key
from baruwa.tasks.settings import delete_dkim_key, reload_exim
from baruwa.lib.helpers import flash, flash_info, flash_alert
from baruwa.forms.settings import AddRuleForm, PolicySettingsForm, \
    ARCHIVE_RULE_ACTIONS, MTASettingsForm, LocalScoreForm
from baruwa.forms.settings import ServerForm, settings_forms, PolicyForm
from baruwa.forms.settings import SigForm, global_settings_dict, DKIMForm
from baruwa.lib.audit.msgs import settings as auditmsgs
from baruwa.tasks.settings import (create_text_sigs, create_html_sigs,
    create_sig_imgs, create_sig_img_names, create_sign_clean,
    create_ms_settings)

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

POLICY_NAME = {'1': _('Archive File Policies'),
                    '2': _('Archive Mime Policies'),
                    '3': _('File Policies'),
                    '4': _('Mime Policies')}

POLICY_TYPES = {1: 'archive-file-policy', 2: 'archive-mime-policy',
                3: 'file-policy', 4: 'mime-policy'}

MTA_NAME = {1: _('Empty Reply Checks Exemptions'),
            2: _('Subject Block List'),
            3: _('TLS/SSL Exemptions'),
            4: _('Anonymizer List'),
            5: _('Anti-Virus Checks Exemptions'),
            6: _('DKIM Checks Exemptions'),
            7: _('DNSBL Checks Exemptions'),
            8: _('System Signature Exemptions'),
            9: _('Ratelimit Exemptions'),
            10: _('SPF Checks Exemptions')}


def check_field(field):
    """Check and validate field"""
    if field.name == 'virusscanners' and len(field.data) > 1:
        if 'auto' in field.data:
            field.data.remove('auto')
        if 'none' in field.data:
            field.data.remove('none')


def get_check_value(field_type, stored_val):
    """Return the correct data type"""
    if field_type == 'SelectMultipleField':
        return stored_val.strip('{}').split(',')
    else:
        return stored_val


def backend_sig_update(signature_type):
    "Perform backend updates"
    if int(signature_type) == 1:
        # text
        create_text_sigs.apply_async(exchange=FANOUT_XCHG)
    else:
        # html
        create_html_sigs.apply_async(exchange=FANOUT_XCHG)
        create_sig_imgs.apply_async(exchange=FANOUT_XCHG)
        create_sig_img_names.apply_async(exchange=FANOUT_XCHG)
    create_sign_clean.apply_async(exchange=FANOUT_XCHG)


@ControllerProtector(not_anonymous())
class SettingsController(BaseController):
    """Settings controller"""
    # @ActionProtector(not_anonymous())
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
        servers = Session\
                    .query(Server)\
                    .filter(Server.hostname != 'default')\
                    .order_by(desc('id')).all()
        items = paginate.Page(servers,
                            page=int(page),
                            items_per_page=num_items)
        if format == 'json':
            response.headers['Content-Type'] = 'application/json'
            data = convert_settings_to_json(items)
            return data

        c.page = items
        return self.render('/settings/index.html')

    @ActionProtector(OnlySuperUsers())
    def new_server(self):
        "Add scan server"
        c.form = ServerForm(request.POST, csrf_context=session)
        if request.method == 'POST' and c.form.validate():
            try:
                server = Server(
                    hostname=c.form.hostname.data,
                    enabled=c.form.enabled.data
                )
                Session.add(server)
                Session.commit()
                info = auditmsgs.HOSTADD_MSG % dict(n=server.hostname)
                audit_log(c.user.username,
                        3, unicode(info), request.host,
                        request.remote_addr, arrow.utcnow().datetime)
                flash(_('The scanning server has been added'))
                redirect(url(controller='settings'))
            except IntegrityError:
                Session.rollback()
                flash_info(_('The server already exists'))

        return self.render('/settings/addserver.html')

    @ActionProtector(OnlySuperUsers())
    def edit_server(self, serverid):
        "Edit scan server"
        server = self._get_server(serverid)
        if not server:
            abort(404)

        c.form = ServerForm(request.POST, server, csrf_context=session)
        c.id = server.id
        if request.method == 'POST' and c.form.validate():
            if (server.hostname != c.form.hostname.data or
                server.enabled != c.form.enabled.data):
                try:
                    server.hostname = c.form.hostname.data
                    server.enabled = c.form.enabled.data
                    Session.add(server)
                    Session.commit()
                    update_serial.delay()
                    info = auditmsgs.HOSTUPDATE_MSG % dict(n=server.hostname)
                    audit_log(c.user.username,
                            2, unicode(info), request.host,
                            request.remote_addr, arrow.utcnow().datetime)
                    flash(_('The scanning server has been updated'))
                except IntegrityError:
                    Session.rollback()
                    msg = _('Update of scanning server failed')
                    flash(msg)
                    log.info(msg)
            else:
                msg = _('No changes were made to the scanning server')
                flash_info(msg)
                log.info(msg)
            redirect(url(controller='settings'))
        return self.render('/settings/editserver.html')

    @ActionProtector(OnlySuperUsers())
    def delete_server(self, serverid):
        "Delete a scan server"
        server = self._get_server(serverid)
        if not server:
            abort(404)

        c.form = ServerForm(request.POST, server, csrf_context=session)
        c.id = server.id
        if request.method == 'POST' and c.form.validate():
            hostname = server.hostname
            Session.delete(server)
            Session.commit()
            update_serial.delay()
            info = auditmsgs.HOSTDELETE_MSG % dict(n=hostname)
            audit_log(c.user.username,
                    4, unicode(info), request.host,
                    request.remote_addr, arrow.utcnow().datetime)
            flash(_('The scanning server has been deleted'))
            redirect(url(controller='settings'))
        return self.render('/settings/deleteserver.html')

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
        if not request.method == 'POST':
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
        if request.method == 'POST' and c.form.validate():
            for field in c.form:
                if field.type == 'SelectMultipleField' or \
                        (field.data and not field.name == 'csrf_token'):
                    if sectionid == '1':
                        if '_' in field.name:
                            external = global_settings_dict[field.name]
                            internal = external
                        else:
                            external = CONFIG_RE.sub(u'',
                                        unicode(field.label.text))
                            internal = field.name
                    else:
                        external = CONFIG_RE.sub(u'',
                                    unicode(field.label.text))
                        internal = field.name
                    conf = self._get_setting(serverid, internal)
                    if conf is None:
                        if (field.type == 'SelectMultipleField' and
                            len(field.data) and field.data != field.default)\
                            or (field.type != 'SelectMultipleField' and
                                field.data != field.default):
                            check_field(field)
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
                            info = auditmsgs.HOSTSETTING_MSG % subs
                            audit_log(c.user.username,
                                    3, unicode(info), request.host,
                                    request.remote_addr,
                                    arrow.utcnow().datetime)
                    else:
                        subs = dict(svr=conf.server.hostname,
                                    s=external,
                                    a=conf.value)
                        info = auditmsgs.HOSTSETTING_MSG % subs
                        check_value = get_check_value(field.type, conf.value)
                        if check_value != field.data:
                            # stored value not equal to updated value
                            if (field.type == 'SelectMultipleField' and
                                len(field.data) and
                                field.data != field.default) or \
                                (field.type != 'SelectMultipleField' and
                                field.data != field.default):
                                # not a default, we can update
                                check_field(field)
                                conf.value = field.data
                                updated = True
                                Session.add(conf)
                                Session.commit()
                                audit_log(c.user.username,
                                    2, unicode(info), request.host,
                                    request.remote_addr,
                                    arrow.utcnow().datetime)
                            else:
                                # is the default lets delete the stored value
                                Session.delete(conf)
                                Session.commit()
                                updated = True
                                audit_log(c.user.username,
                                        4, unicode(info), request.host,
                                        request.remote_addr,
                                        arrow.utcnow().datetime)

            if updated:
                flash(_('%(settings)s updated') % dict(
                    settings=CONFIG_SECTIONS[int(sectionid)]))
                create_ms_settings.apply_async(exchange=FANOUT_XCHG)
                update_serial.delay()
            else:
                flash_info(_('No configuration changes made'))
            # redirect(url('settings-scanner', serverid=serverid))
        elif request.method == 'POST' and not c.form.validate():
            msg = _("Error detected, check the settings below")
            flash_alert(msg)
            log.info(msg)
        return self.render('/settings/section.html')

    @ActionProtector(OwnsDomain())
    def domain_settings(self, domainid):
        "Domain settings landing"
        domain = self._get_domain(domainid)
        if not domain:
            abort(404)
        c.domain = domain
        return self.render('/settings/domain_settings.html')

    @ActionProtector(OwnsDomain())
    def domain_dkim(self, domainid):
        "Domain DKIM settings"
        domain = self._get_domain(domainid)
        if not domain:
            abort(404)
        c.domain = domain
        return self.render('/settings/domain_dkim.html')

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
            info = auditmsgs.DKIMGEN_MSG % dict(d=domain.name)
            audit_log(c.user.username,
                    3, unicode(info), request.host,
                    request.remote_addr, arrow.utcnow().datetime)
            flash(_('DKIM keys successfully generated'))
        except DatabaseError:
            msg = _('Generation of DKIM keys failed')
            flash_alert(msg)
            log.info(msg)
        redirect(url('domain-dkim', domainid=domain.id))

    @ActionProtector(OwnsDomain())
    def domain_dkim_enable(self, domainid):
        "Enable or disable DKIM signing"
        domain = self._get_domain(domainid)
        if not domain or not domain.dkimkeys:
            abort(404)
        c.form = DKIMForm(request.POST, domain.dkimkeys[0],
                            csrf_context=session)
        if request.method == 'POST' and c.form.validate():
            dkimkeys = domain.dkimkeys[0]
            if dkimkeys.enabled != c.form.enabled.data:
                dkimkeys.enabled = c.form.enabled.data
                Session.add(dkimkeys)
                Session.commit()
                if c.form.enabled.data:
                    state = _('enabled')
                    save_dkim_key.apply_async(args=[domain.name,
                                            dkimkeys.pri_key],
                                            exchange=FANOUT_XCHG)
                    info = auditmsgs.DKIMENABLED_MSG % dict(d=domain.name)
                else:
                    info = auditmsgs.DKIMDISABLED_MSG % dict(d=domain.name)
                    delete_dkim_key.apply_async(args=[domain.name],
                                            exchange=FANOUT_XCHG)
                    state = _('disabled')
                audit_log(c.user.username,
                        2, unicode(info), request.host,
                        request.remote_addr, arrow.utcnow().datetime)
                reload_exim.apply_async(exchange=FANOUT_XCHG)
                flash(_('DKIM signing for: %s has been %s') %
                        (domain.name, state))
            else:
                flash(_('DKIM signing status: No changes made'))
            redirect(url('domain-dkim', domainid=domain.id))
        c.domain = domain
        return self.render('/settings/domain_dkim_enable.html')

    @ActionProtector(OwnsDomain())
    def domain_sigs(self, domainid):
        "Domain signatures landing"
        domain = self._get_domain(domainid)
        if not domain:
            abort(404)
        c.domain = domain
        return self.render('/settings/domain_sigs.html')

    @ActionProtector(OwnsDomain())
    def domain_rules(self, domainid):
        "Domain rulesets"
        domain = self._get_domain(domainid)
        if not domain:
            abort(404)
        c.domain = domain
        return self.render('/settings/domain_rules.html')

    @ActionProtector(OwnsDomain())
    def add_domain_sigs(self, domainid):
        "Add domain signature"
        domain = self._get_domain(domainid)
        if not domain:
            abort(404)

        c.form = SigForm(request.POST, csrf_context=session)
        if request.method == 'POST' and c.form.validate():
            try:
                sig = DomSignature()
                for field in c.form:
                    if field.name != 'csrf_token':
                        setattr(sig, field.name, field.data)
                domain.signatures.append(sig)
                Session.add(sig)
                Session.add(domain)
                Session.commit()
                save_dom_sig.apply_async(args=[sig.id], exchange=FANOUT_XCHG)
                backend_sig_update(c.form.signature_type.data)
                info = auditmsgs.ADDDOMSIG_MSG % dict(d=domain.name)
                audit_log(c.user.username,
                        3, unicode(info), request.host,
                        request.remote_addr, arrow.utcnow().datetime)
                flash(_('The signature has been created'))
                redirect(url('domain-settings-sigs', domainid=domainid))
            except IntegrityError:
                Session.rollback()
                msg = _('This signature type already exists')
                flash(msg)
                log.info(msg)
        c.domain = domain
        return self.render('/settings/domain_addsig.html')

    @ActionProtector(OwnsDomain())
    def edit_domain_sigs(self, sigid):
        "Edit domain signatures"
        sign = self._get_domsign(sigid)
        if not sign:
            abort(404)

        c.form = SigForm(request.POST, sign, csrf_context=session)
        signature_type = c.form.signature_type.data
        del c.form['signature_type']
        if request.method == 'POST' and c.form.validate():
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
                    save_dom_sig\
                        .apply_async(args=[sigid], exchange=FANOUT_XCHG)
                    backend_sig_update(signature_type)
                    info = auditmsgs.UPDATEDOMSIG_MSG % \
                            dict(d=sign.domain.name)
                    audit_log(c.user.username,
                            2, unicode(info), request.host,
                            request.remote_addr, arrow.utcnow().datetime)
                    flash(_('The signature has been updated'))
                else:
                    flash(_('No changes made, signature not updated'))
                redirect(url('domain-settings-sigs', domainid=sign.domain_id))
            except IntegrityError:
                Session.rollback()
                msg = _('Error occured updating the signature')
                flash(msg)
                log.info(msg)
        c.sign = sign
        return self.render('/settings/domain_editsig.html')

    @ActionProtector(OwnsDomain())
    def delete_domain_sigs(self, sigid):
        "Delete domain signature"
        sign = self._get_domsign(sigid)
        if not sign:
            abort(404)

        c.form = SigForm(request.POST, sign, csrf_context=session)
        signature_type = c.form.signature_type.data
        del c.form['signature_type']
        if request.method == 'POST' and c.form.validate():
            domain = sign.domain
            files = []
            basedir = config.get('ms.signatures.base',
                        '/etc/MailScanner/signatures')
            if sign.signature_type == 1:
                sigfile = os.path.join(basedir,
                                        'domains',
                                        domain.name,
                                        'sig.txt')
                files.append(sigfile)
            else:
                if sign.image:
                    for imgobj in sign.image:
                        imgfile = os.path.join(basedir,
                                            'domains',
                                            domain.name,
                                            imgobj.name)
                        files.append(imgfile)
                sigfile = os.path.join(basedir, 'domains',
                                        domain.name,
                                        'sig.html')
                files.append(sigfile)
            Session.delete(sign)
            Session.commit()
            if not domain.signatures:
                sigfile = os.path.join(basedir, 'domains', domain.name)
                files.append(sigfile)
                for alias in domain.aliases:
                    sigfile = os.path.join(basedir, 'domains', alias.name)
                    files.append(sigfile)
            delete_sig.apply_async(args=[files], exchange=FANOUT_XCHG)
            backend_sig_update(signature_type)
            info = auditmsgs.DELETEDOMSIG_MSG % dict(d=domain.name)
            audit_log(c.user.username,
                    4, unicode(info), request.host,
                    request.remote_addr, arrow.utcnow().datetime)
            flash(_('The signature has been deleted'))
            redirect(url('domain-settings-sigs', domainid=domain.id))
        c.sign = sign
        return self.render('/settings/domain_deletesig.html')

    @ActionProtector(CanAccessAccount())
    def add_account_sigs(self, userid):
        "Add account signature"
        account = self._get_user(userid)
        if not account:
            abort(404)

        c.form = SigForm(request.POST, csrf_context=session)
        if request.method == 'POST' and c.form.validate():
            try:
                sig = UserSignature()
                for field in c.form:
                    if field.name != 'csrf_token':
                        setattr(sig, field.name, field.data)
                account.signatures.append(sig)
                Session.add(sig)
                Session.add(account)
                Session.commit()
                save_user_sig.apply_async(args=[sig.id], exchange=FANOUT_XCHG)
                backend_sig_update(c.form.signature_type.data)
                info = auditmsgs.ADDACCSIG_MSG % dict(u=account.username)
                audit_log(c.user.username,
                        3, unicode(info), request.host,
                        request.remote_addr, arrow.utcnow().datetime)
                flash(_('The signature has been created'))
                redirect(url('account-detail', userid=userid))
            except IntegrityError:
                Session.rollback()
                flash(_('This signature type already exists'))
        c.account = account
        return self.render('/settings/account_addsig.html')

    @ActionProtector(CanAccessAccount())
    def edit_account_sigs(self, sigid):
        "Edit account signatures"
        sign = self._get_usrsign(sigid)
        if not sign:
            abort(404)

        c.form = SigForm(request.POST, sign, csrf_context=session)
        signature_type = c.form.signature_type.data
        del c.form['signature_type']
        if request.method == 'POST' and c.form.validate():
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
                    save_user_sig\
                        .apply_async(args=[sigid], exchange=FANOUT_XCHG)
                    backend_sig_update(signature_type)
                    info = auditmsgs.UPDATEACCSIG_MSG % dict(
                                                        u=sign.user.username)
                    audit_log(c.user.username,
                            2, unicode(info), request.host,
                            request.remote_addr, arrow.utcnow().datetime)
                    flash(_('The signature has been updated'))
                else:
                    flash(_('No changes made, signature not updated'))
                redirect(url('account-detail', userid=sign.user_id))
            except IntegrityError:
                Session.rollback()
                msg = _('Error occured updating the signature')
                flash(msg)
                log.info(msg)
        c.sign = sign
        return self.render('/settings/account_editsig.html')

    @ActionProtector(CanAccessAccount())
    def delete_account_sigs(self, sigid):
        "Delete account signatures"
        sign = self._get_usrsign(sigid)
        if not sign:
            abort(404)

        c.form = SigForm(request.POST, sign, csrf_context=session)
        signature_type = c.form.signature_type.data
        del c.form['signature_type']
        if request.method == 'POST' and c.form.validate():
            user = sign.user
            files = []
            basedir = config.get('ms.signatures.base',
                                '/etc/MailScanner/signatures')
            if sign.signature_type == 1:
                sigfile = os.path.join(basedir, 'users',
                                        user.username,
                                        'sig.txt')
                files.append(sigfile)
            else:
                if sign.image:
                    for imgobj in sign.image:
                        imgfile = os.path.join(basedir,
                                                'users',
                                                user.username,
                                                imgobj.name)
                        files.append(imgfile)
                sigfile = os.path.join(basedir, 'users',
                                        user.username,
                                        'sig.html')
                files.append(sigfile)
            Session.delete(sign)
            Session.commit()
            if not user.signatures:
                sigfile = os.path.join(basedir, 'users', user.username)
                files.append(sigfile)
                for alias in user.addresses:
                    sigfile = os.path.join(basedir, 'users', alias.address)
                    files.append(sigfile)
            delete_sig.apply_async(args=[files], exchange=FANOUT_XCHG)
            backend_sig_update(signature_type)
            info = auditmsgs.DELETEACCSIG_MSG % dict(u=user.username)
            audit_log(c.user.username,
                    4, unicode(info), request.host,
                    request.remote_addr, arrow.utcnow().datetime)
            flash(_('The signature has been deleted'))
            redirect(url('account-detail', userid=user.id))
        c.sign = sign
        return self.render('/settings/account_deletesig.html')

    @ActionProtector(OnlySuperUsers())
    def rulesets(self):
        """Rulesets"""
        return self.render('/settings/rulesets.html')

    @ActionProtector(OnlySuperUsers())
    def global_policies(self):
        """Set Global policies"""
        settings = get_policy_setting()
        if settings:
            c.form = PolicySettingsForm(request.POST, settings,
                                        csrf_context=session)
        else:
            c.form = PolicySettingsForm(request.POST, csrf_context=session)
        set_policy_form_opts(c.form)
        if request.method == 'POST' and c.form.validate():
            save_policy_settings(c.form, settings, c.user, request.host,
                        request.remote_addr)
            flash(_("The Global Policy Settings have been saved"))
        return self.render('/settings/policy_settings.html')

    @ActionProtector(OnlySuperUsers())
    def domain_policies(self, domain_id):
        """Set Domain Content protection policies"""
        domain = get_domain(domain_id, c.user)
        if not domain:
            abort(404)
        settings = get_domain_policy_settings(domain_id)
        c.domain_id = domain.id
        c.domain_name = domain.name
        if settings:
            c.form = PolicySettingsForm(request.POST, settings,
                                        csrf_context=session)
        else:
            c.form = PolicySettingsForm(request.POST, csrf_context=session)
        set_policy_form_opts(c.form)
        if request.method == 'POST' and c.form.validate():
            save_domain_policy_settings(c.form, settings, domain_id, c.user,
                        request.host, request.remote_addr)
            flash(_("The Domain Policy Settings have been saved"))
        return self.render('/settings/policy_domain_settings.html')

    @ActionProtector(OnlySuperUsers())
    def policy_landing(self, policy_type, page=1):
        """Policy landing page"""
        c.policy_type = policy_type
        num_items = session.get('settings_num_items', 10)
        policies = get_policies(c.policy_type)
        items = paginate.Page(policies,
                            page=int(page),
                            items_per_page=num_items)
        c.page = items
        c.policy = POLICY_TYPES[int(c.policy_type)]
        c.policy_name = POLICY_NAME[str(c.policy_type)]
        return self.render('/settings/policy.html')

    @ActionProtector(OnlySuperUsers())
    def add_policy(self, policy_type):
        """Add a Policy"""
        if int(policy_type) not in [1, 2, 3, 4]:
            flash(_('The requested policy type does not exist'))
            redirect(url('settings-rulesets'))
        c.policy_type = policy_type
        c.POLICY_NAME = POLICY_NAME
        c.POLICY_URL_MAP = POLICY_URL_MAP
        c.form = PolicyForm(request.POST, csrf_context=session)
        if request.method != 'POST':
            c.form.name.data = 'name-%s' % POLICY_TYPES[int(c.policy_type)]
        del c.form.enabled
        if request.method == 'POST' and c.form.validate():
            try:
                add_policy(c.form, policy_type, c.user, request.host,
                            request.remote_addr)
                flash(_('The policy has been created, '
                        'please add rules to the policy'))
            except IntegrityError:
                Session.rollback()
                flash(_('This policy already exists'))
            redirect(url(POLICY_URL_MAP[policy_type]))
        return self.render('/settings/policy_add.html')

    @ActionProtector(OnlySuperUsers())
    def edit_policy(self, policy_id):
        """Edit an existing Policy"""
        policy = get_policy(policy_id)
        if not policy:
            abort(404)
        c.policy_id = policy.id
        c.policy_type = policy.policy_type
        c.POLICY_NAME = POLICY_NAME
        c.POLICY_URL_MAP = POLICY_URL_MAP
        c.form = PolicyForm(request.POST, policy, csrf_context=session)
        rules = get_policy_rules(policy_id, True)
        if not rules:
            del c.form.enabled
        if request.method == 'POST' and c.form.validate():
            try:
                updated = update_policy(c.form, policy, c.user,
                            request.host, request.remote_addr)
                if updated:
                    flash(_('The policy has been updated'))
                else:
                    flash(_('No changes were made to the policy'))
            except IntegrityError:
                Session.rollback()
                flash(_('The update of the policy failed'))
            redirect(url(POLICY_URL_MAP[str(policy.policy_type)]))
        return self.render('/settings/policy_edit.html')

    @ActionProtector(OnlySuperUsers())
    def delete_policy(self, policy_id):
        """Delete an existing Policy"""
        policy = get_policy(policy_id)
        if not policy:
            abort(404)
        c.policy_id = policy.id
        c.policy_type = policy.policy_type
        c.POLICY_NAME = POLICY_NAME
        c.POLICY_URL_MAP = POLICY_URL_MAP
        c.form = PolicyForm(request.POST, policy, csrf_context=session)
        if request.method == 'POST' and c.form.validate():
            delete_policy(policy, c.user, request.host,
                        request.remote_addr)
            flash(_('The policy has been deleted'))
            redirect(url(POLICY_URL_MAP[str(c.policy_type)]))
        return self.render('/settings/policy_delete.html')

    @ActionProtector(OnlySuperUsers())
    def clone_policy(self, policy_type):
        """Create a policy based on the system default"""
        if int(policy_type) not in [1, 2, 3, 4]:
            flash(_('The requested policy type does not exist'))
            redirect(url('settings-rulesets'))
        c.policy_type = policy_type
        c.POLICY_NAME = POLICY_NAME
        c.POLICY_URL_MAP = POLICY_URL_MAP
        c.form = PolicyForm(request.POST, csrf_context=session)
        if request.method != 'POST':
            c.form.name.data = 'name-%s' % POLICY_TYPES[int(policy_type)]
        del c.form.enabled
        if request.method == 'POST' and c.form.validate():
            try:
                clone_policy(c.form, policy_type, c.user, request.host,
                            request.remote_addr)
                flash(_('The policy has been cloned, '
                        'you can now enable the policy'))
            except IntegrityError:
                Session.rollback()
                flash(_('This policy already exists'))
            redirect(url(POLICY_URL_MAP[policy_type]))
        return self.render('/settings/policy_clone.html')

    @ActionProtector(OnlySuperUsers())
    def view_default(self, policy_type):
        """Display the default policy"""
        if int(policy_type) not in [1, 2, 3, 4]:
            flash(_('The requested policy type does not exist'))
            redirect(url('settings-rulesets'))
        c.policy_type = policy_type
        c.POLICY_URL_MAP = POLICY_URL_MAP
        c.policy_name = POLICY_NAME[str(policy_type)]
        c.rules = process_default_rules(policy_type)
        return self.render('/settings/policy_default.html')

    @ActionProtector(OnlySuperUsers())
    def policy_rules(self, policy_id):
        """Display policy rules"""
        policy = get_policy(policy_id)
        if not policy:
            abort(404)
        c.policy_id = policy_id
        c.policy_type = policy.policy_type
        c.POLICY_URL_MAP = POLICY_URL_MAP
        c.policy = policy.name
        c.policy_name = POLICY_NAME[str(policy.policy_type)]
        c.rules = get_policy_rules(policy_id)
        return self.render('/settings/policy_rules.html')

    @ActionProtector(OnlySuperUsers())
    def add_rule(self, policy_id):
        """Add a rule to a policy"""
        policy = get_policy(policy_id)
        if not policy:
            abort(404)
        c.policy_id = policy.id
        c.policy_type = policy.policy_type
        c.POLICY_NAME = POLICY_NAME
        c.POLICY_URL_MAP = POLICY_URL_MAP
        c.form = AddRuleForm(request.POST, csrf_context=session)
        if policy.policy_type in [1, 2]:
            c.form.action.choices = ARCHIVE_RULE_ACTIONS
        if request.method == 'POST' and c.form.validate():
            try:
                add_rule(c.form, policy, c.user, request.host,
                            request.remote_addr)
                flash(_('The rule has been added'))
            except IntegrityError:
                Session.rollback()
                flash(_('The rule already exists'))
            redirect(url('policy-rulesets', policy_id=policy_id))
        return self.render('/settings/rules_add.html')

    @ActionProtector(OnlySuperUsers())
    def edit_rule(self, rule_id):
        """Edit a policy rule"""
        rule = get_rule(rule_id)
        if not rule:
            abort(404)
        c.rule_id = rule_id
        c.policy_id = rule.policy_id
        c.policy_type = rule.policy.policy_type
        c.POLICY_NAME = POLICY_NAME
        c.POLICY_URL_MAP = POLICY_URL_MAP
        c.form = AddRuleForm(request.POST, rule, csrf_context=session)
        if rule.policy.policy_type in [1, 2]:
            c.form.action.choices = ARCHIVE_RULE_ACTIONS
        if request.method == 'POST' and c.form.validate():
            try:
                updated = update_rule(c.form, rule, c.user,
                            request.host, request.remote_addr)
                if updated:
                    flash(_('The rule has been updated'))
                else:
                    flash(_('No changes were made to the rule'))
            except IntegrityError:
                Session.rollback()
                flash(_('The rule could not be updated'))
            redirect(url('policy-rulesets', policy_id=rule.policy_id))
        return self.render('/settings/rules_edit.html')

    @ActionProtector(OnlySuperUsers())
    def delete_rule(self, rule_id):
        """Delete a policy rule"""
        rule = get_rule(rule_id)
        if not rule:
            abort(404)
        c.rule_id = rule_id
        c.policy_id = rule.policy_id
        c.policy_type = rule.policy.policy_type
        c.POLICY_NAME = POLICY_NAME
        c.POLICY_URL_MAP = POLICY_URL_MAP
        c.form = AddRuleForm(request.POST, rule, csrf_context=session)
        if rule.policy.policy_type in [1, 2]:
            c.form.action.choices = ARCHIVE_RULE_ACTIONS
        if request.method == 'POST' and c.form.validate():
            policy_id = rule.policy_id
            delete_rule(rule, c.user, request.host, request.remote_addr)
            flash(_('The rule has been deleted'))
            redirect(url('policy-rulesets', policy_id=policy_id))
        return self.render('/settings/rules_delete.html')

    @ActionProtector(OnlySuperUsers())
    def move_rule(self, rule_id, direc):
        """Move a policy rule"""
        rule = get_rule(rule_id)
        if not rule:
            redirect(url('policy-rulesets', policy_id=rule.policy_id))
        if int(direc) == 1:
            rule.move_up()
        else:
            rule.move_down()
        redirect(url('policy-rulesets', policy_id=rule.policy_id))

    @ActionProtector(OnlySuperUsers())
    def mta(self):
        """MTA settings"""
        return self.render('/settings/mta.html')

    @ActionProtector(OnlySuperUsers())
    def mta_landing(self, setting_type, page=1):
        """MTA settings landing page"""
        c.setting_type = setting_type
        num_items = session.get('settings_num_items', 10)
        settings = get_mta_settings(c.setting_type)
        items = paginate.Page(settings,
                            page=int(page),
                            items_per_page=num_items)
        c.page = items
        c.setting_name = MTA_NAME[int(c.setting_type)]
        return self.render('/settings/mta_landing.html')

    @ActionProtector(OnlySuperUsers())
    def add_mta_setting(self, setting_type):
        """Add MTA Setting"""
        c.setting_type = setting_type
        c.setting_name = MTA_NAME[int(c.setting_type)]
        c.form = MTASettingsForm(request.POST, csrf_context=session)
        c.form.address_type.data = setting_type
        if c.setting_type in [2, '2']:
            c.form.address.label.text = _('Subject')
        if request.method == 'POST' and c.form.validate():
            try:
                create_mta_setting(c.form, setting_type, c.user, request.host,
                            request.remote_addr)
                flash(_('The setting has been created'))
                redirect(url('mta-setting', setting_type=setting_type))
            except IntegrityError:
                flash(_('The setting already exists'))
        return self.render('/settings/mta_add.html')

    @ActionProtector(OnlySuperUsers())
    def edit_mta_setting(self, setting_id):
        """Edit MTA Setting"""
        setting = get_mta_setting(setting_id)
        if not setting:
            abort(404)
        c.setting_id = setting_id
        c.setting_type = setting.address_type
        c.setting_name = MTA_NAME[int(c.setting_type)]
        c.form = MTASettingsForm(request.POST, setting, csrf_context=session)
        if c.setting_type in [2, '2']:
            c.form.address.label.text = _('Subject')
        if request.method == 'POST' and c.form.validate():
            try:
                updated = update_mta_setting(c.form, setting,
                            c.user, request.host,
                            request.remote_addr)
                if updated:
                    flash(_('The setting has been updated'))
                else:
                    flash(_('No changes made to the setting'))
                redirect(url('mta-setting', setting_type=setting.address_type))
            except IntegrityError:
                flash(_('The setting already exists'))
        return self.render('/settings/mta_edit.html')

    @ActionProtector(OnlySuperUsers())
    def del_mta_setting(self, setting_id):
        """Delete MTA Setting"""
        setting = get_mta_setting(setting_id)
        if not setting:
            abort(404)
        c.setting_id = setting_id
        c.setting_type = setting.address_type
        c.setting_name = MTA_NAME[int(c.setting_type)]
        c.form = MTASettingsForm(request.POST, setting, csrf_context=session)
        if c.setting_type in [2, '2']:
            c.form.address.label.text = _('Subject')
        if request.method == 'POST' and c.form.validate():
            try:
                setting_type = setting.address_type
                delete_mta_setting(setting, c.user, request.host,
                            request.remote_addr)
                flash(_('The setting has been deleted'))
                redirect(url('mta-setting', setting_type=setting_type))
            except IntegrityError:
                flash(_('The setting already exists'))
        return self.render('/settings/mta_delete.html')

    @ActionProtector(OnlySuperUsers())
    def local_scores(self, page=1):
        """List local scores"""
        num_items = session.get('settings_num_items', 10)
        scores = get_local_scores()
        items = paginate.Page(scores,
                            page=int(page),
                            items_per_page=num_items)
        c.page = items
        return self.render('/settings/localscores.html')

    # @ActionProtector(OnlySuperUsers())
    # def add_local_scores(self, score_id=None):
    #     """Add a local score"""
    #     if score_id:
    #         score = get_local_score(score_id)

    @ActionProtector(OnlySuperUsers())
    def edit_local_scores(self, score_id):
        """Update a local score"""
        score = get_local_score(score_id)
        if not score:
            abort(404)

        c.score_id = score_id
        c.form = LocalScoreForm(request.POST, score, csrf_context=session)
        if request.method == 'POST' and c.form.validate():
            update_local_score(c.form, score, c.user, request.host,
                        request.remote_addr)
            flash(_('The local score for: %s has been updated') % score.id)
            redirect(url('local-scores'))
        return self.render('/settings/localscores_edit.html')

    # pylint: disable-msg=R0201
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
