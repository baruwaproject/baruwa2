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
"Create an admin user account"

import os
import sys

from cracklib import VeryFascistCheck
from sqlalchemy.exc import IntegrityError

from baruwa.model.meta import Session
from baruwa.model.accounts import User
from baruwa.commands import BaseCommand, check_username
from baruwa.commands import check_password, check_email, check_timezone


class CreateAdminUser(BaseCommand):
    "Create an admin user account"
    BaseCommand.parser.add_option('-u', '--username',
        help='Account Username',
        dest='username',
        type='str',
        action='callback',
        callback=check_username,)
    BaseCommand.parser.add_option('-p', '--password',
        help='Account Password',
        dest='password',
        type='str',
        action='callback',
        callback=check_password,)
    BaseCommand.parser.add_option('-e', '--email',
        help='Account email address',
        dest='email',
        type='str',
        action='callback',
        callback=check_email,)
    BaseCommand.parser.add_option('-t', '--timezone',
        help='Account Timezone',
        dest='timezone',
        type='str',
        action='callback',
        default='UTC',
        callback=check_timezone,)
    summary = """Create an administrator account"""
    group_name = 'baruwa'

    def command(self):
        "run command"
        self.init()
        try:
            for option in ['username', 'password', 'email']:
                if getattr(self.options, option) is None:
                    if option == 'password' and \
                        'BARUWA_ADMIN_PASSWD' in os.environ and \
                        os.environ['BARUWA_ADMIN_PASSWD']:
                        VeryFascistCheck(os.environ['BARUWA_ADMIN_PASSWD'])
                        self.options.password = \
                                            os.environ['BARUWA_ADMIN_PASSWD']
                        continue
                    print "\nOption: %s is required\n" % option
                    print self.parser.print_help()
                    sys.exit(2)

            user = User(username=self.options.username,
                        email=self.options.email)
            user.active = True
            user.timezone = self.options.timezone
            user.account_type = 1
            user.local = True
            user.set_password(self.options.password)
            Session.add(user)
            Session.commit()
            print "Admin account %s created" % self.options.username
        except ValueError, message:
            print >> sys.stderr, "%s." % str(message)[3:]
            sys.exit(2)
        except IntegrityError:
            Session.rollback()
            print >> sys.stderr, ("The user %s already exists" %
                                    self.options.username)
            sys.exit(2)
        finally:
            Session.close()
