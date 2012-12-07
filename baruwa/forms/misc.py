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
"Misc forms"

from wtforms import SelectField, TextField, FileField
from pylons.i18n.translation import lazy_ugettext as _

from baruwa.forms import Form

NO_ITEMS = ((50, 50), (20, 20), (10, 10),)


class ItemsPerPage(Form):
    "Items per page selector"
    items_per_page = SelectField(_('Show items'), choices=list(NO_ITEMS))


class Fmgr(Form):
    "FM upload form"
    handle = FileField(_('Image file'))
    newName = TextField(_('File name'))