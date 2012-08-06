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

"Exim message management"

from eventlet.green import subprocess


def check_ids(msgids):
    "check ids"
    if not isinstance(msgids, list) and not isinstance(msgids, tuple):
        raise TypeError('msgids should be either a list or tuple')


class EximQueue(object):
    "Exim Queue management"
    def __init__(self, cmd):
        "init"
        self.cmd = cmd
        self.errors = []
        self.results = []

    def _run_cmd(self, options):
        "run command"
        cmd = self.cmd.split()
        cmd.extend(options)

        pipe = subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
        error, result = pipe.communicate()
        pipe.wait(timeout=120)
        if error:
            self.errors.append(error)
        if result:
            self.results.append(result)

    def deliver(self, msgids):
        "deliver messages"
        check_ids(msgids)

        self._run_cmd(['-M'] + msgids)

    def freeze(self, msgids):
        "freeze messages"
        check_ids(msgids)

        self._run_cmd(['-Mf'] + msgids)

    def delete(self, msgids):
        "delete messages"
        check_ids(msgids)

        self._run_cmd(['-Mrm'] + msgids)

    def bounce(self, msgids):
        "Bounce messages"
        check_ids(msgids)

        self._run_cmd(['-Mg'] + msgids)

    def add_recipient(self, msgids, addr):
        "Add recipient"
        check_ids(msgids)

        self._run_cmd(['-Mar'] + msgids + [addr])

    def flush_queue(self):
        "flush the queue"
        self._run_cmd(['-qff'])
        