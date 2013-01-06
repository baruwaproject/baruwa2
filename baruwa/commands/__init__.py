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
"base class for commands"
import os
import warnings
#import sys

from gettext import NullTranslations, translation

from paste.script.command import Command, BadCommand
from paste.deploy import loadapp, appconfig

warnings.filterwarnings("ignore", category=DeprecationWarning)


def set_lang(lang, pkgname, localedir):
    "Set language"
    if not lang:
        translator = NullTranslations()
    else:
        if not isinstance(lang, list):
            lang = [lang]
        translator = translation(
                        pkgname,
                        localedir,
                        languages=lang
                    )
    return translator

def get_conf_options(conf, prefix='mail.'):
    "Return a dict of mailer options"
    options = dict((key[len(prefix):], conf[key])
                   for key in conf
                   if key.startswith(prefix))
    return options


class BaseCommand(Command):
    "Base command"
    min_args = 0
    max_args = 1
    
    parser = Command.standard_parser(verbose=True)
    parser.set_conflict_handler("resolve")

    def init(self):
        "init"
        if len(self.args) == 0:
            config_file = '/etc/baruwa/production.ini'
            if not os.path.isfile(config_file):
                raise BadCommand('%sError: CONFIG_FILE not found at: %s, '
                                 'Please specify a CONFIG_FILE' % \
                                 (self.parser.get_usage(), config_file))
        else:
            config_file = self.args[0]

        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        here = os.path.dirname(here)
        config_name = 'config:' + config_file
        self.logging_file_config(config_file)
        conf = appconfig(config_name, relative_to=here)
        conf.update(dict(app_conf=conf.local_conf,
                    global_conf=conf.global_conf))
        #sys.path.insert(0, here)

        wsgiapp = loadapp(config_name, relative_to=here)
        self.conf = conf