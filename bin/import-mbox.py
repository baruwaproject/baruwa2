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
"""Import mbox mail as a test set"""
import os
import re
import sys
import time
import shutil
import mailbox
import binascii
import subprocess

import psutil
import MySQLdb

from email.utils import parseaddr
from optparse import OptionParser
from ConfigParser import SafeConfigParser

from dateutil.parser import parse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from sqlalchemy.engine.url import _parse_rfc1738_args

from baruwa.model.messages import Message, SARule, Archive
from baruwa.lib.spamd import SpamdConnection, SYMBOLS
from baruwa.lib.mail.parser import get_header
from baruwa.lib.misc import get_config_option

FROM_RE = re.compile(r'^From\s+.+$', re.IGNORECASE | re.MULTILINE)
FIND_IPS_RE = re.compile(
    r'\[?((?:[0-9]{1,3})\.(?:[0-9]{1,3})\.(?:[0-9]{1,3})\.(?:[0-9]{1,3}))\]?',
    re.MULTILINE
)


CACHE = {}


def hostname():
    "return the hostname"
    pipe = psutil.Popen(["hostname"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)
    name = pipe.communicate()[0]
    pipe.wait(timeout=120)
    return name.strip() or 'localhost'


def crc32(value):
    "get crc32"
    return binascii.crc32(value) & 0xffffffff


def print_(value):
    "print to same stream"
    spacer = ' ' * 80
    sys.stdout.write("%s%s\r" % (str(value), spacer))
    sys.stdout.flush()


def load_config(conffile):
    "load pylons configuration"
    config_parser = SafeConfigParser()
    config_parser.read(conffile)
    return config_parser


def get_hostname(headers):
    "Get sending host from received headers"
    for header in headers:
        if FROM_RE.match(header):
            match = FIND_IPS_RE.findall(header)
            if match:
                ipaddr = match[0]
                return ipaddr
    return None


def convert_headers(headers):
    "convert headers to string"
    def textize(header):
        "utility"
        return u"%s: %s" % header

    tmp = [textize(header) for header in headers]
    return u'\n'.join(tmp)


def update_index(surl, msgs):
    "update the RT index"
    url = _parse_rfc1738_args(surl)
    connparams = url.translate_connect_args(database='db',
                    username='user', password='passwd')
    MySQLdb.paramstyle = 'pyformat'
    dbconn = MySQLdb.connect(**connparams)
    cursor = dbconn.cursor()
    c = 0
    for mesg in msgs:
        if not mesg.id:
            print "Missing id, skipping"
            continue
        print_(" Indexing: %d" % mesg.id)
        params = {}
        for field in ['id', 'messageid', 'subject', 'headers',
                    'hostname', 'timestamp', 'isquarantined']:
            params[field] = getattr(mesg, field)
        params['from_addr'] = crc32(getattr(mesg, 'from_address'))
        params['to_addr'] = crc32(getattr(mesg, 'to_address'))
        params['from_dom'] = crc32(getattr(mesg, 'from_domain'))
        params['to_dom'] = crc32(getattr(mesg, 'to_domain'))
        params['isquarantined'] = int(params['isquarantined'])
        params['timestamp'] = int(time.mktime(params['timestamp']\
                                .timetuple()))
        sql = """INSERT INTO messages_rt (id, messageid,
                    subject, headers, hostname, from_addr,
                    to_addr, from_dom, to_dom, timestamp,
                    isquarantined) VALUES(
                    %(id)s, %(messageid)s, %(subject)s, %(headers)s,
                    %(hostname)s, %(from_addr)s, %(to_addr)s,
                    %(from_dom)s, %(to_dom)s, %(timestamp)s,
                    %(isquarantined)s)"""
        try:
            cursor.execute(sql, params)
            c += 1
            print_(" Indexed: %d" % c)
        except MySQLdb.MySQLError:
            #print err
            pass
    dbconn.close()
    msgs[:] = []


def save2db(sess, msgs, surl):
    "save messages to db"
    sess.add_all(msgs)
    sess.commit()
    if msgs and isinstance(msgs[0], Message):
        update_index(surl, msgs)


def generate_sareport(status, score, hits):
    "Generate sareport, similar to mailscanner"
    rules = []
    if status:
        begin = ('spam, SpamAssassin (not CACHEd, score=%#.3f,'
                ' required 5,') % score
    else:
        begin = ('not spam, SpamAssassin (not CACHEd,'
                ' score=%#.3f, required 5,') % score
    rules.append(begin)
    for ruleid in hits.split(','):
        try:
            if not ruleid in CACHE:
                sarule = session.query(SARule).get(ruleid)
                if sarule:
                    tmp = u"%s %#.3f," % (sarule.id, sarule.score)
                    rules.append(tmp)
                    CACHE[ruleid] = sarule.score
            else:
                tmp = u"%s %#.3f," % (ruleid, CACHE[ruleid])
                rules.append(tmp)
        except NoResultFound:
            pass
    report = u' '.join(rules)
    if report.endswith(','):
        report = report.rstrip(',')
    report = report + ')'
    return report


def flush2db(sess, msgs, archs, processed, sxurl):
    "save messages to DB"
    #print_ '*' * 100
    #print_ "Flushing to DB"
    try:
        save2db(sess, msgs, sxurl)
        save2db(sess, archs, sxurl)
        print_(" Processed: %(c)d" % dict(c=processed))
        #sys.stdout.write("\n\tProcessed: %d" % processed)
    except IntegrityError:
        print_("Integrity error proceeding")
    msgs[:] = []
    archs[:] = []


if __name__ == '__main__':
    # run the thing
    try:
        conn = SpamdConnection()
        usage = """
        usage: %prog [options]
        
            options:
            -c --config     "configuration file"
            -i --inputdir   "mbox input directory"
            -o --outputdir  "mbox output directory"
        """
        parser = OptionParser(usage)
        parser.add_option('-c', '--config', dest="settingsfile",
                        help="Baruwa configuration file",
                        default='/etc/baruwa/production.ini')
        parser.add_option('-i', '--inputdir', dest="mboxdir",
                        help="Mbox directory")
        parser.add_option('-o', '--outputdir', dest="outputdir",
                        help="Output directory")
        options, args = parser.parse_args()
        if not options.mboxdir:
            print usage
            print "Please specify the directory with the mbox files"
            sys.exit(2)
        if not options.outputdir:
            print usage
            print "Please specify the directory to store processed files"
            sys.exit(2)
        basepath = os.path.dirname(os.path.dirname(__file__))
        configfile = os.path.join(basepath, options.settingsfile)
        config = load_config(configfile)
        sqlalchemyurl = config.get('app:main', 'sqlalchemy.url',
                                    vars=dict(here=basepath))
        sphinxurl = config.get('app:main', 'sphinx.url',
                                vars=dict(here=basepath))
        engine = create_engine(sqlalchemyurl)
        # sphinxengine = create_engine(sphinxurl)
        Session = sessionmaker(bind=engine)
        # SphinxSession = sessionmaker(bind=sphinxengine)
        session = Session()
        # sphinxsession = SphinxSession()
        mboxdir = options.mboxdir
        #count = 0
        messages = []
        archived = []
        servername = hostname()
        msquarantine = get_config_option('QuarantineDir')
        cutoff = parse('01-01-05')
        qdirs = ["spam", "nonspam"]
        for (dirname, dirs, files) in os.walk(mboxdir):
            #print_ '*' * 100
            print 'Processing: %(d)s' % dict(d=dirname)
            for mail in files:
                if mail.startswith('.'):
                    continue
                count = 0
                filename = os.path.join(dirname, mail)
                print "Processing mailbox: %s" % mail
                for message in mailbox.mbox(filename):
                    try:
                        msgdatetime = parse(message['date'], ignoretz=True)
                        msgtimestamp = msgdatetime.strftime("%Y-%m-%d %H:%M:%S")
                        msgdate = msgdatetime.strftime("%Y-%m-%d")
                        msgtime = msgdatetime.strftime("%H:%M:%S")
                        dirdate = msgdate.replace('-', '')
                        # quarantinedir = os.path.join(basepath, 'data',
                        #                         'quarantine', dirdate)
                        quarantinedir = os.path.join(msquarantine, dirdate)
                        if not os.path.exists(quarantinedir):
                            os.mkdir(quarantinedir)
                            os.mkdir(os.path.join(quarantinedir, 'spam'))
                            os.mkdir(os.path.join(quarantinedir, 'nonspam'))
                        messageid = parseaddr(message['message-id'])[1]
                        messageid = messageid.replace('/', '.')
                        #messagepath = os.path.join(quarantinedir, messageid)
                        exists = False
                        for message_kind in qdirs:
                            messagepath = os.path.join(quarantinedir,
                                                        message_kind,
                                                        messageid)
                            if os.path.exists(messagepath):
                                exists = True
                                break
                        if exists:
                            #print_ "Skipping message with id: %s" % messageid
                            continue
                        count += 1
                        message_kind = 'nonspam'
                        received = message.get_all('Received') or []
                        fromip = get_hostname(received)
                        fromaddr = parseaddr(message['from'])[1]
                        toaddr = parseaddr(message['to'])[1]
                        fromdomain = fromaddr.split('@')[1]
                        todomain = toaddr.split('@')[1]
                        msgheaders = convert_headers(message.items())
                        if msgdatetime.date() < cutoff.date():
                            msg = Archive(messageid=messageid)
                        else:
                            msg = Message(messageid=messageid)
                        msg.actions         = "deliver"
                        msg.clientip        = fromip
                        msg.from_address    = fromaddr.lower()
                        msg.from_domain     = fromdomain.lower()
                        msg.to_address      = toaddr.lower()
                        msg.to_domain       = todomain.lower()
                        msg.hostname        = servername
                        msg.timestamp       = msgdatetime
                        msg.date            = msgdatetime.date()
                        msg.time            = msgdatetime.time()
                        msg.subject         = get_header(message['subject'])
                        msg.headers         = msgheaders
                        conn.addheader('User', 'andrew')
                        conn.check(SYMBOLS, message.as_string())
                        isspam, msg.sascore = conn.getspamstatus()
                        msg.spam            = int(isspam)
                        msg.spamreport      = generate_sareport(msg.spam,
                                                    msg.sascore,
                                                    conn.response_message)
                        msg.size            = len(message.as_string())
                        msg.isquarantined   = 1
                        if msg.spam:
                            msg.actions         = "store"
                            message_kind        = 'spam'
                        msg.scaned          = 1
                        if msg.sascore > 10:
                            msg.highspam    = 1
                        if msgdatetime.date() < cutoff.date():
                            messages.append(msg)
                        else:
                            archived.append(msg)
                        messagepath = os.path.join(quarantinedir,
                                                    message_kind,
                                                    messageid)
                        msghandle = open(messagepath, 'w')
                        msghandle.write(message.as_string())
                        msghandle.close()
                        #print_ "Processed: %s" % messageid
                        if (count % 100) == 0:
                        #if count == 100:
                            flush2db(session,
                                    messages,
                                    archived,
                                    count,
                                    sphinxurl)
                            #raise KeyboardInterrupt
                        else:
                            print_(" Processed: %(c)d" % dict(c=count))
                    except (IndexError, ValueError, AttributeError, IOError):
                        pass
                outfile = os.path.join(options.outputdir, mail)
                shutil.move(filename, outfile)
        flush2db(session, messages, archived, count, sphinxurl)
    except KeyboardInterrupt:
        if 'session' in locals() and (messages or archived):
            flush2db(session, messages, archived, count, sphinxurl)
        print "\nExiting..."
