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
"""accounts forms"""

from wtforms import PasswordField, validators, DecimalField, RadioField
from wtforms import BooleanField, TextField, SelectField
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField
from pylons.i18n.translation import lazy_ugettext as _
from sqlalchemy.orm.exc import NoResultFound

from baruwa.forms import Form
from baruwa.model.meta import Session
from baruwa.model.accounts import User
from baruwa.model.domains import Domain, DomainAlias
from baruwa.forms.organizations import check_pw_strength
from baruwa.forms import (TIMEZONE_TUPLES, REQ_MSG, EMAIL_MSG, HIGHSPAM_DESC,
    LOWSPAM_DESC, STATUS_DESC)
from baruwa.forms.messages import MultiCheckboxField

ACCOUNT_TYPES = (
    ('3', _('User')),
    ('2', _('Domain admin')),
    ('1', _('Administrator')),
)

USER_DESC = _("""The username for the account""")

FIRSTNAME_DESC = _("""The first names""")

LASTNAME_DESC = _("""The last names""")

EMAIL_DESC = _("""A valid email address""")

TIMEZONE_DESC = _("""Users timezone, all dates and
times will be displayed in this timezone""")

DOMAINS_DESC = _("""The domains to which this
user belongs""")

REPORTS_DESC = _("""If enabled the user will
receive reports from the system, these
include quarantine as well as summary
reports""")

SPAM_CHECKS_DESC = _("""Enable or disable spam checking
of email sent to and from this users email
addresses""")


def check_password(form, field):
    "check password strength"
    check_pw_strength(field.data)


def check_domain(form, field):
    "check domain"
    try:
        domain = field.data.split('@')[1]
        try:
            Session.query(Domain).filter(Domain.name == domain).one()
        except NoResultFound:
            Session.query(DomainAlias).filter(DomainAlias.name == domain).one()
    except IndexError:
        raise validators.ValidationError(
                _(u'Please provide a valid email address'))
    except NoResultFound:
        raise validators.ValidationError(
                    _(u'The domain: %(dom)s is not local')
                    % dict(dom=domain)
                )


def check_account(form, field):
    "check account"
    if field.data == 3 and not form.domains.data:
        raise validators.ValidationError(
                    _(u'Please select atleast one domain')
                )


def can_reset(form, field):
    "check account is legible to reset"
    try:
        user = Session.query(User)\
                .filter(User.email == field.data)\
                .one()
        if user.account_type != 3:
            raise validators.ValidationError(
                    _("Admin accounts cannot be reset via the web"))
    except NoResultFound:
        raise validators.ValidationError(_("Account not found"))


class AddUserForm(Form):
    """Add user"""
    username = TextField(_('Username'),
                        [validators.Required(message=REQ_MSG),
                        validators.Length(min=4, max=254)],
                        description=USER_DESC)
    firstname = TextField(_('First name'),
                        [validators.Length(max=254)],
                        description=FIRSTNAME_DESC)
    lastname = TextField(_('Last name'),
                        [validators.Length(max=254)],
                        description=LASTNAME_DESC)
    password1 = PasswordField(_('New Password'), [check_password,
                            validators.Required(message=REQ_MSG),
                            validators.EqualTo('password2',
                            message=_('Passwords must match'))],
                        description=_("""This must be a strong
                        password"""))
    password2 = PasswordField(_('Retype Password'),
                        [validators.Required(message=REQ_MSG)])
    email = TextField(_('Email address'),
                        [validators.Required(message=REQ_MSG),
                        validators.Email(message=EMAIL_MSG)],
                        description=EMAIL_DESC)
    timezone = SelectField(_('Timezone'), choices=TIMEZONE_TUPLES,
                        description=TIMEZONE_DESC)
    account_type = SelectField(_('Account type'),
                        choices=list(ACCOUNT_TYPES),
                        description=_("""The account type"""))
    domains = QuerySelectMultipleField(_('Domains'),
                        get_label='name',
                        allow_blank=True,
                        description=DOMAINS_DESC)
    active = BooleanField(_('Enabled'),
                        description=STATUS_DESC)
    send_report = BooleanField(_('Send reports'),
                        description=REPORTS_DESC)
    spam_checks = BooleanField(_('Enable spam checks'), default=True,
                        description=SPAM_CHECKS_DESC)
    low_score = DecimalField(_('Probable spam score'), places=1, default=0,
                        description=LOWSPAM_DESC)
    high_score = DecimalField(_('Definite spam score'), places=1, default=0,
                        description=HIGHSPAM_DESC)

    def validate_domains(form, field):
        """Validate a domain"""
        if int(form.account_type.data) == 3 and not field.data:
            raise validators.ValidationError(
                _(u'Please select atleast one domain'))


class EditUserForm(Form):
    """Edit user"""
    username = TextField(_('Username'), [validators.Required(message=REQ_MSG),
                        validators.Length(min=4, max=254)],
                        description=USER_DESC)
    firstname = TextField(_('First name'), [validators.Length(max=254)],
                        description=FIRSTNAME_DESC)
    lastname = TextField(_('Last name'), [validators.Length(max=254)],
                        description=LASTNAME_DESC)
    email = TextField(_('Email address'),
                        [validators.Required(message=REQ_MSG)],
                        description=EMAIL_DESC)
    timezone = SelectField(_('Timezone'), choices=TIMEZONE_TUPLES,
                        description=TIMEZONE_DESC)
    domains = QuerySelectMultipleField(_('Domains'),
                        get_label='name',
                        allow_blank=False,
                        description=DOMAINS_DESC)
    active = BooleanField(_('Enabled'),
                        description=STATUS_DESC)
    send_report = BooleanField(_('Send reports'),
                        description=REPORTS_DESC)
    spam_checks = BooleanField(_('Enable spam checks'),
                        description=SPAM_CHECKS_DESC)
    low_score = DecimalField(_('Spam low score'), places=1,
                        description=LOWSPAM_DESC)
    high_score = DecimalField(_('Spam high score'), places=1,
                        description=HIGHSPAM_DESC)


class BulkDelUsers(Form):
    """Bulk account delete form"""
    accountid = MultiCheckboxField('')
    whatdo = RadioField('', choices=[('delete', _('delete'),),
                                    ('disable', _('disable'),),
                                    ('enable', _('enable'),), ])


class AddressForm(Form):
    """Add alias address"""
    address = TextField(_('Email Address'),
                    [validators.Required(message=REQ_MSG),
                    validators.Email(message=EMAIL_MSG), check_domain],
                    description=EMAIL_DESC)
    enabled = BooleanField(_('Enabled'),
                    description=SPAM_CHECKS_DESC)


class ChangePasswordForm(Form):
    """Admin change user password"""
    password1 = PasswordField(_('New Password'),
                    [check_password, validators.Required(message=REQ_MSG),
                    validators.EqualTo('password2',
                    message=_('Passwords must match'))])
    password2 = PasswordField(_('Retype Password'),
                    [validators.Required(message=REQ_MSG)])


class UserPasswordForm(ChangePasswordForm):
    """User password change"""
    password3 = PasswordField(_('Old Password'),
                    [validators.Required(message=REQ_MSG)])


class ResetPwForm(Form):
    """User reset password form"""
    email = TextField(_('Email Address'),
            [validators.Required(message=REQ_MSG),
            validators.Email(message=EMAIL_MSG),
            can_reset])
