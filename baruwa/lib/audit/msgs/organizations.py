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
"Organizations audit messages"

from baruwa.lib.misc import _


ADDORG_MSG = _("Organization: %(o)s added")
UPDATEORG_MSG = _("Organization: %(o)s updated")
DELETEORG_MSG = _("Organization: %(o)s deleted")
IMPORTORG_MSG = _("Organization: %(o)s domains imported")
#EXPORTORG_MSG = _("Organization: %(o)s domains exported")
ADDRELAY_MSG = _("Relay: %(r)s added")
UPDATERELAY_MSG = _("Relay: %(r)s updated")
DELETERELAY_MSG = _("Relay: %(r)s deleted")


__all__ = [
    'ADDORG_MSG',
    'UPDATEORG_MSG',
    'DELETEORG_MSG',
    'IMPORTORG_MSG',
    #'EXPORTORG_MSG',
    'ADDRELAY_MSG',
    'UPDATERELAY_MSG',
    'DELETERELAY_MSG',
]