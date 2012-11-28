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
"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to templates as 'h'.
"""
# Import helpers as desired, or define your own, ie:
#from webhelpers.html.tags import checkbox, password
from webhelpers.html import literal, HTML
from webhelpers.text import wrap_paragraphs, truncate
from webhelpers.number import format_byte_size, percent_of
from webhelpers.pylonslib.flash import Flash as _Flash, Message as Msg
#from webhelpers.pylonslib.secure_form import secure_form as form
from webhelpers.pylonslib.minify import stylesheet_link, javascript_link
from webhelpers.html.tags import link_to, end_form, submit, checkbox
from webhelpers.html.tags import select, text, hidden, password, image
from webhelpers.html.tags import BR, form, radio

from baruwa.lib.templates.helpers import (relayed_via, sa_learned,
    spam_report, value_yes_no, get_rbl_name, do_pagination,
    spam_actions, do_breaks, enabled_or_not, country_flag,
    get_hostname, service_status, media_url, highlight_errors,
    wrap_headers, pager_img, pager_select, portable_img,
    datetimeformat, format_date)
from baruwa.lib.misc import get_languages

flash = _Flash()


def flash_ok(message):
    flash(message)


def flash_info(message):
    flash(message)


def flash_alert(message):
    flash(message, 'error')


def linebreaksbr(value):
    value = value.split('\n')
    return literal(BR).join(value)
