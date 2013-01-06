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

""" Helper functions for mail operations """
import socket

import pytz
#from textwrap import wrap

from IPy import IP
from webhelpers.html import escape, HTML, literal
from webhelpers.html.tags import image, select
from pylons.i18n.translation import _
from pylons import url, config
from beaker.cache import cache_region
from pyparsing import Word, alphas, restOfLine, Suppress
from pyparsing import Group, SkipTo, Or, CaselessLiteral

from baruwa.model import Session
from baruwa.model.messages import SARule
from baruwa.lib.misc import geoip_lookup, wrap_string
from baruwa.lib.caching_query import FromCache
from baruwa.lib.regex import RBL_RE, SARULE_RE
from baruwa.lib.regex import LEARN_RE, SPAM_REPORT, FIND_IPS_RE

socket.setdefaulttimeout(1.0)


def media_url():
    "return the configured media url"
    return config['baruwa.media.url']


def service_status(value):
    "Service status"
    if value:
        name = 'status_ok'
    else:
        name = 'caution'
    return image(url('img', name=name), alt='value')


@cache_region('long_term', 'get-hostname')
def get_hostname(value):
    "display hostname"
    try:
        IP(value).version()
        if value == '127.0.0.1' or value == '::1':
            hostname = 'localhost'
        else:
            socket.setdefaulttimeout(60)
            hostname = socket.gethostbyaddr(value)[0]
    except (ValueError, socket.error, socket.gaierror, socket.timeout):
        hostname = _('unknown')
    return hostname


@cache_region('long_term', 'country-flag')
def country_flag(value):
    "return country flag"
    value = value.strip()
    try:
        IP(value).version()
        cname, ccode = geoip_lookup(value)
        if not ccode:
            ccode = 'unknown'
        tag = media_url() + url('flag', country=ccode)
        return image(tag, cname, title=cname)
    except ValueError:
        return ''


def _generate_relay_html(hosts):
    "Format the result"
    if hosts:
        rows = hosts
    else:
        rows = []
    return rows


def get_ips(headers):
    "Return a list of IP address from mail headers"
    ips = []
    end = Word(alphas, alphas + "-") + ":" + restOfLine
    begin = Or((Suppress("Received: "),
                Suppress(CaselessLiteral("X-Originating-IP: ")))
            ) + restOfLine
    token = Group(begin + SkipTo(end, False))
    #hdrs = []
    def parse_headers():
        "parse headers"
        for msg_hdr in token.searchString(headers):
            for hdr in msg_hdr:
                fullhdr = ' '.join(hdr)
                fullhdr = fullhdr.replace('\n', '')
                yield fullhdr
    hdrs = parse_headers()
    def extract_ips(header):
        "Extract headers"
        match = FIND_IPS_RE.findall(header)
        match.reverse()
        ips.extend((address[0] or address[1] or address[2]
                    for address in match))
    def dedup(seq):
        "remove duplicate IP's"
        seen = set()
        seen_add = seen.add
        return [val for val in seq if val not in seen and not seen_add(val)]
    map(extract_ips, hdrs)
    return dedup(ips)


def ip_details(ipaddr):
    "Return IP type and country for an IP address"
    try:
        country_code = ''
        country_name = ''
        hostname = ''
        iptype = IP(ipaddr).iptype()
        if (iptype != "LOOPBACK" and ipaddr != '127.0.0.1'
            and iptype != "LINKLOCAL"):
            socket.setdefaulttimeout(60)
            #hostname = socket.gethostbyaddr(ipaddr)[0]
            hostname = get_hostname(ipaddr)
            if iptype != "PRIVATE":
                country_name, country_code = geoip_lookup(ipaddr)
        elif iptype == "LINKLOCAL":
            hostname = _('IPv6 Link local address')
    except (socket.gaierror, socket.timeout, socket.error, ValueError):
        if 'iptype' in locals() and iptype == "PRIVATE":
            hostname = _("RFC1918 Private address")
        else:
            hostname = _("Reverse lookup failed")
    finally:
        details = dict(ip_address=ipaddr,
                    hostname=hostname or literal('unknown'),
                    country_code=country_code or 'unknown',
                    country_name=country_name or '',
                    media_url=media_url())
    return details


def relayed_via(headers):
    "display relayed via"
    ips = get_ips(headers)
    hosts = [ip_details(ip)
            for ip in ips if ip != '127.0.0.1' and ip != '::1']
    return _generate_relay_html(hosts)


def sa_learned(value):
    "indicate learning status"
    if not value:
        HTML.span(_('N'), class_='negative')

    match = LEARN_RE.search(value)
    if match:
        return (HTML.span(_('Y'), class_='positive') +
            literal('&nbsp;') + '(%s)' % escape(match.group(1)))
    else:
        return HTML.span(_('N'), class_='negative')


def get_rule_info(rules):
    "get spamassassin rules"
    if not rules:
        return []

    def gen_rules(rule):
        "map to generate rules"
        rule = rule.strip()
        match = SARULE_RE.match(rule)
        description = ""
        if match:
            rule = match.groups()[1]
            rule_obj = Session.query(SARule)\
                        .options(FromCache('sql_cache_long', rule))\
                        .get(rule)
            if rule_obj:
                description = rule_obj.description
            return dict(rule=rule, score=match.groups()[3],
                            description=description)
    tmplist = (gen_rules(rule) for rule in rules)
    return (rule for rule in tmplist if rule)


def spam_report(value):
    "print spam report"
    if not value:
        return ""

    match = SPAM_REPORT.search(value)
    if match:
        rules = get_rule_info(match.groups()[0].split(','))
        rows = (rule for rule in rules)
        return rows
    return []


def value_yes_no(value):
    "Creates the Y/N span"
    if value:
        return HTML.span(_('Y'), class_='positive')
    return HTML.span(_('N'), class_='negative')


def enabled_or_not(value):
    "Enabled status"
    if value:
        return image(media_url() + 'imgs/tick.png',
                    _('Enabled'),
                    class_="positio")
    return image(media_url() + 'imgs/minus.png',
                    _('Disabled'),
                    class_="positio")


def spam_actions(msg, spam_type):
    "Returns the spam actions"
    if spam_type == 1:
        return value_yes_no(msg.spam)
    else:
        return value_yes_no(msg.highspam)


def get_rbl_name(value):
    "get the rbl name"
    rbl = ''
    match = RBL_RE.search(value)
    if match:
        if match.group(1):
            rbl = escape(match.group(1))
        else:
            rbl = escape(match.group(2))
    return rbl


def do_pagination(pager, adjacent_pages=2):
    """
    Generates the pagination links
    """
    startpage = max(pager.page - adjacent_pages, 1)
    if startpage <= 3:
        startpage = 1

    endpage = pager.page + adjacent_pages + 1
    if endpage >= pager.page_count - 1:
        endpage = pager.page_count

    page_numbers = (num for num in range(startpage, endpage)
        if num > 0 and num <= pager.page_count)
    return page_numbers


def do_breaks(value):
    "Converts , to <br />"
    value = value.split(',')
    return literal('<br />').join(value)


def highlight_errors(field, **kwargs):
    "Highlight a form field when error occurs"
    if field.errors:
        kwargs.pop('class', '')
        return field(class_='error', **kwargs)
    return field(**kwargs)


def wrap_headers(value, length=100):
    "wrap the headers"
    headers = value.split('\n')
    rstring = []
    for header in headers:
        if len(header) > length:
            header = wrap_string(header, length)
        rstring.append(header)
    return ('\n'.join(rstring))


def pager_img(direction):
    "generate img html"
    return literal(
        '<img src="%(m)simgs/%(d)s_pager.png" alt="%(a)s" title="%(a)s" />' %
        dict(m=media_url(), d=direction, a=direction.capitalize()))


def pager_select(name, selected):
    "generate select field"
    no_items = ((100, 100), (50, 50), (20, 20), (10, 10),)
    return select(name, selected, no_items)


def portable_img(name, alt, **kwargs):
    "image with media path"
    return image(media_url() + name, alt, **kwargs)


def datetimeformat(value, format='%Y-%m-%d %H:%M:%S'):
    "return formated date"
    return value.strftime(format)


def format_date(date, timezone):
    "return a localized datetime"
    return pytz.UTC.normalize(date).astimezone(timezone)
