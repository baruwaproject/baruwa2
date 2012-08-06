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
"""Setup the baruwa application"""
import os
import sys
import signal
import logging
import getpass

import cracklib
import pylons.test

from sqlalchemy.sql import text
from sqlalchemy.exc import ProgrammingError

from baruwa.model.accounts import User
from baruwa.model.settings import Server, ConfigSettings
from baruwa.lib.regex import ADDRESS_RE
from baruwa.model.meta import Session, Base
from baruwa.config.environment import load_environment

log = logging.getLogger(__name__)

class TimeoutException(Exception): 
    pass


def setup_app(command, conf, variables):
    """Place any commands to setup baruwa here"""
    # Don't reload the app if it was loaded under the testing environment
    if not pylons.test.pylonsapp:
        load_environment(conf.global_conf, conf.local_conf)

    # Create the tables if they don't already exist
    print '-' * 100
    log.info("Creating tables")
    Base.metadata.create_all(bind=Session.bind)
    basepath = os.path.dirname(os.path.dirname(__file__))
    # Create the custom functions
    print '-' * 100
    log.info("Creating custom functions")
    sqlfile = os.path.join(basepath,
                        'baruwa',
                        'config',
                        'sql',
                        'functions.sql')
    if os.path.exists(sqlfile):
        with open(sqlfile, 'r') as handle:
            sql = handle.read()
            try:
                conn = Session.connection()
                conn.execute(text(sql))
                Session.commit()
            except ProgrammingError:
                Session.rollback()
    defaultserver = Session.query(Server)\
                    .filter(Server.hostname == 'default')\
                    .all()
    # Create the Mailscanner SQL config views
    print '-' * 100
    log.info("Populating initial sql")
    sqlfile = os.path.join(basepath,
                        'baruwa',
                        'config',
                        'sql',
                        'integration.sql')
    if os.path.exists(sqlfile):
        with open(sqlfile, 'r') as handle:
            sql = handle.read()
        for sqlcmd in sql.split(';'):
            if sqlcmd:
                try:
                    sqlcmd = "%s;" % sqlcmd
                    Session.execute(text(sqlcmd))
                    Session.commit()
                except ProgrammingError:
                    Session.rollback()
    if not defaultserver:
        log.info("Creating the default settings node")
        dfls = Server('default', True)
        Session.add(dfls)
        confserial = ConfigSettings('confserialnumber',
                                    'ConfSerialNumber',
                                    0)
        confserial.value = 1
        confserial.server_id = 1
        Session.add(confserial)
        Session.commit()
        log.info("Default settings node created !")
    admin = Session.query(User).filter(User.account_type==1).all()
    if not admin:
        def timeout_handler(signum, frame):
            raise TimeoutException()

        old_handler = signal.signal(signal.SIGALRM, timeout_handler) 
        signal.alarm(30)
        try:
            create_user = raw_input('Do you want to configure '
                                'an admin account? (Y/N): ')
        except (TimeoutException, EOFError):
            sys.exit(0)
        finally:
            signal.signal(signal.SIGALRM, old_handler)
        signal.alarm(0)
        if str(create_user).lower() == 'y':
            print '-' * 100
            log.info("Creating initial admin account")
            value_map = {'username': True, 'password1': True,
                        'password2': True, 'firstname': False,
                        'lastname': False, 'email': True}
            values = {}

            def get_input(field, required):
                "Get user input"
                prompt = "Please enter the %s:" % field
                while 1:
                    if field in ['password1', 'password2']:
                        value = getpass.getpass(prompt=prompt)
                    else:
                        value = raw_input(prompt)
                    if not required:
                        break
                    if required and value.strip() != "":
                        if not field in ['email', 'password1', 'password2']:
                            break
                        if field == 'email':
                            if not ADDRESS_RE.match(value):
                                print "Please provide a valid email address."
                            else:
                                break
                        if field == 'password1':
                            try:
                                cracklib.VeryFascistCheck(value)
                            except ValueError, message:
                                print str(message)
                            else:
                                break
                        if field == 'password2':
                            if values['password1'] == value:
                                break
                            else:
                                print 'password2 does not match password1'
                return value

            for attr in value_map:
                value = get_input(attr, value_map[attr])
                values[attr] = value
            user = User(values['username'], values['email'])
            for name in ['firstname', 'lastname']:
                if values[name]:
                    setattr(user, name, values[name])
            user.internal = True
            user.active = True
            user.local = True
            user.account_type = 1
            user.set_password(values['password1'])
            Session.add(user)
            Session.commit()
