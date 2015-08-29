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
"base class for commands"
import os
import pwd
import grp
import sys
import hashlib
import warnings

import pytz
import arrow
import cracklib

from optparse import OptionValueError
from distutils.sysconfig import get_python_lib
from gettext import NullTranslations, translation

from mako.lookup import TemplateLookup
from pylons.error import handle_mako_error
from paste.script.command import Command, BadCommand
from paste.deploy import loadapp, appconfig

from baruwa.lib.regex import EMAIL_RE

warnings.filterwarnings("ignore", category=DeprecationWarning)


def get_mako_lookup(tmpldir, cache_dir):
    """Get Mako lookup"""
    mako_lookup = TemplateLookup(
                    directories=[tmpldir],
                    error_handler=handle_mako_error,
                    module_directory=cache_dir,
                    input_encoding='utf-8',
                    default_filters=['escape'],
                    output_encoding='utf-8',
                    encoding_errors='replace',
                    imports=['from webhelpers.html import escape'])
    return mako_lookup


def change_user(user, group):
    """Switch to the baruwa user"""
    try:
        uid = pwd.getpwnam(user).pw_uid
        gid = grp.getgrnam(group).gr_gid
        os.setgid(gid)
        os.setuid(uid)
    except OSError, error:
        print >> sys.stderr, "Failed to change to %s:%s %s" % \
            (user, group, str(error))
        sys.exit(2)


def gen_uuid(account):
    "Generates a uuid"
    seed = "%s%s%s" % (account.username, account.email,
                        arrow.utcnow().datetime)
    messageuuid = hashlib.sha1(seed).hexdigest()
    return messageuuid


def workout_path():
    "Workout the path to the baruwa installation"
    base = get_python_lib(1)
    if not os.path.exists(os.path.join(base, 'baruwa', 'templates')):
        import baruwa as bwp
        base = os.path.dirname(os.path.dirname(os.path.abspath(bwp.__file__)))
    return base


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


def get_theme_dirs(domains, themebase, cache_base):
    "Get theme directories"
    tmpldir = None
    assetdir = None
    cachedir = None
    for domain in domains:
        if domain.status is False:
            continue
        tmpldir = os.path.join(themebase,
                                'templates',
                                domain.name)
        assetdir = os.path.join(themebase,
                                'assets',
                                domain.name)
        if os.path.exists(tmpldir) and os.path.exists(assetdir):
            cachedir = os.path.join(cache_base, 'templates', domain.name)
            return (tmpldir, assetdir, cachedir)
    return None, None, None


def check_email(option, opt_str, value, parser):
    "check validity of email address"
    if not EMAIL_RE.match(value):
        raise OptionValueError("%s is not a valid email address" % value)

    setattr(parser.values, option.dest, value)


def check_timezone(option, opt_str, value, parser):
    "check the validity of a timezone"
    if value not in pytz.common_timezones:
        raise OptionValueError("%s is not a valid timezone" % value)

    setattr(parser.values, option.dest, value)


def check_password(option, opt_str, value, parser):
    "check the password strength"
    try:
        cracklib.VeryFascistCheck(value)
    except ValueError, message:
        raise OptionValueError("%s." % str(message)[3:])

    setattr(parser.values, option.dest, value)


def check_username(option, opt_str, value, parser):
    "check the username"
    if '@' in value:
        raise OptionValueError("Username cannot contain domain")
    if len(value) < 3:
        raise OptionValueError("Username: %s is too short" % value)

    setattr(parser.values, option.dest, value)


def check_username_len(option, opt_str, value, parser):
    "check the username"
    if len(value) < 3:
        raise OptionValueError("Username: %s is too short" % value)

    setattr(parser.values, option.dest, value)


def check_period(option, opt_str, value, parser):
    "Check the validity of the period option"
    if value is None:
        raise OptionValueError("Option: %s is required" % option)
    if value not in ['daily', 'weekly', 'monthly']:
        raise OptionValueError("%s is not a valid option for %s\n"
                                "\t\t\tSupported options are "
                                "[daily, weekly, monthly]"
                                % (value, opt_str))
    setattr(parser.values, option.dest, value)


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
        else:
            config_file = self.args[0]

        if not os.path.isfile(config_file):
            raise BadCommand('%sError: CONFIG_FILE not found at: %s, '
                             'Please specify a CONFIG_FILE' %
                             (self.parser.get_usage(), config_file))

        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        here = os.path.dirname(here)
        config_name = 'config:' + config_file
        self.logging_file_config(config_file)
        conf = appconfig(config_name, relative_to=here)
        conf.update(dict(app_conf=conf.local_conf,
                    global_conf=conf.global_conf))

        wsgiapp = loadapp(config_name, relative_to=here)
        self.conf = conf
