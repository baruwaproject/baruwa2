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
"Date manipulation functions"

import pytz

from datetime import datetime


SHTFMT = "%Y-%m-%d %I:%M:%S"
TZFMT = "%Y-%m-%d %H:%M:%S %z (%Z)"


def now():
    """
    Returns an aware datetime.datetime
    """
    return datetime.utcnow().replace(tzinfo=pytz.utc)


def convert_date(date, tmzone):
    "Convert UTC date to timezone"
    tmzone = make_tz(tmzone)
    return pytz.UTC.normalize(date).astimezone(tmzone)


def make_tz(tzinfo):
    "Convert timezone string to timezone"
    if isinstance(tzinfo, basestring):
        tzinfo = pytz.timezone(tzinfo)
    return tzinfo


def startday():
    "Return start time"
    date = now()
    return date.replace(hour=00, minute=00, second=00)


def endday():
    "Return end time"
    date = now()
    return date.replace(hour=23, minute=59, second=59)


def ustartday(tmz):
    "Get users localized start day in UTC"
    currentdate = datetime.now(make_tz(tmz))
    currentdate = currentdate.replace(hour=00, minute=00, second=00)
    return pytz.utc.normalize(currentdate.astimezone(pytz.utc))


def uendday(tmz):
    "Get users localized end day in UTC"
    currentdate = datetime.now(make_tz(tmz))
    currentdate = currentdate.replace(hour=23, minute=59, second=59)
    return pytz.utc.normalize(currentdate.astimezone(pytz.utc))
