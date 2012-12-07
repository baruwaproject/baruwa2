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
"Reports forms"

import re
import time
import datetime

from wtforms import SelectField, validators, TextField
from webhelpers.html import escape
from pylons.i18n.translation import lazy_ugettext as _

from baruwa.forms import Form
from baruwa.lib.regex import ADDRESS_RE, DOM_RE, IPV4_RE


FILTER_ITEMS = (
    ('messageid', _('Message ID')),
    ('size', _('Message size')),
    ('from_address', _('From Address')),
    ('from_domain', _('From Domain')),
    ('to_address', _('To Address')),
    ('to_domain', _('To Domain')),
    ('subject', _('Subject')),
    ('clientip', _('Received from')),
#    ('archive','Is Archived'),
    ('scaned', _('Was scanned')),
    ('spam', _('Is Spam')),
    ('highspam', _('Is Definite spam')),
#    ('saspam', _('Is SA spam')),
    ('rblspam', _('Is RBL listed')),
    ('whitelisted', _('Is approved sender')),
    ('blacklisted', _('Is banned sender')),
    ('sascore', _('Spam score')),
    ('spamreport', _('Spam report')),
    ('virusinfected', _('Is virus infected')),
    ('nameinfected', _('Is name infected')),
    ('otherinfected', _('Is other infected')),
    ('date', _('Date')),
    ('time', _('Time')),
    ('headers', _('Headers')),
    ('isquarantined', _('Is quarantined')),
    ('hostname', _('Processed by host')),
)

FILTER_BY = (
    ('1', _('is equal to')),
    ('2', _('is not equal to')),
    ('3', _('is greater than')),
    ('4', _('is less than')),
    ('5', _('contains')),
    ('6', _('does not contain')),
    ('7', _('matches regex')),
    ('8', _('does not match regex')),
    ('9', _('is null')),
    ('10', _('is not null')),
    ('11', _('is true')),
    ('12', _('is false')),
)

EMPTY_VALUES = (None, '')

BOOL_FIELDS = ["scaned", "spam", "highspam", "saspam", "rblspam",
    "whitelisted", "blacklisted", "virusinfected", "nameinfected",
    "otherinfected", "isquarantined"]
TEXT_FIELDS = ["id", "from_address", "from_domain", "to_address",
    "to_domain", "subject", "clientip", "spamreport", "headers",
    "hostname"]
TIME_FIELDS = ["date", "time"]
NUM_FIELDS = ["size", "sascore"]
EMAIL_FIELDS = ['from_address', 'to_address']
DOMAIN_FIELDS = ['from_domain', 'to_domain']

BOOL_FILTER = [11, 12]
NUM_FILTER = [1, 2, 3, 4]
TEXT_FILTER = [1, 2, 5, 6, 7, 8, 9, 10]
TIME_FILTER = [1, 2, 3, 4]


def isnumeric(value):
    "Validate numeric values"
    return str(value).replace(".", "").replace("-", "").isdigit()


def check_form(form, field):
    "validate the form"
    filteredby = dict(FILTER_BY)
    filteritems = dict(FILTER_ITEMS)
    # field <-> filter checks
    if ((field.data in BOOL_FIELDS and int(form.filtered_by.data)
        not in BOOL_FILTER) or (field.data in TEXT_FIELDS and
        int(form.filtered_by.data) not in TEXT_FILTER) or
        (field.data in TIME_FIELDS and int(form.filtered_by.data)
        not in TIME_FILTER) or (field.data in NUM_FIELDS and
        int(form.filtered_by.data) not in NUM_FILTER)):
        raise validators.ValidationError(
        _('%(field)s does not support the "%(filt)s" filter') %
        dict(field=filteritems[field.data],
        filt=filteredby[form.filtered_by.data]))
    # time
    if ((field.data in TEXT_FIELDS or field.data in TIME_FIELDS
        or field.data in NUM_FIELDS) and form.filtered_value.data in
        EMPTY_VALUES):
        raise validators.ValidationError(_('Please supply a value to query'))
    # numerics
    if field.data in NUM_FIELDS and not isnumeric(form.filtered_value.data):
        raise validators.ValidationError(_('The value has to be numeric'))
    # emails
    if (field.data in TEXT_FIELDS and int(form.filtered_by.data) in [1, 2]
        and field.data in EMAIL_FIELDS):
        if not ADDRESS_RE.match(form.filtered_value.data):
            raise validators.ValidationError(
            _('%(email)s is not a valid e-mail address.') %
            dict(email=escape(form.filtered_value.data)))
    # domains
    if (field.data in TEXT_FIELDS and int(form.filtered_by.data) in [1, 2]
        and field.data in DOMAIN_FIELDS):
        if not DOM_RE.match(form.filtered_value.data):
            raise validators.ValidationError(
            _('%(dom)s is not a valid domain address.') %
            dict(dom=escape(form.filtered_value.data)))
    # regex on text fields
    if field.data in TEXT_FIELDS and int(form.filtered_by.data) in [7, 8]:
        try:
            re.compile(form.filtered_value.data)
        except re.error:
            raise validators.ValidationError(_('Invalid regex supplied'))
    if field.data in TEXT_FIELDS:
        # ip
        if field.data == 'clientip':
            if not IPV4_RE.match(form.filtered_value.data):
                raise validators.ValidationError(
                _('Please provide a valid ipv4 address'))
        # hostname
        if field.data == 'hostname':
            if (not IPV4_RE.match(form.filtered_value.data) and
                not DOM_RE.match(form.filtered_value.data)):
                raise validators.ValidationError(
                _("Please provide a valid hostname or ipv4 address"))
    if field.data in TIME_FIELDS:
        if field.data == 'date':
            try:
                datetime.date(
                *time.strptime(form.filtered_value.data, '%Y-%m-%d')[:3])
            except ValueError:
                raise validators.ValidationError(
                    _('Please provide a valid date in YYYY-MM-DD format'))
        if field.data == 'time':
            try:
                datetime.time(
                *time.strptime(form.filtered_value.data, '%H:%M')[3:6])
            except ValueError:
                raise validators.ValidationError(
                    _('Please provide valid time in HH:MM format'))


class FilterForm(Form):
    "Filters form"
    filtered_field = SelectField('', [check_form], choices=list(FILTER_ITEMS))
    filtered_by = SelectField('', choices=list(FILTER_BY))
    filtered_value = TextField('')
