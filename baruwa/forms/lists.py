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
"Lists forms"

from wtforms import validators, TextField, SelectField, BooleanField
from sqlalchemy.orm.exc import NoResultFound
from pylons.i18n.translation import lazy_ugettext as _

from baruwa.forms import Form, REQ_MSG
from baruwa.model.meta import Session
from baruwa.model.domains import Domain
from baruwa.lib.misc import ipaddr_is_valid
from baruwa.lib.regex import EMAIL_RE, DOM_RE, IPV4_RE
from baruwa.lib.regex import IPV4_NET_OR_RANGE_RE, LOCAL_PART_RE


LIST_TYPES = (
    ('1', _('Approved senders')),
    ('2', _('Banned senders')),
)


def from_addr_check(form, field):
    "Check from address"
    if (not EMAIL_RE.match(field.data) and not DOM_RE.match(field.data)
            and not IPV4_RE.match(field.data) and not
            IPV4_NET_OR_RANGE_RE.match(field.data) and not
            ipaddr_is_valid(field.data)):
        raise validators.ValidationError(
            _('Provide either a valid IP, email,'
            ' Domain address, or IP network or range'))


def admin_toaddr_check(form, field):
    "Admin check to field"
    if field.data != '':
        #email
        if EMAIL_RE.match(field.data) or DOM_RE.match(field.data):
            if '@' in field.data:
                domain = field.data.split('@')[1]
            else:
                domain = field.data
            try:
                Session.query(Domain.name).filter(Domain.name == domain).one()
            except NoResultFound:
                raise validators.ValidationError(
                _('The domain %(dom)s is not local') % dict(dom=domain))
        elif field.data != 'any':
            raise validators.ValidationError(
            _('Provide either a valid email or domain address'))


class AddtoList(Form):
    "Add list form"
    from_address = TextField(_('From address'),
                        [validators.Required(message=REQ_MSG),
                        from_addr_check])
    to_address = TextField(_('To address'), [admin_toaddr_check])
    list_type = SelectField(_('List type'), choices=list(LIST_TYPES))


class AddtoDomainList(Form):
    "Add list to domain form"
    from_address = TextField(_('From address'),
                        [validators.Required(message=REQ_MSG),
                        from_addr_check])
    to_address = TextField(_('User account'))
    to_domain = SelectField(_('Domain name'))
    list_type = SelectField(_('List type'), choices=list(LIST_TYPES))
    add_to_alias = BooleanField(_('Add to aliases as well'), default=False)

    def validate_to_address(form, field):
        if field.data != '' and field.data != 'any':
            if not LOCAL_PART_RE.match(field.data):
                raise validators.ValidationError(
                _('Invalid user account supplied'))


class AddtoUserList(Form):
    "Add list to user form"
    from_address = TextField(_('From address'),
                        [validators.Required(message=REQ_MSG),
                        from_addr_check])
    to_address = SelectField(_('To address'))
    list_type = SelectField(_('List type'), choices=list(LIST_TYPES))
    add_to_alias = BooleanField(_('Add to aliases as well'), default=False)


list_forms = {
    1: AddtoList,
    2: AddtoDomainList,
    3: AddtoUserList
}
