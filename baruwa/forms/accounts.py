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
"""accounts forms"""

from wtforms import PasswordField, validators, DecimalField, RadioField
from wtforms import BooleanField, TextField, SelectField
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField
from pylons.i18n.translation import lazy_ugettext as _
from sqlalchemy.orm.exc import NoResultFound

from baruwa.model.domains import Domain
from baruwa.model.meta import Session
from baruwa.forms.organizations import check_pw_strength

try:
    x = _('hi')
    x
except TypeError:
    from baruwa.lib.misc import _

from baruwa.forms import Form
from baruwa.forms.messages import MultiCheckboxField

ACCOUNT_TYPES = (
    ('3', _('User')),
    ('2', _('Domain admin')),
    ('1', _('Administrator')),
)


def check_password(form, field):
    "check password strength"
    check_pw_strength(field.data)


def check_domain(form, field):
    "check domain"
    domain = field.data.split('@')[1]
    try:
        Session.query(Domain).filter(Domain.name == domain).one()
    except NoResultFound:
        raise validators.ValidationError(
                    _('The domain: %(dom)s is not local')
                    % dict(dom=domain)
                )


def check_account(form, field):
    "check account"
    if field.data == 3 and not form.domains.data:
        raise validators.ValidationError(
                    _('Please select atleast one domain')
                )


class AddUserForm(Form):
    """Add user"""
    username = TextField(_('Username'),
                        [validators.Required(),
                        validators.Length(min=4, max=254)])
    firstname = TextField(_('First name'),
                        [validators.Length(max=254)])
    lastname = TextField(_('Last name'),
                        [validators.Length(max=254)])
    password1 = PasswordField(_('New Password'), [check_password,
                            validators.Required(),
                            validators.EqualTo('password2',
                            message=_('Passwords must match'))])
    password2 = PasswordField(_('Retype Password'),
                        [validators.Required()])
    email = TextField(_('Email address'),
                        [validators.Required(),
                        validators.Email()])
    account_type = SelectField(
                                _('Account type'),
                                choices=list(ACCOUNT_TYPES))
    domains = QuerySelectMultipleField(_('Domains'),
                                        get_label='name',
                                        allow_blank=True)
    active = BooleanField(_('Enabled'))
    send_report = BooleanField(_('Send reports'))
    spam_checks = BooleanField(_('Enable spam checks'), default=True)
    low_score = DecimalField(_('Probable spam score'), places=1, default=0)
    high_score = DecimalField(_('Definite spam score'), places=1, default=0)

    def validate_domains(form, field):
        if int(form.account_type.data) == 3 and not field.data:
            raise validators.ValidationError(
            _('Please select atleast one domain'))


class EditUserForm(Form):
    """Edit user"""
    username = TextField(_('Username'), [validators.Required(),
                        validators.Length(min=4, max=254)])
    firstname = TextField(_('First name'), [validators.Length(max=254)])
    lastname = TextField(_('Last name'), [validators.Length(max=254)])
    email = TextField(_('Email address'), [validators.Required()])
    domains = QuerySelectMultipleField(_('Domains'), get_label='name', 
                                        allow_blank=False)
    active = BooleanField(_('Enabled'))
    send_report = BooleanField(_('Send reports'))
    spam_checks = BooleanField(_('Enable spam checks'))
    low_score = DecimalField(_('Spam low score'), places=1)
    high_score = DecimalField(_('Spam high score'), places=1)


class BulkDelUsers(Form):
    accountid = MultiCheckboxField('')
    whatdo = RadioField('', choices=[('delete', 'delete',), ('disable', 'disable',),('enable', 'enable',),])


class AddressForm(Form):
    """Add alias address"""
    address = TextField('Email Address', [validators.Required(),
                        validators.Email(), check_domain])
    enabled = BooleanField(_('Enabled'))


class ChangePasswordForm(Form):
    """Admin change user password"""
    password1 = PasswordField(_('New Password'), [check_password,
                            validators.Required(),
                            validators.EqualTo('password2',
                            message=_('Passwords must match'))])
    password2 = PasswordField(_('Retype Password'), [validators.Required()])


class UserPasswordForm(ChangePasswordForm):
    """User password change"""
    password3 = PasswordField(_('Old Password'), [validators.Required()])
