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

"Baruwa email message related modules"
import os
import shutil
import socket
import smtplib

from eventlet.green import subprocess

from baruwa.lib.misc import get_config_option, get_ipaddr
from baruwa.lib.regex import MSGID_RE, IPV4_RE, DOM_RE
from baruwa.lib.mail.parser import EmailParser
from baruwa.lib.mail.backends.smtp import Sendmail


def get_message_path(qdir, date, message_id):
    """
    Returns the on disk path of a message
    or None if path does not exist
    """
    file_path = os.path.join(qdir, date, message_id, 'message')
    if os.path.exists(file_path):
        return file_path, True

    qdirs = ["spam", "nonspam", "mcp"]
    for message_kind in qdirs:
        file_path = os.path.join(qdir, date, message_kind, message_id)
        if os.path.exists(file_path):
            return file_path, False
    return None, None


def search_quarantine(date, message_id):
    """search_quarantine"""
    qdir = get_config_option('Quarantine Dir')
    date = "%s" % date
    date = date.replace('-', '')
    return get_message_path(qdir, date, message_id)


class ProcessQuarantinedMessage(object):
    """Process a quarantined message"""
    def __init__(self, msgfile, isdir, host='127.0.0.1', debug=None):
        "init"
        self.msgfile = msgfile
        self.isdir = isdir
        self.host = host
        self.errors = []
        self.output = ''
        self.debug = debug
        self.salearn = 'sa-learn'

    def release(self, from_addr, to_addrs):
        "Release message from quarantine"
        try:
            messagefile = open(self.msgfile, 'r')
            message = messagefile.readlines()
            messagefile.close()
            for index, line in enumerate(message):
                if line.endswith(' ret-id none;\n'):
                    message[index] = line.replace(' ret-id none;', '')
                if MSGID_RE.match(line):
                    message.pop(index)
                    break
            message = ''.join(message)

            smtp = Sendmail(self.host, self.debug)
            if not smtp.send(from_addr, to_addrs, message):
                self.errors.extend(smtp.geterrors())
                smtp.close()
                return False
            smtp.close()
            return True
        except IOError, exception:
            self.errors.append(str(exception))
            return False

    def setlearncmd(self, learncmd):
        "Set the salearn command"
        self.salearn = learncmd

    def learn(self, learnas):
        "Bayesian learn the message"
        learnopts = ('spam', 'ham', 'forget')
        if not learnas in learnopts:
            self.errors.append('Unsupported learn option supplied')
            return False

        learn = "--%s" % learnas
        sa_learn_cmd = [self.salearn, learn, self.msgfile]
        try:
            pipe = subprocess.Popen(sa_learn_cmd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            stdout, stderr = pipe.communicate()
            pipe.wait(timeout=30)
            if pipe.returncode == 0:
                self.output = stdout
                return True
            else:
                self.errors.append(stderr)
                self.output = stderr
                return False
        except IOError, exception:
            self.errors.append(str(exception))
            return False
        except OSError, exception:
            self.errors.append(str(exception))
            return False

    def delete(self):
        "Delete quarantined file"
        try:
            if '..' in self.msgfile:
                raise OSError('Attempted directory traversal')
            if self.isdir:
                path = os.path.dirname(self.msgfile)
                shutil.rmtree(path)
            else:
                os.remove(self.msgfile)
        except OSError, exception:
            self.errors.append(str(exception))
            return False
        return True

    def reset_errors(self):
        "Resets errors"
        self.errors[:] = []


class PreviewMessage(object):
    """Preview message"""
    def __init__(self, msgfile):
        "init"
        self.parser = EmailParser(msgfile)

    def preview(self):
        "Return message"
        return self.parser.parse()

    def attachment(self, attachmentid):
        "Return attachment"
        return self.parser.get_attachment(attachmentid)

    def img(self, imageid):
        "Return inline image"
        return self.parser.get_img(imageid)


class TestDeliveryServers(object):
    """Test deliverying mail to a server"""
    def __init__(self, host, port, test_addr, from_addr):
        "init"
        self.host = host
        self.port = int(port)
        self.has_ssl = False
        self.has_starttls = False
        self.debug = False
        self.errors = []
        self.test_addr = test_addr
        self.from_addr = from_addr

    def smtp_test(self):
        "run smtp test"
        try:
            if self.port == 465:
                conn = smtplib.SMTP_SSL(self.host)
                self.has_ssl = True
            elif self.port == 25:
                conn = smtplib.SMTP(self.host)
            else:
                conn = smtplib.SMTP(self.host, self.port)
            if self.debug:
                conn.set_debuglevel(5)
            conn.ehlo()
            if conn.has_extn('STARTTLS') and self.port != 465:
                conn.starttls()
                conn.ehlo()
                self.has_starttls = True
            conn.docmd('MAIL FROM:', self.from_addr)
            result = conn.docmd('RCPT TO:', self.test_addr)
            if result[0] in range(200, 299):
                return True
            else:
                self.errors.append('Expected response code 2xx got %(code)s'
                                    % dict(code=str(result[0])))
                conn.quit()
                return False
        except socket.error:
            self.errors.append('Connection timed out')
        except smtplib.SMTPServerDisconnected, exception:
            self.errors.append('The server disconnected abruptly')
        except smtplib.SMTPSenderRefused, exception:
            self.errors.append('The sender %(sender)s was rejected' %
            dict(sender=exception.sender))
        except smtplib.SMTPRecipientsRefused, exception:
            self.errors.append('Some recipients: %(recpts)s were'
            ' rejected with errors: %(errors)s' % 
            dict(recpts=str(exception.recipients), errors=str(exception)))
        except smtplib.SMTPConnectError:
            self.errors.append('Error occured while establishing'
            ' connection to the server')
        except smtplib.SMTPHeloError:
            self.errors.append('Server rejected our HELO message')
        except smtplib.SMTPResponseException, exception:
            self.errors.append('Error occured, CODE:'
            ' %(code)s MESSAGE: %(msg)s' % dict(code=exception.smtp_code,
            msg=str(exception)))
        finally:
            if 'conn' in locals():
                try:
                    conn.quit()
                except smtplib.SMTPServerDisconnected:
                    pass
        return False

    def ping(self, count=None):
        "ping host"
        if count is None:
            count = 5
        if DOM_RE.match(self.host):
            ipaddr = get_ipaddr(self.host)
        if (IPV4_RE.match(self.host) or 'ipaddr' in locals()
            and IPV4_RE.match(ipaddr)):
            if not 'ipaddr' in locals():
                ipaddr = self.host
            ping_bin = 'ping'
        else:
            ipaddr = self.host
            ping_bin = 'ping6'
        if ipaddr:
            ping_cmd = [ping_bin, '-c', str(count), ipaddr]
            pipe = subprocess.Popen(ping_cmd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            stdout, stderr = pipe.communicate()
            pipe.wait(timeout=10)
            if pipe.returncode == 0:
                return True
            else:
                self.errors.append(stderr)
                return False
        self.errors.append('Unable to resolve hostname')
        return False

    def setdebug(self):
        "enable debug info"
        self.debug = True

    def tests(self, pingcount=None):
        "Run all tests"
        if self.ping(pingcount) and self.smtp_test():
            return True
        return False

    def reset_errors(self):
        "reset errors"
        self.errors[:] = []

    def properties(self):
        "return supported properties"
        self.smtp_test()
        return dict(ssl=self.has_ssl, starttls=self.has_starttls,
                    hostname=self.host, port=self.port)
