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
"Settings audit messages"

from baruwa.lib.misc import _


ADDACCSIG_MSG = _("Account: %(u)s signature created")
UPDATEACCSIG_MSG = _("Account: %(u)s signature updated")
DELETEACCSIG_MSG = _("Account: %(u)s signature deleted")
ADDDOMSIG_MSG = _("Domain: %(d)s signature created")
UPDATEDOMSIG_MSG = _("Domain: %(d)s signature updated")
DELETEDOMSIG_MSG = _("Domain: %(d)s signature deleted")
HOSTADD_MSG = _("Node: %(n)s created")
HOSTUPDATE_MSG = _("Node: %(n)s updated")
HOSTDELETE_MSG = _("Node: %(n)s deleted")
HOSTSETTING_MSG = _("Scanner %(svr)s setting: %(s)s set to %(a)s")
#SCANNERSETTING_MSG = _("Default Scanner setting: %(s)s set to %(as)s")
DKIMGEN_MSG = _("DKIM keys generated for: %(d)s")
DKIMENABLED_MSG = _("DKIM signing enabled for: %(d)s")
DKIMDISABLED_MSG = _("DKIM signing disabled for: %(d)s")


__all__ = [
    'HOSTADD_MSG',
    'HOSTUPDATE_MSG',
    'HOSTDELETE_MSG',
    'HOSTSETTING_MSG',
    #'SCANNERSETTING_MSG',
    'ADDACCSIG_MSG',
    'UPDATEACCSIG_MSG',
    'DELETEACCSIG_MSG',
    'ADDDOMSIG_MSG',
    'UPDATEDOMSIG_MSG',
    'DELETEDOMSIG_MSG',
    'DKIMGEN_MSG',
    'DKIMENABLED_MSG',
    'DKIMDISABLED_MSG',
]