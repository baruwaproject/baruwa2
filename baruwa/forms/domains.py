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
"""Domain forms"""

from wtforms import TextAreaField
from pylons.i18n.translation import lazy_ugettext as _
from wtforms import BooleanField, TextField, IntegerField, RadioField
from wtforms import SelectField, validators, DecimalField, PasswordField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField

from baruwa.forms import myhostname
from baruwa.lib.misc import get_languages
from baruwa.forms.messages import MultiCheckboxField
from baruwa.forms import Form, TIMEZONE_TUPLES, REQ_MSG, LOWSPAM_DESC
from baruwa.forms import check_domain, check_domain_alias, STATUS_DESC, \
    HIGHSPAM_DESC
from baruwa.lib.regex import DOM_RE, MSGSIZE_RE, NUMORSPACE_RE, IPV4_RE


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

VIRUS_ACTIONS = (
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

SMTP_CALL_DESC = _("""Enable SMTP callout based
recipient verification. The recipients of
email sent to this domain will be checked
on the delivery server(s) configured for
the domain""")

LDAP_CALL_DESC = _("""Enable LDAP email address
verification for this domain. If enabled,
the recipients of email sent to this domain
will be checked aganist an LDAP directory prior
to being accepted, you need to have an
authentication server entry of type LDAP for
this to work correctly.""")

SITE_URL_DESC = _("""Customize the url that is used
in links generated for reports for users in this
domain. This url needs to be configured to point
to this system otherwise it will create incorrect
links in the reports. This must be the full base
url for example https://antispam.example.com""")

VIRUS_CHECKS_DESC = _("""Enable or disable virus checks
for this domain""")

VIRUS_CHECKS_AT_SMTP_DESC = _("""Run Virus Checks at
SMTP time, if disabled virus checks will be ran after
SMTP time allowing you to quarantine virus infected
messages""")

SPAM_CHECKS_DESC = _("""Enable or disable spam checks
for this domain""")

SPAM_ACTIONS_DESC = _("""What to do with messages that
score at or above the 'Probable spam score' but
below the 'Definite spam score', these scores
can be set below""")

HIGHSPAM_ACTIONS_DESC = _("""What to do with messages that
score at or above the 'Definite spam score',
this score can be set below""")

VIRUS_ACTIONS_DESC = _("""What to do with messages that
are virus infected""")

MSG_SIZE_DESC = _("""The maximum message size for
email sent to and from email addresses under
this domain, the format is 2B,2K,2M for
bytes,kilobytes,megabytes respectively""")

DELIVERY_MODES_DESC = _("""If the domain has more than one
server where clean mail is delivered how should
the deliveries be done, load balanced and failover
delivery is supported""")

LANGUAGES_DESC = _("""The default language for users
under this domain""")

TIMEZONE_DESC = _("""The default timezone for users
under this domain""")

REPORT_DESC = _("""How often PDF reports should
be sent""")

ORGS_DESC = _("""The organizations that own
this domain""")

DOMAIN_DESC = _("""Domain name for which email is
processed""")

DOMAIN_ALIAS_DESC = _("""Domain alias name""")


def check_server_addr(form, field):
    "check server address"
    if not DOM_RE.match(field.data) and not IPV4_RE.match(field.data):
        raise validators.ValidationError(
            _('Invalid Domain name or IP address'))


class AddDomainForm(Form):
    """Add domain"""
    name = TextField(_('Domain name'), [validators.Required(message=REQ_MSG),
                    validators.Regexp(DOM_RE,
                    message=_('Invalid Domain name')),
                    check_domain,
                    check_domain_alias],
                    description=DOMAIN_DESC)
    site_url = TextField(_('Site url'),
                        [validators.Required(message=REQ_MSG),
                        validators.URL()],
                        description=SITE_URL_DESC,
                        default=myhostname)
    status = BooleanField(_('Enabled'), default=True,
                        description=STATUS_DESC)
    smtp_callout = BooleanField(_('Enable SMTP callouts'), default=False,
                        description=SMTP_CALL_DESC)
    ldap_callout = BooleanField(_('Enable LDAP callouts'), default=False,
                        description=LDAP_CALL_DESC)
    virus_checks = BooleanField(_('Enable Virus checks'), default=True,
                        description=VIRUS_CHECKS_DESC)
    virus_checks_at_smtp = BooleanField(_('Run Virus checks at SMTP time'),
                        default=True,
                        description=VIRUS_CHECKS_AT_SMTP_DESC)
    spam_checks = BooleanField(_('Enable SPAM checks'), default=True,
                        description=SPAM_CHECKS_DESC)
    spam_actions = SelectField(_('What to do with probable spam'),
                        choices=list(SPAM_ACTIONS),
                        description=SPAM_ACTIONS_DESC)
    highspam_actions = SelectField(_('What to do with definite spam'),
                        choices=list(SPAM_ACTIONS),
                        description=HIGHSPAM_ACTIONS_DESC)
    virus_actions = SelectField(_('What to do with Virus infected messages'),
                        choices=list(VIRUS_ACTIONS),
                        description=VIRUS_ACTIONS_DESC)
    low_score = DecimalField(_('Probable spam score'), places=1, default=0,
                        description=LOWSPAM_DESC)
    high_score = DecimalField(_('Definite spam score'), places=1, default=0,
                        description=HIGHSPAM_DESC)
    message_size = TextField(_('Maximum Message Size'),
                        [validators.Regexp(MSGSIZE_RE,
                            message=_('Invalid message size, '
                                    'only B, K, M accepted'))],
                        default='0',
                        description=MSG_SIZE_DESC)
    delivery_mode = SelectField(_('Multi destination delivery mode'),
                        choices=DELIVERY_MODES,
                        description=DELIVERY_MODES_DESC)
    language = SelectField(_('Language'),
                        choices=LANGUAGES, default='en',
                        description=LANGUAGES_DESC)
    timezone = SelectField(_('Default Timezone'),
                        choices=TIMEZONE_TUPLES,
                        description=TIMEZONE_DESC)
    report_every = SelectField(_('Report frequency'),
                        choices=REPORT_FREQ, default='3',
                        description=REPORT_DESC)
    organizations = QuerySelectMultipleField(_('Organizations'),
                        get_label='name',
                        allow_blank=True,
                        description=ORGS_DESC)


class EditDomainForm(Form):
    """Edit/Delete a domain"""
    name = TextField(_('Domain name'), [validators.Required(message=REQ_MSG),
                    validators.Regexp(DOM_RE,
                    message=_('Invalid Domain name'))],
                    description=DOMAIN_DESC)
    # not inheriting from AddDomainForm cause it mangles output if we do
    site_url = TextField(_('Site url'),
                        [validators.Required(message=REQ_MSG),
                        validators.URL()],
                        description=SITE_URL_DESC)
    status = BooleanField(_('Enabled'), default=True,
                            description=STATUS_DESC)
    smtp_callout = BooleanField(_('Enable SMTP callouts'), default=False,
                            description=SMTP_CALL_DESC)
    ldap_callout = BooleanField(_('Enable LDAP callouts'), default=False,
                            description=LDAP_CALL_DESC)
    virus_checks = BooleanField(_('Enable Virus checks'), default=True,
                            description=VIRUS_CHECKS_DESC)
    virus_checks_at_smtp = BooleanField(_('Run Virus checks at SMTP time'),
                        default=True,
                        description=VIRUS_CHECKS_AT_SMTP_DESC)
    spam_checks = BooleanField(_('Enable SPAM checks'), default=True,
                            description=SPAM_CHECKS_DESC)
    spam_actions = SelectField(_('What to do with probable spam'),
                            choices=list(SPAM_ACTIONS),
                            description=SPAM_ACTIONS_DESC)
    highspam_actions = SelectField(_('What to do with definite spam'),
                            choices=list(SPAM_ACTIONS),
                            description=HIGHSPAM_ACTIONS_DESC)
    virus_actions = SelectField(_('What to do with Virus infected messages'),
                        choices=list(VIRUS_ACTIONS),
                        description=VIRUS_ACTIONS_DESC)
    low_score = DecimalField(_('Probable spam score'), places=1, default=0,
                            description=LOWSPAM_DESC)
    high_score = DecimalField(_('Definite spam score'), places=1, default=0,
                            description=HIGHSPAM_DESC)
    message_size = TextField(_('Maximum Message Size'),
                            [validators.Regexp(MSGSIZE_RE,
                            message=_('Invalid message size, '
                                    'only B, K, M accepted'))],
                            default='0',
                            description=MSG_SIZE_DESC)
    delivery_mode = SelectField(_('Multi destination delivery mode'),
                            choices=DELIVERY_MODES,
                            description=DELIVERY_MODES_DESC)
    language = SelectField(_('Language'), choices=LANGUAGES, default='en',
                            description=LANGUAGES_DESC)
    timezone = SelectField(_('Default Timezone'), choices=TIMEZONE_TUPLES,
                            description=TIMEZONE_DESC)
    report_every = SelectField(_('Report frequency'),
                            choices=REPORT_FREQ, default='3',
                            description=REPORT_DESC)
    organizations = QuerySelectMultipleField(_('Organizations'),
                            get_label='name',
                            allow_blank=True,
                            description=ORGS_DESC)


class BulkDelDomains(Form):
    """Bulk domains delete"""
    domainid = MultiCheckboxField('')
    whatdo = RadioField('', choices=[('delete', _('delete'),),
                                    ('disable', _('disable'),),
                                    ('enable', _('enable'),), ])


class AddDomainAlias(Form):
    """Add domain alias"""
    name = TextField(_('Domain alias name'),
                    [validators.Required(message=REQ_MSG),
                    validators.Regexp(DOM_RE,
                    message=_('Invalid Domain name')),
                    check_domain,
                    check_domain_alias],
                    description=DOMAIN_ALIAS_DESC)
    status = BooleanField(_('Enabled'), default=True,
                    description=_("""Enable or disable this entry"""))
    domain = QuerySelectField(_('Parent domain'),
                    get_label='name',
                    allow_blank=False,
                    description=_("""The domain for which this is an
                    alias."""))


class EditDomainAlias(AddDomainAlias):
    """Override to make status work"""
    name = TextField(_('Domain alias name'),
                    [validators.Required(message=REQ_MSG),
                    validators.Regexp(DOM_RE,
                    message=_('Invalid Domain name')), ],
                    description=DOMAIN_ALIAS_DESC)
    status = BooleanField(_('Enabled'),
                    description=STATUS_DESC)


class DelDomainAlias(AddDomainAlias):
    """Override to make prevent validation"""
    name = TextField(_('Domain alias name'),
                    [validators.Required(message=REQ_MSG),
                    validators.Regexp(DOM_RE,
                    message=_('Invalid Domain name')), ],
                    description=_("""Domain alias name"""))


class AddDeliveryServerForm(Form):
    """Add delivery server"""
    address = TextField(_('Server address'),
                    [validators.Required(message=REQ_MSG),
                    check_server_addr],
                    description=_("""The hostname or IP address of a server
                    to which the clean email is delivered"""))
    protocol = SelectField(_('Protocol'), choices=list(DELIVERY_PROTOCOLS),
                    description=_("""The protocol used to deliver the clean
                    email"""))
    port = IntegerField(_('Port'), default=25,
                    description=_("""The port to which the destination
                    server is listening, the default is the standard
                    SMTP port 25"""))
    enabled = BooleanField(_('Enabled'), default=True,
                    description=STATUS_DESC)


class LinkDeliveryServerForm(Form):
    """Link delivery server"""
    server = QuerySelectField(_('Server address'), get_label='address')


class AddAuthForm(Form):
    """Add auth server"""
    address = TextField(_('Server address'),
                [validators.Required(message=REQ_MSG),
                check_server_addr],
                description=_("""The hostname or IP address of the server
                to which to authenticate"""))
    protocol = SelectField(_('Protocol'), choices=list(AUTH_PROTOCOLS),
                description=_("""The protocol used to authenticate the
                user"""))
    port = TextField(_('Port'), [validators.Regexp(NUMORSPACE_RE,
                message=_('must be numeric'))],
                description=_("""The port to connect to on the server"""))
    enabled = BooleanField(_('Enabled'), default=True,
                description=STATUS_DESC)
    split_address = BooleanField(_('Split address'), default=False,
                description=_("""Enabling this will split the address
                and only send the user part to the authentication
                server for example for user@example.com will authenticate
                as user"""))
    user_map_template = TextField(_('Username map template'),
                description=_("""This enables you to support complex
                usernames such as those created by some control panels
                like: user.domainouwner or \DOMAIN\username.
                Substitution is supported, refer to the documentation
                for the available variables"""))


class AddLDAPSettingsForm(Form):
    """Add ldap settings"""
    basedn = TextField(_('Base DN'), [validators.Required(message=REQ_MSG)],
                    description=_("""Base DN, The DN under which to search.
                                    This is the top most level you want to
                                    search under. Something like:
                                    ou=users,dc=example,dc=org"""))
    nameattribute = TextField(_('Username attribute'),
                            [validators.Required(message=REQ_MSG)],
                            default='uid',
                            description=_("""The attribute in the records that
                            holds the username default is uid which is used
                            by OpenLDAP, Active directory uses sAMAccountName
                            """))
    emailattribute = TextField(_('Email attribute'),
                            [validators.Required(message=REQ_MSG)],
                            default='mail',
                            description=_("""The attribute that holds the
                            email address default is mail which is used
                            by OpenLDAP and Active directory"""))
    binddn = TextField(_('Bind DN'),
                        description=_("""The DN used to bind to the directory
                        """))
    bindpw = PasswordField(_('Bind password'),
                        description=_("""The password used to authenticate
                        binding to the directory. Enter 'None' if you want
                        to use a blank password"""))
    usetls = BooleanField(_('Use TLS'), default=False,
                        description=_("""Use TLS on the connection, This
                        uses STARTTLS on the plain connection port"""))
    usesearch = BooleanField(_('Search for UserDN'), default=False,
                        description=_("""Search for the Users DN using
                        the username attribute, then bind to that user
                        DN with the password the user supplied. Use this
                        if the user DN's in your directory do not take
                        the format cn=<nameattribute>,<basedn>"""))
    searchfilter = TextAreaField(_('Auth Search Filter'),
                        description=_("""A filter to limit the number
                        of entries that are searched, only entries that
                        match this filter will be searched during
                        authentication"""))
    search_scope = SelectField(_('Auth Search Scope'),
                        choices=list(SEARCH_SCOPE),
                        description=_("""The SCOPE setting is the
                        starting point of an LDAP search and the
                        depth from the base DN to which the search
                        should occur."""))
    emailsearchfilter = TextAreaField(_('Email Search Filter'),
                        description=_("""A filter to limit the number
                        of entries that are searched, only entries that
                        match this filter will be searched during
                        email address verification"""))
    emailsearch_scope = SelectField(_('Email Search Scope'),
                        choices=list(SEARCH_SCOPE),
                        description=_("""The SCOPE setting is the
                        starting point of an LDAP search and the
                        depth from the base DN to which the search
                        should occur."""))
    # enabled = BooleanField(_('Enabled'), default=True)

    def validate_search_scope(form, field):
        "validate search scope"
        if form.usesearch and field.data not in ['subtree', 'onelevel']:
            raise validators.ValidationError(
                    _('Unsupported search scope'))


class AddRadiusSettingsForm(Form):
    """Add radius settings"""
    secret = PasswordField(_('Radius secret'),
            [validators.Required(message=REQ_MSG)],
            description=_("""The radius shared secret, this is
            used to encrypt communications to the radius server"""))
    timeout = IntegerField(_('Request timeout'), default=0,
            description=_("""The connection timeout setting, timeout
            connection after this number of seconds"""))
