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
"""Domain forms"""

from wtforms import TextAreaField
from pylons.i18n.translation import lazy_ugettext as _
from wtforms import BooleanField, TextField, IntegerField, RadioField
from wtforms import SelectField, validators, DecimalField, PasswordField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField

from baruwa.forms.messages import MultiCheckboxField
from baruwa.forms import Form, TIMEZONE_TUPLES, REQ_MSG
from baruwa.forms import check_domain, check_domain_alias
from baruwa.lib.misc import ipaddr_is_valid, get_languages
from baruwa.lib.regex import DOM_RE, MSGSIZE_RE, NUMORSPACE_RE


DELIVERY_MODES = (
    ('1', _('Load balance')),
    ('2', _('Fail over')),
)

LANGUAGES = [lang.popitem() for lang in get_languages()]

SPAM_ACTIONS = (
    ('2', _('Quarantine')),
    ('3', _('Delete')),
    ('1', _('Deliver')),
)

REPORT_FREQ = (
    ('3', _('Monthly')),
    ('2', _('Weekly')),
    ('1', _('Daily')),
    ('0', _('Disabled')),
)

DELIVERY_PROTOCOLS = (
    ('1', _('SMTP')),
    ('2', _('LMTP')),
)

AUTH_PROTOCOLS = (
    ('1', _('POP3')),
    ('2', _('IMAP')),
    ('3', _('SMTP')),
    ('4', _('RADIUS/RSA SECUREID')),
    ('5', _('LDAP')),
    ('6', _('YUBIKEY')),
    ('7', _('OAUTH')),
)

SEARCH_SCOPE = (
    ('subtree', _('SUBTREE')),
    ('onelevel', _('ONE LEVEL')),
)


def check_server_addr(form, field):
    "check server address"
    if not DOM_RE.match(field.data) and not ipaddr_is_valid(field.data):
        raise validators.ValidationError(
        _('Invalid Domain name or IP address'))


class AddDomainForm(Form):
    """Add domain"""
    name = TextField(_('Domain name'), [validators.Required(message=REQ_MSG),
                    validators.Regexp(DOM_RE,
                    message=_('Invalid Domain name')),
                    check_domain,
                    check_domain_alias])
    site_url = TextField(_('Site url'),
                        [validators.Required(message=REQ_MSG),
                        validators.URL()])
    status = BooleanField(_('Enabled'), default=True)
    smtp_callout = BooleanField(_('Enable SMTP callouts'), default=False)
    ldap_callout = BooleanField(_('Enable LDAP callouts'), default=False)
    virus_checks = BooleanField(_('Enable Virus checks'), default=True)
    spam_checks = BooleanField(_('Enable SPAM checks'), default=True)
    spam_actions = SelectField(_('What to do with probable spam'),
                                choices=list(SPAM_ACTIONS))
    highspam_actions = SelectField(_('What to do with definite spam'),
                                    choices=list(SPAM_ACTIONS))
    low_score = DecimalField(_('Probable spam score'), places=1, default=0)
    high_score = DecimalField(_('Definite spam score'), places=1, default=0)
    message_size = TextField(_('Maximum Message Size'),
                            [validators.Regexp(MSGSIZE_RE,
                            message=_('Invalid message size, '
                                    'only B, K, M accepted'))],
                            default='0')
    delivery_mode = SelectField(_('Multi destination delivery mode'),
                                choices=DELIVERY_MODES)
    language = SelectField(_('Language'), choices=LANGUAGES, default='en')
    timezone = SelectField(_('Default Timezone'), choices=TIMEZONE_TUPLES)
    report_every = SelectField(_('Report frequency'),
                                choices=REPORT_FREQ, default='3')
    organizations = QuerySelectMultipleField(_('Organizations'),
                                    get_label='name',
                                    allow_blank=True)


class EditDomainForm(Form):
    """Edit/Delete a domain"""
    name = TextField(_('Domain name'), [validators.Required(message=REQ_MSG),
                    validators.Regexp(DOM_RE,
                    message=_('Invalid Domain name'))])
    # not inheriting from AddDomainForm cause it mangles output if we do
    site_url = TextField(_('Site url'),
                        [validators.Required(message=REQ_MSG),
                        validators.URL()])
    status = BooleanField(_('Enabled'), default=True)
    smtp_callout = BooleanField(_('Enable SMTP callouts'), default=False)
    ldap_callout = BooleanField(_('Enable LDAP callouts'), default=False)
    virus_checks = BooleanField(_('Enable Virus checks'), default=True)
    spam_checks = BooleanField(_('Enable SPAM checks'), default=True)
    spam_actions = SelectField(_('What to do with probable spam'),
                                choices=list(SPAM_ACTIONS))
    highspam_actions = SelectField(_('What to do with definite spam'),
                                    choices=list(SPAM_ACTIONS))
    low_score = DecimalField(_('Probable spam score'), places=1, default=0)
    high_score = DecimalField(_('Definite spam score'), places=1, default=0)
    message_size = TextField(_('Maximum Message Size'),
                            [validators.Regexp(MSGSIZE_RE,
                            message=_('Invalid message size, '
                                    'only B, K, M accepted'))],
                            default='0')
    delivery_mode = SelectField(_('Multi destination delivery mode'),
                                choices=DELIVERY_MODES)
    language = SelectField(_('Language'), choices=LANGUAGES, default='en')
    timezone = SelectField(_('Default Timezone'), choices=TIMEZONE_TUPLES)
    report_every = SelectField(_('Report frequency'),
                                choices=REPORT_FREQ, default='3')
    organizations = QuerySelectMultipleField(_('Organizations'),
                                    get_label='name',
                                    allow_blank=True)


class BulkDelDomains(Form):
    """Bulk domains delete"""
    domainid = MultiCheckboxField('')
    whatdo = RadioField('', choices=[('delete', _('delete'),),
                                    ('disable', _('disable'),),
                                    ('enable', _('enable'),),])


class AddDomainAlias(Form):
    """Add domain alias"""
    name = TextField(_('Domain alias name'),
                    [validators.Required(message=REQ_MSG),
                    validators.Regexp(DOM_RE,
                    message=_('Invalid Domain name')),
                    check_domain,
                    check_domain_alias])
    status = BooleanField(_('Enabled'), default=True)
    domain = QuerySelectField(_('Parent domain'),
                            get_label='name',
                            allow_blank=False)


class EditDomainAlias(AddDomainAlias):
    """Override to make status work"""
    name = TextField(_('Domain alias name'),
                    [validators.Required(message=REQ_MSG),
                    validators.Regexp(DOM_RE,
                    message=_('Invalid Domain name')),])
    status = BooleanField(_('Enabled'))


class DelDomainAlias(AddDomainAlias):
    """Override to make prevent validation"""
    name = TextField(_('Domain alias name'),
                    [validators.Required(message=REQ_MSG),
                    validators.Regexp(DOM_RE,
                    message=_('Invalid Domain name')),])


class AddDeliveryServerForm(Form):
    """Add delivery server"""
    address = TextField(_('Server address'),
                    [validators.Required(message=REQ_MSG),
                    check_server_addr])
    protocol = SelectField(_('Protocol'), choices=list(DELIVERY_PROTOCOLS))
    port = IntegerField(_('Port'), default=25)
    enabled = BooleanField(_('Enabled'), default=True)


class LinkDeliveryServerForm(Form):
    """Link delivery server"""
    server = QuerySelectField(_('Server address'), get_label='address')


class AddAuthForm(Form):
    """Add auth server"""
    address = TextField(_('Server address'),
                [validators.Required(message=REQ_MSG),
                check_server_addr])
    protocol = SelectField(_('Protocol'), choices=list(AUTH_PROTOCOLS))
    port = TextField(_('Port'), [validators.Regexp(NUMORSPACE_RE,
                    message=_('must be numeric'))])
    enabled = BooleanField(_('Enabled'), default=True)
    split_address = BooleanField(_('Split address'), default=False)
    user_map_template = TextField(_('Username map template'))


class AddLDAPSettingsForm(Form):
    """Add ldap settings"""
    basedn = TextField(_('Base DN'), [validators.Required(message=REQ_MSG)])
    nameattribute = TextField(_('Username attribute'),
                            [validators.Required(message=REQ_MSG)],
                            default='uid')
    emailattribute = TextField(_('Email attribute'), 
                            [validators.Required(message=REQ_MSG)],
                               default='mail')
    binddn = TextField(_('Bind DN'))
    bindpw = PasswordField(_('Bind password'))
    usetls = BooleanField(_('Use TLS'), default=False)
    usesearch = BooleanField(_('Search for UserDN'), default=False)
    searchfilter = TextAreaField(_('Auth Search Filter'))
    search_scope = SelectField(_('Auth Search Scope'),
                    choices=list(SEARCH_SCOPE))
    emailsearchfilter = TextAreaField(_('Email Search Filter'))
    emailsearch_scope = SelectField(_('Email Search Scope'),
                    choices=list(SEARCH_SCOPE))
    #enabled = BooleanField(_('Enabled'), default=True)

    # def validate_searchfilter(form, field):
    #     "Validate searchfilter"
    #     if form.usesearch and field.data == '':
    #         raise validators.ValidationError(
    #                     _('Search Filter is required if using search')
    #                 )

    def validate_search_scope(form, field):
        "validate search scope"
        if form.usesearch and field.data not in ['subtree', 'onelevel']:
            raise validators.ValidationError(
                    _('Unsupported search scope')
                )


class AddRadiusSettingsForm(Form):
    """Add radius settings"""
    secret = PasswordField(_('Radius secret'),
            [validators.Required(message=REQ_MSG)])
    timeout = IntegerField(_('Request timeout'), default=0)
