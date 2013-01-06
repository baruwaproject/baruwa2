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
"Archives, then deletes old records"

import sys
import datetime

from sqlalchemy.sql import text
from eventlet.green import subprocess
from sqlalchemy.exc import IntegrityError

from baruwa.lib.dates import now
from baruwa.commands import BaseCommand
from baruwa.model.meta import Session


def process_messages(last_date):
    "process messages table"
    params = dict(date=last_date)
    sql1 = text("""INSERT INTO archive
                SELECT * FROM messages WHERE timestamp <
                :date;""")
    try:
        Session.execute(sql1, params=params)
    except IntegrityError, error:
        Session.rollback()
        sql = text("""DELETE FROM archive WHERE id in
                    (SELECT id FROM messages WHERE timestamp < :date);"""
                    )
        Session.execute(sql, params=params)
        Session.execute(sql1, params=params)
        print >> sys.stderr, "Integrety error occured: %s" % str(error)
        sys.exit(2)
    sql = text("""DELETE FROM messages WHERE timestamp < :date;""")
    result = Session.execute(sql, params=params)
    sql = text("""DELETE FROM releases WHERE timestamp < :date;""")
    Session.execute(sql, params=params)
    Session.commit()
    if result.rowcount > 0:
        index_cmd = ['/usr/bin/indexer', '--rotate', 'messages']
        pipe = subprocess.Popen(index_cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        _, stderr = pipe.communicate()
        pipe.wait()
        if stderr:
            print >> sys.stderr, stderr


def prune_archive(last_date):
    "prune the messages archive"
    params = dict(date=last_date)
    sql = text("""DELETE FROM archive WHERE timestamp < :date;""")
    result = Session.execute(sql, params=params)
    Session.commit()
    if result.rowcount > 0:
        index_cmd = ['/usr/bin/indexer', '--rotate', 'archive']
        pipe = subprocess.Popen(index_cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        _, stderr = pipe.communicate()
        pipe.wait()
        if stderr:
            print >> sys.stderr, stderr


class DBCleanCommand(BaseCommand):
    "DB clean command"
    BaseCommand.parser.add_option('-d', '--days',
        help='Archive, then delete records older than days',
        type='int', default=30)
    BaseCommand.parser.add_option('-a', '--adays',
        help='Delete achived records older than archive',
        type='int', default=90)
    summary = 'archives, then deletes old records, and trims archive'
    group_name = 'baruwa'

    def command(self):
        "command"
        self.init()
        
        if (self.conf.get('baruwa.messages.keep.days', 30) !=
            self.options.days):
            days = self.options.days
        else:
            days = self.conf.get('baruwa.messages.keep.days', 30)
        if (self.conf.get('baruwa.archive.keep.days', 90) !=
            self.options.adays):
            adays = self.options.adays
        else:
            adays = self.conf.get('baruwa.archive.keep.days', 90)

        interval = datetime.timedelta(days=days)
        archive_interval = datetime.timedelta(days=adays)
        msgs_date = now() - interval
        last_achive_date = now() - archive_interval
        # process messages table
        process_messages(msgs_date)
        # process archive table
        prune_archive(last_achive_date)
        
        
