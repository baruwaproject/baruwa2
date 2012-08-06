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

from datetime import timedelta

from wtforms.ext.csrf.session import SessionSecureForm
from pylons import config


class Form(SessionSecureForm):
    """Use as base for other forms"""
    SECRET_KEY = config.get('beaker.session.secret',
                'EPj12jpfj9Gx1XjnyLxwBBSQfnQ9DJYe0Ym')
    TIME_LIMIT = timedelta(minutes=120)


