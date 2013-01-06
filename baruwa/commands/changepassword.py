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
"Change a user's password"

import sys
import getpass

import cracklib

from optparse import OptionValueError

from sqlalchemy.orm.exc import NoResultFound

from baruwa.model.meta import Session
from baruwa.model.accounts import User
from baruwa.commands import BaseCommand


def check_username(option, opt_str, value, parser):
    "check the username"
    if len(value) < 3:
        raise OptionValueError("Username: %s is too short" % value)

    setattr(parser.values, option.dest, value)


class ChangePassword(BaseCommand):
    "Change a user's password"
    BaseCommand.parser.add_option('-u', '--username',
        help='Account Username',
        dest='username',
        type='str',
        action='callback',
        callback=check_username,)
    summary = """Change a user's password"""
    group_name = 'baruwa'

    def command(self):
        "run command"
        self.init()
        if self.options.username is None:
            print "\nProvide an username\n"
            print self.parser.print_help()
            sys.exit(2)
        try:
            user = Session\
                    .query(User)\
                    .filter(User.username == self.options.username)\
                    .filter(User.local == True)\
                    .one()
            pass1 = getpass.getpass(prompt="Please enter the password:")
            pass2 = getpass.getpass(prompt="Please reenter the password:")
            pass1 = pass1.strip()
            pass2 = pass2.strip()
            assert pass1 and pass2, "Passwords cannot be blank"
            assert pass1 == pass2, "Passwords entered do not match"
            cracklib.VeryFascistCheck(pass1)
            user.set_password(pass1)
            Session.add(user)
            Session.commit()
            print "The account password has been updated"
        except NoResultFound:
            print >> sys.stderr, ("No local user found with username %s" %
                                    self.options.username)
        except AssertionError, message:
            print >> sys.stderr, str(message)
        except ValueError, message:
            print >> sys.stderr, str(message)