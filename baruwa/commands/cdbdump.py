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
"Dump MTA cdb files"
import os
import sys

import cdb

from baruwa.commands import BaseCommand


def cdbdump(cdb_o):
    "cdb dump"
    rec = cdb_o.each()
    while rec:
        print "%s => %s" % (rec[0], rec[1])
        rec = cdb_o.each()
    print


class DumpCDBFileCommand(BaseCommand):
    "Dump CDB file command"
    BaseCommand.parser.add_option('-f', '--filename',
        help='Name of the cdb file to dump',
        dest='filename',
        type='str',)

    summary = 'Display the contents Exim cdb lookup files'
    group_name = 'baruwa'

    def command(self):
        "command"
        self.init()
        filename = self.options.filename
        if filename is None:
            print "\nThe cdb filename is required\n"
            print self.parser.print_help()
            sys.exit(2)

        if not os.path.isfile(filename):
            print "\nThe cdb filename %s does not exist\n" % filename
            print self.parser.print_help()
            sys.exit(2)

        print "*" * 10, 'Dumping: %s' % filename, "*" * 10
        cdbo = cdb.init(filename)
        cdbdump(cdbo)
