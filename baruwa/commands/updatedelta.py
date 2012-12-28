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
"Update sphinx index"

import sys

from MySQLdb import Error
from sqlalchemy.sql import text
from eventlet.green import subprocess

from baruwa.model.meta import Session
from baruwa.commands import BaseCommand
from baruwa.lib.query import sphinx_connection, format_sphinx_ids


def update_rt_index(index_name, sphinxurl):
    "Update the realtime index"
    ts_sql_temp = """SELECT UNIX_TIMESTAMP(maxts) FROM indexer_counters WHERE
                    tablename='%s_delta'"""
    ids_sql_temp = """SELECT id FROM %s_rt WHERE timestamp <= %%s
                    option max_matches=500"""

    timestamp = Session.execute(ts_sql_temp % index_name).scalar()
    conn = sphinx_connection(sphinxurl)
    try:
        cursor = conn.cursor()
        cursor.execute(ids_sql_temp % index_name, [timestamp])
        ids = [int(msgid[0]) for msgid in cursor.fetchall()]
        if ids:
            idstr = format_sphinx_ids(len(ids))
            delsql = "DELETE FROM %s_rt WHERE id in (%s)" % (index_name, idstr)
            cursor.execute(delsql, ids)
    except Error, exp:
        print >> sys.stderr, str(exp)
    finally:
        conn.close()


def update_index(sphinx_url, index, has_rt):
    "Update Sphinx index"
    sql_temp = """SELECT set_var('maxts', 
                (SELECT maxts FROM indexer_counters
                WHERE tablename='messages_delta'));
                UPDATE indexer_counters
                SET maxts=get_var('maxts')
                WHERE tablename='%s';"""

    main_index = index
    delta_index = '%sdelta' % index
    indexer_cmd = ['/usr/bin/indexer', '--rotate', '--merge',
                    main_index, delta_index]
    pipe = subprocess.Popen(indexer_cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    _, stderr = pipe.communicate()
    pipe.wait()
    if pipe.returncode == 0:
        sql = text(sql_temp % main_index)
        Session.execute(sql, params={})
        Session.commit()
        delta_index_cmd = ['/usr/bin/indexer', '--rotate', delta_index]
        pipe = subprocess.Popen(delta_index_cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        _, stderr = pipe.communicate()
        pipe.wait()
        if has_rt:
            update_rt_index(index, sphinx_url)
    else:
        print >> sys.stderr, stderr

class UpdateDeltaIndex(BaseCommand):
    "Update sphinx delta indexes"
    BaseCommand.parser.add_option('-i', '--index',
        help='Name of the index to update',
        dest='index_name',
        type='str',)
    BaseCommand.parser.add_option('-r', '--realtime',
        help='Index has realtime component',
        dest='index_has_rt',
        action="store_true",
        default=False,)
    summary = """Update the Delta and RT indexes[messages, archive]"""
    group_name = 'baruwa'

    def command(self):
        "run command"
        self.init()
        if self.options.index_name is None:
            print "\nProvide an index to update\n"
            print self.parser.print_help()
            sys.exit(2)

        if self.options.index_name not in ['messages', 'archive']:
            print "\nProvide a valid index to update\n"
            print self.parser.print_help()
            sys.exit(2)

        update_index(self.conf['sphinx.url'],
                    self.options.index_name,
                    self.options.index_has_rt)

        
