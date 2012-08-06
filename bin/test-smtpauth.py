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

import sys
import base64
import socket
import getpass
import smtplib


def get_value(field, required):
    "get user input"
    prompt = "Please enter the %s:" % field
    while 1:
        if field in ['password']:
            value = getpass.getpass(prompt=prompt)
        else:
            value = raw_input(prompt)
        if value or not required:
            break
    return value

def startconn(vals):
    "start an smtp connection"
    con = smtplib.SMTP(vals['hostname'])
    if vals['port'] == 465:
        con = smtplib.SMTP_SSL(vals['hostname'], vals['port'])
    elif vals['port'] == 25:
        con = smtplib.SMTP(vals['hostname'])
    else:
        con = smtplib.SMTP(vals['hostname'], vals['port'])
    con.ehlo()
    if con.has_extn('STARTTLS') and vals['port'] != 465:
        con.starttls()
        con.ehlo()
    return con


if __name__ == '__main__':
    "ran da thing"
    params = dict(hostname=True,
                port=False,
                usetls=False,
                username=True,
                password=True)

    values = dict([(param, get_value(param, params[param]))
                for param in params])

    try:
        values['port'] = int(values['port']) if values['port'] else 25
        conn = startconn(values)
        username = values['username'].replace('@', '\@')
        password = values['password']
        sys.stdout.write("Trying LOGIN AUTH: ")
        conn.docmd("AUTH LOGIN", base64.b64encode(username))
        code, response = conn.docmd(base64.b64encode(password), "")
        print code, response
        conn.close()
        conn = startconn(values)
        sys.stdout.write("Trying PLAIN AUTH: ")
        auth = "AUTH PLAIN %s" % base64.b64encode('\000%s\000%s' %
                                                (username, password))
        code, response = conn.docmd(auth)
        print code, response
        conn.close()
    except (socket.error, socket.gaierror) as err:
        print 'ERROR: %s' % str(err)
