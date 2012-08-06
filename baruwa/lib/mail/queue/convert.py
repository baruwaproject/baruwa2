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

"convert exim queue files to mbox file"

import os
import datetime

from baruwa.lib.regex import EXIMQ_HEADER_RE, EXIMQ_NUM_RE
from baruwa.lib.regex import EXIMQ_XX_RE, EXIMQ_BLANK_RE


class Exim2Mbox(list):
    """Init, takes path of header file"""
    def __init__(self, headerfile):
        list.__init__([])
        assert (os.path.exists(headerfile) and os.path.isfile(headerfile)), \
        'The headerfile: %s either does not exist or is not a file' % \
        headerfile
        self.headerfile = headerfile

    def __call__(self):
        "process the files"
        j = None
        k = None
        l = None
        # for index, line in enumerate(message):
        with open(self.headerfile) as handle:
            index = 0
            for line in handle:
                index += 1
                if index == 1:
                    msgid = line.strip().rstrip('-H')
                    continue
                if index == 3:
                    now = datetime.datetime.today()
                    self.append('From %s %s\n' % (line.strip(),
                            now.strftime("%a %b %d %T %Y")))
                    continue
                if EXIMQ_XX_RE.match(line):
                    j = 1
                    continue
                if j and EXIMQ_NUM_RE.match(line):
                    m = EXIMQ_NUM_RE.match(line)
                    k = m.group()
                    k = int(k)
                    j -= 1
                    continue
                if k:
                    k -= 1
                    self.append('X-BaruwaFW-From: %s' % line)
                    continue
                if EXIMQ_BLANK_RE.match(line):
                    continue
                match = EXIMQ_HEADER_RE.match(line)
                if match:
                    groups = match.groups()
                    if groups[1] == '*':
                        l = 0
                    else:
                        l = int(groups[0]) - len(groups[2]) + 1
                    self.append(groups[2] + '\n')
                    continue
                else:
                    if l:
                        self.append(line)
                        l -= len(line)

        dirname = os.path.dirname(self.headerfile)
        with open('%s/%s-D' % (dirname, msgid)) as handle:
            body = handle.readlines()
        self.append('\n')
        body.pop(0)
        self.extend(body)
        return ''.join(self)


if __name__ == '__main__':
    # run it
    from optparse import OptionParser
    usage = "usage: %prog filename"
    parser = OptionParser(usage)
    options, args = parser.parse_args()
    if len(args) != 1:
        parser.error("incorrect number of arguments")
    try:
        filename = args[0]
        convertor = Exim2Mbox(filename)
        mbox = convertor()
        print mbox
    except AssertionError, error:
        print error
        