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
"""Regexes
"""

import re


EMAIL_RE = re.compile(
    r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"
    r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|'
    r'\\[\001-011\013\014\016-\177])*")'
    r'@(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?$',
    re.IGNORECASE)

LOCAL_PART_RE = re.compile(
    r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"
    r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|'
    r'\\[\001-011\013\014\016-\177])*")',
    re.IGNORECASE)

DOM_RE = re.compile(
        r'^(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?$',
        re.IGNORECASE
    )

IPV4_RE = re.compile(
    r'^(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}$'
    )

USER_RE = re.compile(
    r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*|"
    r"^([\001-\010\013\014\016-\037!#-\[\]-\177]|"
    r"\\[\001-011\013\014\016-\177])*)$",
    re.IGNORECASE)

ADDRESS_RE = re.compile(
    r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"
    r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|'
    r'\\[\001-011\013\014\016-\177])*")'
    r'@(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?$'
    r'|^(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?$',
    re.IGNORECASE)

HOST_OR_IPV4_RE = re.compile(
    r'^(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}$'
    r'|^(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?$',
    re.IGNORECASE
)

IPV4_NET_OR_RANGE_RE = re.compile(
    r'^[.:\da-f]+\s*-\s*[.:\da-f]+$|'
    r'^([.:\da-f]+)\s*\/\s*([.:\da-f]+)$',
    re.IGNORECASE
)

RBL_RE = re.compile(r'^spam\,\s+(.+)\,\s+SpamAssassin|^spam\,\s+(.+)$')

SARULE_RE = re.compile(r'((\w+)(\s)(\-?\d{1,2}\.\d{1,2}))')

SARULE_SCORE_RE = re.compile(r'^score\s+(?P<ruleid>\S+)\s+(?P<scores>.+)$')

LEARN_RE = re.compile(r'autolearn=((\w+\s\w+)|(\w+))')

IP_RE = re.compile(r'(([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3}))')

SPAM_REPORT = re.compile(r'\((.+?)\)')

HEADER_RE = re.compile(r'(^Received:|X-Originating-IP:)')

FIND_IPS_RE = re.compile(
    r'[^=](?:\[)?((?:\b[0-9]{1,3}\b)\.(?:\b[0-9]{1,3}\b)\.(?:\b[0-9]{1,3}\b)\.(?:\b[0-9]{1,3}\b(?![;])))(?:\])?'
    r'|(?:(?:\[IPv6\:)([^]]*)(?:\]))|(?:(?:\[)([.:\da-f]+)(?:\]))'
)

RULE_DESCRIPTION_RE = re.compile(r'^describe\s+(?P<ruleid>\S+)\s+(?P<description>.+)$')

CONFIG_RE = re.compile(r'[^%a-zA-Z0-9]')

MSGID_RE = re.compile(r'^(?:Message-Id\:\s+.+)$', re.IGNORECASE)

HTMLTITLE_RE = re.compile(r'<title>.+</title>', re.IGNORECASE)

QDIR = re.compile(r"^\d{8}$")

MSGSIZE_RE = re.compile(r"^\d+(M|K|B)?$")

NUMORSPACE_RE = re.compile(r'^(\s?|\d+)$')

USTRING_RE = re.compile(u"([\u0080-\uffff])")

DBURL_RE = re.compile(
    r"(?P<name>[\w\+]+)://(?:(?P<username>[^:/]*)"
    r"(?::(?P<password>[^/]*))?@)?(?:(?P<host>[^/:]*)"
    r"(?::(?P<port>[^/]*))?)?(?:/(?P<database>.*))?"
)

EXIM_DELIVERY_RE = re.compile(
    r'^(?P<message_id>[A-Za-z0-9]{6}-[A-Za-z0-9]{6}-[A-Za-z0-9]{2})'
    r' (?P<rest>(?P<direction>[^ ]+).*)$'
)

EXIM_MSGID_RE = re.compile(r'^[A-Za-z0-9]{6}-[A-Za-z0-9]{6}-[A-Za-z0-9]{2}')

EXIM_HOST_RE = re.compile(r'^.+ \[(?P<destination>.+?)\](.+$)?')

CLEANRE = re.compile(r'<[^>]*?>')

CLEANQRE = re.compile(r'^(\s+)?@.+$')

EXIMQ_HEADER_RE = re.compile(r'^(\d{3,})([^\d])\s(.*)')

EXIMQ_NUM_RE = re.compile(r'(\d+)')

EXIMQ_BLANK_RE = re.compile(r'^$')

EXIMQ_XX_RE = re.compile(r'^XX$')

I18N_HEADER = re.compile(r'(?P<i18n>=\?.*?\?[QqBb]\?.*\?=)(?P<email>.+)?$')

I18N_HEADER_MATCH = re.compile(r'=\?.*?\?[QqBb]\?.*\?=$')

BAYES_INFO_RE = re.compile(
    r'(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+non-token data: (.+)'
)

USER_TEMPLATE_MAP_RE = re.compile(r'%\(user\)s')

DOM_TEMPLATE_MAP_RE = re.compile(r'%\(domain\)s')

LOADER_FIX_RE = re.compile(r'(%)\|(\w+)\|(s|d)')

APOP_RE = re.compile(r"^.+\<\d+\.\d+\@.+\>$")

USER_DN_RE = re.compile('<dn:(?P<b64dn>[A-Za-z0-9+/]+=*)>')

PROXY_ADDR_RE = re.compile(r'(SMTP|smtp):')

SQL_URL_RE = re.compile(r'''
        (?P<name>[\w\+]+)://
        (?:
            (?P<user>[^:/]*)
            (?::(?P<passwd>[^/]*))?
        @)?
        (?:
            (?P<host>[^/:]*)
            (?::(?P<port>[^/]*))?
        )?
        (?:/(?P<db>.*))?
        '''
        , re.X)

def clean_regex(rule):
    """
    Formats a regex for parsing MailScanner
    configs
    """
    if rule == 'default' or rule == '*':
        rule = '*@*'
    if not '@' in rule:
        if re.match(r'^\*', rule):
            rule = "*@%s" % rule
        else:
            rule = "*@%s" % rule
    if re.match(r'^@', rule):
        rule = "*%s" % rule
    if re.match(r'@$', rule):
        rule = "%s*" % rule
    rule = re.sub(r'\*', '.*', rule)
    rule = "^%s\.?$" % rule
    return rule