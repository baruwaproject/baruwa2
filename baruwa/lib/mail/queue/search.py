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

"search queue directories for a specific message"
import os

from baruwa.lib.misc import get_config_option


def search_queue(msgid, direction):
    "search queue"
    if direction == 1:
        qdir = get_config_option('Incoming Queue Dir')
    else:
        qdir = get_config_option('Outgoing Queue Dir')
    header = os.path.join(qdir, '%s-H' % msgid)
    data = os.path.join(qdir, '%s-D' % msgid)
    if os.path.exists(header) and os.path.exists(data):
        return header
    return None