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
"Accounts audit messages"

from baruwa.lib.misc import _


ADDACCOUNT_MSG = _("User account: %(u)s created")
UPDATEACCOUNT_MSG = _("User account: %(u)s updated")
DELETEACCOUNT_MSG = _("User account: %(u)s deleted")
PASSWORDCHANGE_MSG = _("User account: %(u)s password changed")
ADDRADD_MSG = _("Alias: %(a)s added to account: %(ac)s")
ADDRUPDATE_MSG = _("Email Alias: %(a)s on account: %(ac)s updated")
ADDRDELETE_MSG = _("Email Alias: %(a)s on account: %(ac)s deleted")
ACCOUNTEXPORT_MSG = _("Accounts exported")
ACCOUNTIMPORT_MSG = _("Accounts imported")
ACCOUNTLOGIN_MSG = _("User: %(u)s logged in")

__all__ = [
    'ADDACCOUNT_MSG',
    'UPDATEACCOUNT_MSG',
    'DELETEACCOUNT_MSG',
    'PASSWORDCHANGE_MSG',
    'ADDRADD_MSG',
    'ADDRUPDATE_MSG',
    'ADDRDELETE_MSG',
    'ACCOUNTEXPORT_MSG',
    'ACCOUNTIMPORT_MSG',
    'ACCOUNTLOGIN_MSG',
]