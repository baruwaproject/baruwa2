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
"Status forms"

from wtforms import SelectField
from pylons.i18n.translation import lazy_ugettext as _

from baruwa.forms import Form
from baruwa.forms.messages import MultiCheckboxField

QUEUE_OPTS = (
    ('0', _('Select action')),
    ('deliver', _('Deliver')),
    ('bounce', _('Bounce')),
    ('freeze', _('Hold')),
    ('delete', _('Delete')),
)


class MailQueueProcessForm(Form):
    "mail queue process form"
    id = MultiCheckboxField('')
    queue_action = SelectField('', choices=QUEUE_OPTS, default='none')
