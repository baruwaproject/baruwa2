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

"Clean up the quarantine directories"

import os
import sys
import shutil
import datetime

from baruwa.commands import BaseCommand
from baruwa.model.meta import Session
from baruwa.lib.regex import QDIR
from baruwa.model.messages import Message
from baruwa.lib.misc import get_config_option


def should_be_pruned(direc, days_to_retain):
    """
    Returns true or false :
    if the directory is older than days_to_retain
        returns true
    else
        returns false
    """

    if (not days_to_retain) or (not QDIR.match(direc)):
        return False

    interval = datetime.timedelta(days=days_to_retain)
    last_date = datetime.date.today() - interval
    year = int(direc[0:4])
    mon = int(direc[4:-2])
    day = int(direc[6:])
    dir_date = datetime.date(year, mon, day)

    return dir_date < last_date


class CleanQuarantineCommand(BaseCommand):
    "DB clean command"
    summary = 'cleans the quarantine directory'
    # usage = 'NAME '
    group_name = 'baruwa'

    def command(self):
        "command"
        self.init()

        days_to_retain = int(self.conf.get('ms.quarantine.days_to_keep', 0))
        quarantine_dir = get_config_option('QuarantineDir')

        if (quarantine_dir.startswith('/etc') or
            quarantine_dir.startswith('/lib') or
            quarantine_dir.startswith('/home') or
            quarantine_dir.startswith('/bin') or
            quarantine_dir.startswith('..')):
            return False

        if (not os.path.exists(quarantine_dir)) or (days_to_retain == 0):
            return False

        ignore_dirs = ['spam', 'mcp', 'nonspam']

        def process_dir(dirs, process_path, direc):
            "process dirs"
            if os.path.exists(os.path.join(process_path, direc)):
                dirs.extend(
                [f for f in os.listdir(os.path.join(process_path, direc))])

        dirs = [f for f in os.listdir(quarantine_dir)
                if os.path.isdir(os.path.join(quarantine_dir, f)) and
                QDIR.match(f) and should_be_pruned(f, days_to_retain)]
        dirs.sort()
        for direc in dirs:
            process_path = os.path.join(quarantine_dir, direc)
            ids = [f for f in os.listdir(process_path)
                    if f not in ignore_dirs]
            for ignore_dir in ignore_dirs:
                process_dir(ids, process_path, ignore_dir)

            sql = Message.__table__.update()\
                .where(Message.messageid.in_(ids))\
                .values(isquarantined=0)
            Session.bind.execute(sql)
            if (os.path.isabs(process_path) and
                (not os.path.islink(process_path))):
                try:
                    shutil.rmtree(process_path)
                except shutil.Error:
                    print >> sys.stderr, ("Failed to remove %(path)s" %
                                dict(path=process_path))
            else:
                print >> sys.stderr, ("%(path)s is a symlink skipping" %
                                dict(path=process_path))