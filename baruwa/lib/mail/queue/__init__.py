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

"""Shared queue management functions"""

import os
import re
import codecs

from datetime import datetime
from email.Header import decode_header

from eventlet.green import subprocess


SUBJECT_RE = re.compile(r'(?:\d+\s+Subject):(.+)')
MSGLOG_RE = re.compile(r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})'
                        '\s+(?:.+\s(?:defer|failed|error)\s.+)$')


def rmqueuefiles(item, header, data):
    "remove the header and data files"
    try:
        if os.path.exists(header) and os.path.exists(data):
            os.remove(header)
            os.remove(data)
            return dict(msgid=item, done=True)
        else:
            return dict(msgid=item, done=False)
    except OSError:
        return dict(msgid=item, done=False)


def getsubject(lines):
    "Get the subject"
    subject = ''
    line = None
    for val in lines:
        match = SUBJECT_RE.match(val)
        if match:
            line = match.groups()[0].strip()
            if line.startswith('=?'):
                text, charset = decode_header(line)[0]
                line = unicode(text, charset or 'ascii', 'replace')
            break
    if line:
        subject = line
    return subject


def getrecipients(lines):
    "Get the recipients"
    lines.reverse()
    recipients = []
    for line in lines:
        if line.strip().isdigit():
            break
        recipients.append(line.strip())
    return recipients


def getqfs(matched, dirname, files):
    "utility to get queue header files"
    matched.extend([os.path.join(dirname, filename)
                    for filename in files
                    if filename.endswith('-H')])


class Mailq(list):
    "Mail queue parser"

    def __init__(self, queue):
        "init"
        list.__init__([])
        self.qdir = queue

    def process_delete(self, item):
        "Process items to delete"
        hdr = "%s-H" % item
        dat = "%s-D" % item
        data = os.path.join(self.qdir, dat)
        header = os.path.join(self.qdir, hdr)
        rmqueuefiles(item, header, data)

    def extractinfo(self, path):
        "extract attributes from queue file"
        try:
            with codecs.open(path, 'r', 'utf-8', 'replace') as headerfile:
                lines = headerfile.readlines()
            index = lines.index('\n')
            attribs = {}
            attribs['messageid'] = lines[0][:-3]
            attribs['timestamp'] = str(datetime\
                                    .utcfromtimestamp(float(lines[3]\
                                    .split()[0])))
            attribs['lastattempt'] = attribs['timestamp']
            attribs['from_address'] = lines[2].lstrip('<').rstrip('>\n')
            attribs['to_address'] = getrecipients(lines[:index])
            attribs['subject'] = getsubject(lines[index:])
            pipe1 = subprocess.Popen('hostname', shell=True,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            attribs['hostname'] = pipe1.stdout.read().strip()
            pipe1.wait(timeout=2)
            datafile = "%s-D" % os.path.basename(path)[:-2]
            dpath = os.path.join(os.path.dirname(path), datafile)
            replace = path.split(os.sep)[-2]
            mpath = os.path.join(
                    os.path.dirname(path.replace(replace, 'msglog')),
                    os.path.basename(path)[:-2])
            attribs['size'] = (os.path.getsize(path) +
                                os.path.getsize(dpath))
            attribs['attempts'] = 0
            reasons = []
            try:
                with codecs.open(mpath, 'r', 'utf-8', 'replace') as msglog:
                    for msg in msglog:
                        match = MSGLOG_RE.match(msg)
                        if match:
                            attribs['attempts'] += 1
                            attribs['lastattempt'] = match.groups()[0]
                            reasons.append(msg)
            except UnicodeEncodeError:
                pass
            if attribs['from_address'] == '':
                attribs['from_address'] = '<>'
            attribs['reason'] = '\n'.join(reasons)
            self.append(attribs)
        except (os.error, IOError, ValueError):
            pass

    def delete(self, items):
        "delete from queue"
        return [self.process_delete(item) for item in items]

    def __call__(self):
        "process"
        queuefiles = []
        os.path.walk(self.qdir, getqfs, queuefiles)
        [self.extractinfo(path) for path in queuefiles]
