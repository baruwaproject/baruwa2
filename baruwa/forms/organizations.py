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
"Organization forms"

import cracklib

from wtforms import validators, TextField, BooleanField, PasswordField
from wtforms import FileField, DecimalField, SelectField, IntegerField
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField
from pylons.i18n.translation import lazy_ugettext as _

from baruwa.lib.misc import ipaddr_is_valid
from baruwa.lib.regex import DOM_RE, IPV4_RE
from baruwa.forms.domains import SPAM_ACTIONS, SPAM_ACTIONS_DESC, \
    HIGHSPAM_ACTIONS_DESC
from baruwa.forms import Form, REQ_MSG, STATUS_DESC, LOWSPAM_DESC, \
    HIGHSPAM_DESC


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
                [validators.Required(message=REQ_MSG)],
                description=_("""The name of the organization,
                organizations are used to group domains and
                assign administrators to manage them"""))
    domains = QuerySelectMultipleField(_('Domains'),
                get_label='name',
                allow_blank=True,
                description=_("""The domains to add to this
                organization"""))
    admins = QuerySelectMultipleField(_('Admins'),
                get_label='username',
                allow_blank=True,
                description=_("""The selected admins will
                manage all the domains under this
                organization"""))


class DelOrgForm(OrgForm):
    "Bulk delete organizations domains"
    delete_domains = BooleanField(_('Delete Organization domains'),
                            default=False)


class RelayForm(Form):
    "Organization relay form"
    address = TextField(_('Hostname'),
                description=_("""The hostname, IP address or
                IP network of server(s) that you want to allow
                to relay mail via this system. If using SMTP-AUTH
                you do not have to specify this."""))
    enabled = BooleanField(_('Enabled'), default=True,
                description=STATUS_DESC)
    username = TextField(_('SMTP-AUTH username'),
                description=_("""Username to use for SMTP AUTH"""))
    password1 = PasswordField(_('SMTP-AUTH password'),
                description=_("""Password to use for SMTP AUTH"""))
    password2 = PasswordField(_('Retype Password'),
                            [validators.EqualTo('password1',
                            message=_('Passwords must match'))])
    description = TextField(_('Description'),
                description=_("""Description of the relay"""))
    ratelimit = IntegerField(_('Number of messages per 15 minutes'),
                            default=250,
                            description=_("""The number of messages to
                            process within a 15 minute window. This is
                            used to ratelimit senders to prevent issues
                            such as blacklisting due to spam outbreaks
                            and malware compromise"""))
    low_score = DecimalField(_('Probable spam score'), places=1, default=0,
                        description=LOWSPAM_DESC)
    high_score = DecimalField(_('Definite spam score'), places=1, default=0,
                        description=HIGHSPAM_DESC)
    spam_actions = SelectField(_('What to do with probable spam'),
                        choices=list(SPAM_ACTIONS),
                        description=SPAM_ACTIONS_DESC)
    highspam_actions = SelectField(_('What to do with definite spam'),
                        choices=list(SPAM_ACTIONS),
                        description=HIGHSPAM_ACTIONS_DESC)

    def validate_address(self, field):
        "validate address"
        if self.username.data == '' and field.data == '':
            msg = _('Provide either a hostname or username & password')
            raise validators.ValidationError(msg)
        if (field.data != '' and not DOM_RE.match(field.data) and
            not IPV4_RE.match(field.data) and not ipaddr_is_valid(field.data)):
            msg = _('Provide a valid hostname, IP address or IP network')
            raise validators.ValidationError(msg)

    def validate_username(self, field):
        "validate username"
        if field.data == '' and self.address.data == '':
            raise validators.ValidationError(_('Required'))
        if field.data and '@' in field.data:
            msg = _('Email usernames not supported')
            raise validators.ValidationError(msg)

    def validate_password1(self, field):
        "validate password"
        if self.address.data == '' and self.username.data != '':
            check_pw_strength(field.data)


class RelayEditForm(RelayForm):
    "Edit relay"
    def validate_password1(self, field):
        "validate password strength"
        if (self.address.data == '' and self.username.data != ''
            and field.data != ''):
            try:
                cracklib.VeryFascistCheck(field.data)
            except ValueError, message:
                raise validators.ValidationError(_("Password %(msg)s.") %
                dict(msg=str(message)[3:]))


class ImportCSVForm(Form):
    "import csv"
    csvfile = FileField(_('CSV file'),
                description=_("""CSV formated file containing the
                records that should be imported"""))
    skipfirst = BooleanField(_('Skip first line'), default=False,
                description=_("""Select this if the first line
                contains the names of the fields, this will always
                be the case for files formated according to the
                specifications"""))
