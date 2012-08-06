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

import ast

from celery.loaders.base import BaseLoader
from pylons import config

from baruwa.lib.regex import LOADER_FIX_RE

to_pylons = lambda x: x.replace('_', '.').lower()
to_celery = lambda x: x.replace('.', '_').upper()

LIST_PARAMS = """CELERY_IMPORTS ADMINS""".split()


class PylonsSettingsProxy(object):
    """Pylons Settings Proxy

    Proxies settings from pylons.config

    """
    def __getattr__(self, key):
        "get attr"
        pylons_key = to_pylons(key)
        try:
            value = config[pylons_key]
            if key in LIST_PARAMS:
                return value.split()
            return self.type_converter(value)
        except KeyError:
            raise AttributeError(pylons_key)

    def get(self, key):
        "get atte"
        try:
            return self.__getattr__(key)
        except AttributeError:
            return None

    def __getitem__(self, key):
        try:
            return self.__getattr__(key)
        except AttributeError:
            raise KeyError()

    def __setattr__(self, key, value):
        pylons_key = to_pylons(key)
        config[pylons_key] = value

    def __setitem__(self, key, value):
        self.__setattr__(key, value)

    def type_converter(self, value):
        #cast to int
        if value.isdigit():
            return int(value)

        #cast to bool
        if value.lower() in ['true', 'false']:
            return value.lower() == 'true'

        #cast to dict
        if value.startswith('{') and value.endswith('}'):
            return ast.literal_eval(str(value))

        #cast to list
        if value.startswith('(') and value.endswith(')'):
            return ast.literal_eval(str(value))

        #allow logging format strings
        if '%' in value:
            return LOADER_FIX_RE.sub(r"\1(\2)\3", value)

        return value

class PylonsLoader(BaseLoader):
    """Pylons celery loader

    Maps the celery config onto pylons.config

    """
    def read_configuration(self):
        self.configured = True
        return PylonsSettingsProxy()

    def on_worker_init(self):
        """
        Import task modules.
        """
        self.import_default_modules()
