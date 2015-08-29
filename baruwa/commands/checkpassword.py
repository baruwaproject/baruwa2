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
"Check a user's password"

import os
import sys

from sqlalchemy.sql.expression import true
from sqlalchemy.orm.exc import NoResultFound

from baruwa.model.meta import Session
from baruwa.model.accounts import User
from baruwa.commands import BaseCommand, check_username_len


class CheckPassword(BaseCommand):
    "Check a user's password"
    BaseCommand.parser.add_option('-u', '--username',
        help='Account Username',
        dest='username',
        type='str',
        action='callback',
        callback=check_username_len,)
    summary = """Check a user's password"""
    group_name = 'baruwa'

    def command(self):
        "run command"
        self.init()
        if self.options.username is None:
            print >> sys.stderr, "\nProvide an username\n"
            print self.parser.print_help()
            sys.exit(126)

        try:
            user = Session\
                    .query(User)\
                    .filter(User.username == self.options.username)\
                    .filter(User.local == true())\
                    .one()
            if user.validate_password(os.environ['BARUWA_ADMIN_PASSWD']):
                print >> sys.stderr, "The account password is valid"
                sys.exit(0)
            else:
                print >> sys.stderr, "The account password is invalid"
                sys.exit(2)
        except KeyError:
            print >> sys.stderr, "BARUWA_ADMIN_PASSWD env variable not set"
            sys.exit(126)
        except NoResultFound:
            print >> sys.stderr, ("No local user found with username %s" %
                                    self.options.username)
            sys.exit(126)
        finally:
            Session.close()
