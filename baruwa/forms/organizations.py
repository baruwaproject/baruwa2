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
"Organization forms"

import cracklib

from wtforms import validators, TextField, BooleanField, PasswordField
from wtforms import FileField
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField
from pylons.i18n.translation import lazy_ugettext as _

from baruwa.forms import Form, REQ_MSG
from baruwa.lib.regex import DOM_RE
from baruwa.lib.misc import ipaddr_is_valid


def check_pw_strength(passwd):
    "Check password strength"
    try:
        cracklib.VeryFascistCheck(passwd)
    except ValueError, message:
        raise validators.ValidationError(_("Password %(msg)s.") %
        dict(msg=str(message)[3:]))


class OrgForm(Form):
    "Organization form"
    name = TextField(_('Organization name'),
                [validators.Required(message=REQ_MSG)])
    domains = QuerySelectMultipleField(_('Domains'),
                            get_label='name',
                            allow_blank=True)
    admins = QuerySelectMultipleField(_('Admins'),
                            get_label='username',
                            allow_blank=True)


class DelOrgForm(OrgForm):
    "Bulk delete organizations domains"
    delete_domains = BooleanField(_('Delete Organization domains'),
                            default=False)


class RelayForm(Form):
    "Organization relay form"
    address = TextField(_('Hostname'))
    enabled = BooleanField(_('Enabled'), default=True)
    username = TextField(_('SMTP-AUTH username'))
    password1 = PasswordField(_('SMTP-AUTH password'))
    password2 = PasswordField(_('Retype Password'),
    [validators.EqualTo('password1', message=_('Passwords must match'))])

    def validate_address(self, field):
        if self.username.data == '' and field.data == '':
            raise validators.ValidationError(
            _('Provide either a hostname or username & password'))
        if (field.data != '' and not DOM_RE.match(field.data) and
            not ipaddr_is_valid(field.data)):
            raise validators.ValidationError(
            _('Provide a valid hostname or IP address'))

    def validate_username(self, field):
        if field.data == '' and self.address.data == '':
            raise validators.ValidationError(_('Required'))
        if field.data and '@' in field.data:
            raise validators.ValidationError(
                    _('Email usernames not supported'))

    def validate_password1(self, field):
        if self.address.data == '' and self.username.data != '':
            check_pw_strength(field.data)


class RelayEditForm(RelayForm):
    "Edit relay"
    def validate_password1(self, field):
        if (self.address.data == '' and self.username.data != ''
            and field.data != ''):
            try:
                cracklib.VeryFascistCheck(field.data)
            except ValueError, message:
                raise validators.ValidationError(_("Password %(msg)s.") %
                dict(msg=str(message)[3:]))


class ImportCSVForm(Form):
    "import csv"
    csvfile = FileField(_('CSV file'))
    skipfirst = BooleanField(_('Skip first line'), default=False)
