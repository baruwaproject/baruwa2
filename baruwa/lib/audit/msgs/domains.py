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
"Domains audit messages"

from baruwa.lib.misc import _


ADDDOMAIN_MSG = _("Domain: %(d)s created")
UPDATEDOMAIN_MSG = _("Domain: %(d)s updated")
DELETEDOMAIN_MSG = _("Domain: %(d)s deleted")
ADDDOMALIAS_MSG = _("Domain Alias: %(d)s created")
UPDATEDOMALIAS_MSG = _("Domain Alias: %(d)s updated")
DELETEDOMALIAS_MSG = _("Domain Alias: %(d)s deleted")
EXPORTDOM_MSG = _("Domain: %(d)s accounts exported")
# IMPORTDOM_MSG = _("Domain: %(d)s accounts imported")
ADDDELSVR_MSG = _("Domain: %(d)s Delivery server: %(ds)s added")
UPDATEDELSVR_MSG = _("Domain: %(d)s Delivery server: %(ds)s updated")
DELETEDELSVR_MSG = _("Domain: %(d)s Delivery server: %(ds)s deleted")
ADDAUTHSVR_MSG = _("Domain: %(d)s AUTH server: %(ds)s added")
UPDATEAUTHSVR_MSG = _("Domain: %(d)s AUTH server: %(ds)s updated")
DELETEAUTHSVR_MSG = _("Domain: %(d)s AUTH server: %(ds)s deleted")
AUTHSETTINGS_MSG = _("Domain: %(d)s AUTH settings updated for: %(a)s")

__all__ = [
    'ADDDOMAIN_MSG',
    'UPDATEDOMAIN_MSG',
    'DELETEDOMAIN_MSG',
    'ADDDOMALIAS_MSG',
    'UPDATEDOMALIAS_MSG',
    'DELETEDOMALIAS_MSG',
    'EXPORTDOM_MSG',
    # 'IMPORTDOM_MSG',
    'ADDDELSVR_MSG',
    'UPDATEDELSVR_MSG',
    'DELETEDELSVR_MSG',
    'ADDAUTHSVR_MSG',
    'UPDATEAUTHSVR_MSG',
    'DELETEAUTHSVR_MSG',
    'AUTHSETTINGS_MSG',
]