#!/usr/bin/env python
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
"Reconcile messages on disk with database"

import os
import sys

from optparse import OptionParser
from ConfigParser import SafeConfigParser

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from baruwa.lib.regex import EXIM_MSGID_RE
from baruwa.lib.misc import get_config_option
from baruwa.model.messages import Message, Archive


def load_config(conffile):
    "load pylons configuration"
    config_parser = SafeConfigParser()
    config_parser.read(conffile)
    return config_parser


def main(argv):
    "Main function"
    parser = OptionParser()
    parser.add_option('-c', '--config', dest="settingsfile",
                    help="Baruwa configuration file",
                    default='/etc/baruwa/production.ini')
    parser.add_option('-e', '--disable-exim-messageid', dest="eximid",
                    help="Disable the filtering of exim message id's",
                    action="store_false",
                    default=True)
    parser.add_option('-d', '--delete-ophans', dest="delmsg",
                    help="Delete ophaned messages",
                    action="store_true",
                    default=False)
    options, _ = parser.parse_args(argv)
    basepath = os.path.dirname(os.path.dirname(__file__))
    configfile = os.path.join(basepath, options.settingsfile)

    if not os.path.exists(configfile):
        print parser.print_help()
        print "The config file %s does not exist" % configfile
        sys.exit(2)

    config = load_config(configfile)
    sqlalchemyurl = config.get('app:main', 'sqlalchemy.url',
                                vars=dict(here=basepath))
    engine = create_engine(sqlalchemyurl)
    Session = sessionmaker(bind=engine)
    session = Session()
    quarantine = get_config_option('QuarantineDir')
    count = 0
    for (dirname, _, files) in os.walk(quarantine):
        for mail in files:
            if mail == 'message':
                mail = os.path.dirname(dirname)
            if mail.startswith('.'):
                continue
            if options.eximid and not EXIM_MSGID_RE.match(mail):
                continue
            count += 1
            msg = session.query(Message.id)\
                .filter(Message.messageid == mail)\
                .all()
            if not msg:
                msg = session.query(Archive.id)\
                    .filter(Archive.messageid == mail)\
                    .all()
            if not msg:
                print "%(m)s not found" % dict(m=mail)
                filename = os.path.join(dirname, mail)
                if options.delmsg:
                    os.unlink(filename)
    print '-' * 100
    print '%(c)d messages found' % dict(c=count)


if __name__ == '__main__':
    # run the thing
    main(sys.argv)
