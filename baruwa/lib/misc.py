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
"""Misc functions"""

import os
import json
import magic
import psutil
import socket
import string
import gettext
import binascii

import GeoIP

from random import choice
from textwrap import wrap

from IPy import IP
from pylons import config
from babel.core import Locale
from webhelpers.html import escape
from eventlet.green import subprocess
from webhelpers.number import format_byte_size
from webhelpers.text import wrap_paragraphs, truncate

from baruwa.lib.regex import USTRING_RE

REPORTS = {
            '1': {'address': 'from_address', 'sort': 'count'},
            '2': {'address': 'from_address', 'sort': 'size'},
            '3': {'address': 'from_domain', 'sort': 'count'},
            '4': {'address': 'from_domain', 'sort': 'size'},
            '5': {'address': 'to_address', 'sort': 'count'},
            '6': {'address': 'to_address', 'sort': 'size'},
            '7': {'address': 'to_domain', 'sort': 'count'},
            '8': {'address': 'to_domain', 'sort': 'size'},
            '9': {'address': '', 'sort': ''},
            '10': {'address': 'clientip', 'sort': 'count'},
            '11': {'address': '', 'sort': ''}
            }
BASEPATH = os.path.dirname(os.path.dirname(__file__))
I18NPATH = os.path.join(BASEPATH, 'i18n')


def get_processes(process_name):
    "Gets running processes by process name"
    count = 0
    for process in psutil.process_iter():
        try:
            if (process.name == process_name or
                process.name.startswith(process_name)):
                count += 1
        except psutil.error.AccessDenied:
            pass
    return count


def get_config_option(search_option):
    """
    Returns a MailScanner config setting from the
    config file
    """
    msconf = config.get('ms.config', '/etc/MailScanner/MailScanner.conf')
    quickpeek = config.get('ms.quickpeek', '/usr/sbin/Quick.Peek')

    option = "'%s'" % search_option
    pipe = subprocess.Popen([quickpeek, option, msconf],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)
    val = pipe.communicate()[0]
    pipe.wait(timeout=10)
    return val.strip()


def ipaddr_is_valid(ip):
    """
    Checks the validity of an IP address
    """
    try:
        IP(ip)
        return True
    except ValueError:
        return False

def check_language(lang_code):
    "Check existance of language files"
    if gettext.find('baruwa', I18NPATH, [lang_code]) is not None:
        return True
    return False


def get_languages():
    "return a list of supported languages"
    langs = (lang for lang in os.listdir(I18NPATH)
            if os.path.isdir(os.path.join(I18NPATH, lang)))
    def dictify(lang, name):
        "map function to make dict"
        retdict = {}
        retdict[lang] = name
        return retdict

    return (dictify(lang, Locale(lang).display_name)
            for lang in langs if check_language(lang))


def geoip_lookup(ipaddr):
    "Perform a GeoIP lookup of an IP address"
    try:
        if IP(ipaddr).version() == 6:
            ipv6db = config.get('baruwa.ipv6db',
            '/usr/share/GeoIP/GeoIPv6.dat')
            gip = GeoIP.open(ipv6db, GeoIP.GEOIP_MEMORY_CACHE)
            country_code = gip.country_code_by_addr_v6(ipaddr) or ''
            country_name = gip.country_name_by_name_v6(ipaddr)
        else:
            gip = GeoIP.new(GeoIP.GEOIP_MEMORY_CACHE)
            country_code = gip.country_code_by_addr(ipaddr) or ''
            country_name = gip.country_name_by_addr(ipaddr)
        country_code = country_code.lower()
        return country_name, country_code
    except (GeoIP.error, AttributeError, ValueError):
        return ('', '')


def jsonify_msg_list(element):
    """
    Fixes the converting error in converting
    DATETIME objects to JSON
    """
    value = 'white'
    if (element.spam and not element.highspam and not element.blacklisted
        and not element.nameinfected and not element.otherinfected 
        and not element.virusinfected):
        value = 'spam'
    if element.highspam and (not element.blacklisted):
        value = 'highspam'
    if element.whitelisted:
        value = 'whitelisted'
    if element.blacklisted:
        value = 'blacklisted'
    if (element.nameinfected or element.virusinfected or
        element.otherinfected):
        value = 'infected'
    if not element.scaned:
        value = 'gray'
    if (element.spam and (not element.blacklisted) 
        and (not element.virusinfected) 
        and (not element.nameinfected) 
        and (not element.otherinfected)):
        status = _('Spam')
    if element.blacklisted:
        status = _('BL')
    if (element.virusinfected or 
           element.nameinfected or 
           element.otherinfected):
        status = _('Infected')
    if ((not element.spam) and (not element.virusinfected) 
           and (not element.nameinfected) 
           and (not element.otherinfected) 
           and (not element.whitelisted)):
        status = _('Clean')
    if element.whitelisted:
        status = _('WL')
    if not element.scaned:
        status = _('NS')
    return dict(
                id=element.id,
                timestamp=element.timestamp.strftime('%A, %d %b %Y %H:%M:%S %Z'),
                sascore=element.sascore,
                size=format_byte_size(element.size),
                subject=truncate(escape(element.subject), 50),
                from_address=wrap_paragraphs(escape(element.from_address), 32),
                to_address=wrap_paragraphs(escape(element.to_address), 32),
                style=value,
                status=status,
            )
    # return mydict


def quote_js(jstr, quote_double_quotes=False):
    "Quote JS"

    def fix(match):
        "fixup js quoute"
        return r"\u%04x" % ord(match.group(1))

    if type(jstr) == str:
        jstr = jstr.decode('utf-8')
    elif type(jstr) != unicode:
        raise TypeError(jstr)
    jstr = jstr.replace('\\', '\\\\')
    jstr = jstr.replace('\r', '\\r')
    jstr = jstr.replace('\n', '\\n')
    jstr = jstr.replace('\t', '\\t')
    jstr = jstr.replace("'", "\\'")
    if quote_double_quotes:
        jstr = jstr.replace('"', '&quot;')
    return str(USTRING_RE.sub(fix, jstr))


def paginator2json(paginator):
    "convert paginator to json"
    value = {}
    for key in ['first_item', 'first_page', 'item_count', 'items_per_page',
                'last_item', 'last_page', 'next_page', 'page', 'page_count',
                'previous_page']:
        value[key] = getattr(paginator, key)
    left = max(value['first_page'], (value['page'] - 2))
    right = min(value['page_count'], (value['page'] + 2))
    value['page_nums'] = list(xrange(left, right + 1))
    return value


def convert_to_json(pages, direction, order_by, section):
    "convert messages action response json"
    value = paginator2json(pages)
    value['direction'] = direction
    value['order_by'] = order_by
    value['items'] = [jsonify_msg_list(item) for item in pages.items]
    value['section'] = section
    return json.dumps(value)


def convert_dom_to_json(pages, orgid):
    "convert domains action response to json"
    value = paginator2json(pages)
    value['items'] = [item.tojson() for item in pages.items]
    value['orgid'] = orgid
    return json.dumps(value)


def convert_acct_to_json(pages, orgid):
    "convert accounts action response to json"
    value = paginator2json(pages)
    def mkdict(item):
        "Make it a dict"
        if item.account_type == 1:
            user_icon = 'imgs/user_admin.png'
        elif item.account_type == 2:
            user_icon = 'imgs/user_dadmin.png'
        else:
            user_icon = 'imgs/user.png'
        return dict(id=item.id,
                username=item.username,
                fullname=item.firstname + ' ' + item.lastname,
                email=item.email,
                statusimg='imgs/tick.png' if item.active else 'imgs/minus.png',
                userimg=user_icon,
            )
    value['items'] = map(mkdict, pages.items)
    value['orgid'] = orgid
    return json.dumps(value)


def convert_org_to_json(pages):
    "convert org"
    value = paginator2json(pages)
    value['items'] = [dict(id=item.id, name=item.name)
                    for item in pages.items]
    return json.dumps(value)


def convert_settings_to_json(pages):
    "conver settings"
    value = paginator2json(pages)
    value['items'] = [item.tojson() for item in pages.items]
    return json.dumps(value)


def convert_list_to_json(pages, list_type):
    "convert list"
    value = paginator2json(pages)
    value['items'] = [item.tojson() for item in pages.items]
    value['listname'] = ('Approved senders' if int(list_type) == 1
                        else 'Banned senders')
    value['list_type'] = list_type
    return json.dumps(value)


def _(value):
    "dummy translator"
    return value


def crc32(value):
    "return crc32 value"
    return binascii.crc32(value) & 0xffffffff


def iscsv(handle):
    "check file magic"
    mime = magic.Magic(mime=True)
    kind = mime.from_buffer(handle.read(1024))
    handle.seek(0)
    return kind == 'text/plain' or kind == 'text/csv'


def check_num_param(req):
    "Check and return the num get param"
    num = req.GET.get('n', None)
    try:
        num = int(num)
    except TypeError:
        num = None
    return num


def wrap_string(value, length=100):
    "wrap a string value"
    length = int(length)
    if len(value) > length:
        value = '\n'.join(wrap(value, length))
    return value


def get_ipaddr(value):
    "resolve a hostname to IP address"
    try:
        socket.setdefaulttimeout(60)
        ipaddr = socket.gethostbyname(value)
    except (ValueError, socket.error, socket.gaierror, socket.timeout):
        ipaddr = None
    return ipaddr


def mkpasswd(length=15):
    """Generate a random password"""
    chars = "!#$%()*+,-./:;=?@^_`{|}~"
    return ''.join([choice(string.letters + string.digits + chars)
            for i in range(length)])