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
"""Baruwa forms"""

import pytz

from datetime import timedelta

from pylons import config
from sqlalchemy.orm.exc import NoResultFound
from wtforms.validators import ValidationError
from pylons.i18n.translation import lazy_ugettext as _
# from pylons.i18n.translation import ugettext, ungettext
from wtforms.ext.csrf.session import SessionSecureForm

from baruwa.model.meta import Session
from baruwa.model.accounts import User
from baruwa.lib.mail.freemail import FREE_DOMAINS
from baruwa.model.domains import Domain, DomainAlias

TIMEZONE_TUPLES = [(timz, timz) for timz in pytz.common_timezones]
REQ_MSG = _(u'This field is required.')
EMAIL_MSG = _(u'Invalid email address.')
DISALLOWED_USERNAMES = ['mailer-daemon', 'postmaster', 'bin', 'daemon',
                        'adm', 'lp', 'sync', 'shutdown', 'halt', 'mail',
                        'news', 'uucp', 'operator', 'games', 'gopher',
                        'ftp', 'nobody', 'radiusd', 'nut', 'dbus', 'vcsa',
                        'canna', 'wnn', 'rpm', 'nscd', 'pcap', 'apache',
                        'webalizer', 'dovecot', 'fax', 'quagga', 'radvd',
                        'pvm', 'amanda', 'privoxy', 'ident', 'named', 'xfs',
                        'gdm', 'mailnull', 'postgres', 'sshd', 'smmsp',
                        'postfix', 'netdump', 'ldap', 'squid', 'ntp',
                        'mysql', 'desktop', 'rpcuser', 'rpc', 'nfsnobody',
                        'ingres', 'system', 'toor', 'manager', 'dumper',
                        'abuse', 'newsadm', 'newsadmin', 'usenet', 'ftpadm',
                        'ftpadmin', 'ftp-adm', 'ftp-admin', 'www', 'webmaster',
                        'noc', 'security', 'hostmaster', 'info', 'marketing',
                        'sales', 'support', 'decode', 'root']


# class BaruwaTranslator(object):
#     """Custom wtforms translator"""
#     def gettext(self, string):
#         "overide gettext"
#         return ugettext(string)
# 
#     def ngettext(self, singular, plural, n):
#         "overide ngettext"
#         return ungettext(singular, plural, n)


class Form(SessionSecureForm):
    """Use as base for other forms"""
    SECRET_KEY = config.get('beaker.session.secret',
                'EPj12jpfj9Gx1XjnyLxwBBSQfnQ9DJYe0Ym')
    TIME_LIMIT = timedelta(minutes=120)

    # def _get_translations(self):
    #     "Use the baruwa translator"
    #     return BaruwaTranslator()

def is_freemail(domain):
    "check if domain is a freemail domain"
    if domain in FREE_DOMAINS:
        raise ValidationError(_('The domain is a free mail domain'))


def check_domain(form, field):
    "check domain"
    try:
        is_freemail(field.data)
        Session.query(Domain.name).filter(Domain.name == field.data).one()
        raise ValidationError(_('The domain already exists on the system'))
    except NoResultFound:
        pass


def check_domain_alias(form, field):
    "check domain alias"
    try:
        Session.query(DomainAlias.name)\
            .filter(DomainAlias.name == field.data)\
            .one()
        raise ValidationError(_('The domain already exists on the system'))
    except NoResultFound:
        pass


def check_username(form, field):
    "check the username"
    try:
        if '@' in field.data:
            raise ValidationError(_('The username cannot be an email address'))
        if field.data in DISALLOWED_USERNAMES:
            raise ValidationError(_('The username is not available'))
        Session.query(User).filter(User.username == field.data).one()
        raise ValidationError(_('The username is not available'))
    except NoResultFound:
        pass


def check_email(form, field):
    "check the email address"
    try:
        domain = field.data.split('@')[-1]
        Session.query(Domain).filter(Domain.name == domain).one()
        raise ValidationError(
                _('Email from a domain that is already registered'))
    except NoResultFound:
        pass
