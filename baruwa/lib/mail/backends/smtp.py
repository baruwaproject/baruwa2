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

"""SMTP related classes"""

import re
import socket
import smtplib

ERRORSAN_RE = re.compile(r'\[Errno\s+\d+\]\s+')


class Sendmail(object):
    """Send mail via SMTP"""
    def __init__(self, server, debug):
        "Init server"
        self.server = server
        self.debug = debug
        self.errors = []
        self.conn = smtplib.SMTP(self.server)
        if self.debug:
            self.conn.set_debuglevel(5)

    def send(self, from_addr, to_addrs, message):
        "Send the mail"
        try:
            self.conn.sendmail(from_addr, to_addrs, message)
            return True
        except socket.gaierror:
            self.errors.append('Unable to resolve hostname: %(h)s' %
                                dict(h=self.server))
            return False
        except socket.timeout:
            self.errors.append('SMTP connection to: %(h)s timed out' %
                                dict(h=self.server))
            return False
        except socket.error, exception:
            self.errors.append(ERRORSAN_RE.sub('', str(exception)))
            return False
        except IOError:
            self.errors.append('The quarantined message not found')
            return False
        except smtplib.SMTPException, exception:
            self.errors.append(str(exception))
            return False

    def geterrors(self):
        "Return errors"
        return self.errors

    def close(self):
        "Close smtp connection"
        if self.conn:
            try:
                self.conn.quit()
            except smtplib.SMTPServerDisconnected:
                pass
