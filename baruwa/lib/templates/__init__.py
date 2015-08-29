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
"Templating functions"

import os

from pylons import config
from mako.lookup import TemplateLookup


def render(template, **kwargs):
    "Render a mako template"
    root = os.path.dirname(os.path.dirname(os.path\
                .dirname(os.path.abspath(__file__))))
    cdir = config.get('cache_dir', '/var/lib/baruwa/data')
    # cdir = os.path.dirname(cdir)
    mylookup = TemplateLookup(directories=[os.path.join(root, 'templates')],
                            module_directory=os.path.join(cdir, 'templates'),
                            imports=['from baruwa.lib.regex import DOM_RE',
                                    'from baruwa.lib.misc import MS_ACTIONS'],
                            input_encoding='utf-8')
    mytemplate = mylookup.get_template(template)
    return mytemplate.render(**kwargs)
