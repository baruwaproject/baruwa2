# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4
# Baruwa - Web 2.0 MailScanner front-end.
# Copyright (C) 2010-2015  Andrew Colin Kissa <andrew@topdog.za.net>
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
"Email a list of top spammers"

import sys
import datetime

import arrow

from sqlalchemy.sql import text
from marrow.mailer import Message as Msg, Mailer
from marrow.mailer.exc import TransportFailedException, MessageFailedException

from baruwa.model.meta import Session
from baruwa.commands import BaseCommand, check_email, \
    get_conf_options, check_period


class BuildWhiteList(BaseCommand):
    "Generate Approved senders lists command"
    BaseCommand.parser.add_option('-e', '--email',
        help='Account email address',
        dest='email',
        type='str',
        action='callback',
        callback=check_email,)
    BaseCommand.parser.add_option('-m', '--include-message-count',
        help='Include the number messages received',
        dest='include_count',
        action="store_true",
        default=False,)
    BaseCommand.parser.add_option('-d', '--dry-run',
        help='Print to stdout do not send email',
        dest='dry_run',
        action="store_true",
        default=False,)
    BaseCommand.parser.add_option('-n', '--messages-sent',
        help='Return senders with message counts equal to or greater than',
        dest='num',
        type='int',
        default=10,)
    BaseCommand.parser.add_option('-s', '--spam-score-threshold',
        help='Count messages with spam scores equal to or less than',
        dest='spamscore',
        type='float',
        default=-15,)
    BaseCommand.parser.add_option('-p', '--report-period',
        help='Report period [daily, weekly, monthly]',
        dest='report_period',
        type='str',
        default='daily',
        action='callback',
        callback=check_period,)
    summary = 'Generates a list of top ham senders for whitelisting'
    group_name = 'baruwa'

    def command(self):
        "command"
        self.init()
        if self.options.email is None:
            print "\nA valid email is required\n"
            print self.parser.print_help()
            sys.exit(2)

        starttime = arrow.utcnow()

        if self.options.report_period == 'daily':
            endtime = starttime - datetime.timedelta(days=1)
        elif self.options.report_period == 'weekly':
            endtime = starttime - datetime.timedelta(weeks=1)
        else:
            endtime = starttime - datetime.timedelta(weeks=4)

        params = dict(spamscore=self.options.spamscore, num=self.options.num,
                    starttime=starttime.datetime, endtime=endtime.datetime)

        sql = text("""SELECT clientip, COUNT(clientip) a
                    FROM messages WHERE sascore <= :spamscore
                    AND (timestamp BETWEEN :endtime AND :starttime)
                    GROUP BY clientip HAVING COUNT(clientip) >= :num
                    ORDER BY a DESC;""")
        results = Session.execute(sql, params=params)
        if results.rowcount:
            if self.options.include_count is False:
                records = [result.clientip for result in results]
            else:
                records = ["%s\t%d" % tuple(result) for result in results]
            content = "\n".join(records)
            if self.options.dry_run is True:
                print content
            else:
                mailer = Mailer(get_conf_options(self.conf))
                mailer.start()
                email = Msg(author=self.conf['baruwa.reports.sender'],
                            to=self.options.email, subject='TWL')
                email.plain = content
                try:
                    mailer.send(email)
                except (TransportFailedException, MessageFailedException), err:
                    print >> sys.stderr, err
                mailer.stop()
        else:
            print >> sys.stderr, "No records returned"
        Session.close()
