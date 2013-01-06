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
"Send PDF reports"

import os
import sys
import base64
import logging
import datetime

from mako.lookup import TemplateLookup
from pylons.error import handle_mako_error
from sqlalchemy import desc, func
from sqlalchemy.sql.expression import case, and_
from marrow.mailer import Message as Msg, Mailer
from marrow.mailer.exc import TransportFailedException, MessageFailedException

from baruwa.lib.query import UserFilter
from baruwa.model.meta import Session
from baruwa.model.domains import Domain
from baruwa.lib.graphs import PDFReport
from baruwa.lib.query import ReportQuery
from baruwa.model.messages import Message
from baruwa.model.accounts import User, domain_owners
from baruwa.commands import BaseCommand, set_lang, get_conf_options


logging.basicConfig(level=logging.INFO)


class SendPdfReports(BaseCommand):
    "Sends PDF reports"
    BaseCommand.parser.add_option('-n', '--from-days', dest='days',
        help='only messages newer than days ago',
        type='int', default=0)
    summary = 'Send summary PDF reports'
    group_name = 'baruwa'

    def command(self):
        "send"
        self.init()

        import baruwa
        pkgname = 'baruwa'
        here = os.path.dirname(
                    os.path.dirname(os.path.abspath(baruwa.__file__))
                )
        path = os.path.join(here, 'baruwa', 'templates')
        logo = os.path.join(here, 'baruwa', 'public', 'imgs', 'logo.png')
        localedir = os.path.join(here, 'baruwa', 'i18n')
        cache_dir = os.path.join(self.conf['cache_dir'], 'templates')
        mako_lookup = TemplateLookup(
                        directories=[path],
                        error_handler=handle_mako_error,
                        module_directory=cache_dir,
                        input_encoding='utf-8',
                        default_filters=['escape'],
                        output_encoding='utf-8',
                        encoding_errors='replace',
                        imports=['from webhelpers.html import escape']
                        )

        mailer = Mailer(get_conf_options(self.conf))
        mailer.start()
        users = Session\
                .query(User)\
                .filter(User.active == True)\
                .filter(User.send_report == True).all()
        #localedir = os.path.join(self.conf['here'], 'baruwa', 'i18n')
        for user in users:
            host_url = self.conf['baruwa.default.url']
            sentry = 0
            language = 'en'
            if user.is_domain_admin:
                orgs = [group.id for group in user.organizations]
                domains = Session\
                        .query(Domain.site_url, Domain.language)\
                        .join(domain_owners)\
                        .filter(Domain.status == True)\
                        .filter(domain_owners.c.organization_id.in_(orgs))\
                        .all()
                if domains:
                    host_url, language = domains.pop(0)
            if user.is_peleb:
                domains = [(domain.site_url, domain.language)
                            for domain in user.domains
                            if domain.status == True]
                if domains:
                    host_url, language = domains.pop(0)
            if language == 'en' and 'domains' in locals() and domains:
                while domains:
                    _, language = domains.pop(0)
                    if language != 'en':
                        break
            translator = set_lang(language, pkgname, localedir)
            _ = translator.ugettext
            reports = {
                        '1': {'address': 'from_address', 'sort': 'count',
                            'title': _('Top Senders by Quantity')},
                        '2': {'address': 'from_address', 'sort': 'size',
                            'title': _('Top Senders by Volume')},
                        '3': {'address': 'from_domain', 'sort': 'count',
                            'title': _('Top Sender Domains by Quantity')},
                        '4': {'address': 'from_domain', 'sort': 'size',
                            'title': _('Top Sender Domains by Volume')},
                        '5': {'address': 'to_address', 'sort': 'count',
                            'title': _('Top Recipients by Quantity')},
                        '6': {'address': 'to_address', 'sort': 'size',
                            'title': _('Top Recipients by Volume')},
                        '7': {'address': 'to_domain', 'sort': 'count',
                            'title': _('Top Recipient Domains By Quantity')},
                        '8': {'address': 'to_domain', 'sort': 'size',
                            'title': _('Top Recipient Domains By Volume')},
                        '9': {'address': '', 'sort': '',
                            'title': _('Spam Score distribution')},
                        '10': {'address': 'clientip', 'sort': 'count',
                            'title': _('Top mail hosts by quantity')},
                        '11': {'address': '', 'sort': '',
                            'title': _('Total messages [ After SMTP ]')}
                        }
            pieheadings = ('', _('Address'), _('Count'), _('Volume'), '')
            totalsheaders = dict(date=_('Date'), mail=_('Mail totals'),
                            spam=_('Spam totals'), virus=_('Virus totals'),
                            volume=_('Mail volume'), totals=_('Totals'))
            pdfcreator = PDFReport(logo, _('Baruwa mail report'))
            for reportid in ['1', '2', '3', '4', '5', '6', '7', '8', '10']:
                sortby = reports[reportid]['sort']
                if user.account_type == 3 and reportid in ['7', '8']:
                    data = None
                else:
                    query = ReportQuery(user, reportid)
                    if int(self.options.days) > 0:
                        a_day = datetime.timedelta(days=self.options.days)
                        startdate = datetime.date.today() - a_day
                        query = query.get().filter(Message.timestamp >
                                str(startdate))
                        data = query[:10]
                    else:
                        data = query.get()[:10]
                if data:
                    sentry += 1
                    pdfcreator.add(data, reports[reportid]['title'],
                                pieheadings, sortby)
            query = Session.query(Message.date,
                                func.count(Message.date).label('mail_total'),
                                func.sum(case([(Message.virusinfected > 0, 1)],
                                else_=0)).label('virus_total'),
                                func.sum(case([(and_(Message.virusinfected ==
                                0, Message.spam > 0), 1)], else_=0))\
                                .label('spam_total'), func.sum(Message.size)\
                                .label('total_size')).group_by(Message.date)\
                                .order_by(desc(Message.date))
            uquery = UserFilter(Session, user, query)
            query = uquery.filter()
            data = query.all()
            if data:
                if not sentry:
                    sentry += 1
                pdfcreator.add(data, _('Message Totals'), totalsheaders,
                                chart='bar')
            if sentry:
                template = mako_lookup.get_template('/email/pdfreports.txt')
                text = template.render(user=user, url=host_url)
                displayname = '%s %s' % (user.firstname or '',
                                        user.lastname or '')
                email = Msg(author=[(_('Baruwa Reports'),
                                self.conf['baruwa.reports.sender'])],
                                to=[(displayname, user.email)],
                                subject=_('Baruwa usage report'))
                email.plain = text
                pdf_file = base64.b64encode(pdfcreator.build())
                email.attach('baruwa-reports.pdf',
                            data=pdf_file,
                            maintype='application',
                            subtype='pdf')
                try:
                    mailer.send(email)
                except (TransportFailedException, MessageFailedException), err:
                    print >> sys.stderr, ("Error sending to: %s, Error: %s" %
                            (user.email, err))
        mailer.stop()
