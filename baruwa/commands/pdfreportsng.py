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
import datetime

from distutils.sysconfig import get_python_lib
from optparse import OptionValueError

from mako.lookup import TemplateLookup
from pylons.error import handle_mako_error
from sqlalchemy import desc, func
from sqlalchemy.sql.expression import case, and_, or_
from marrow.mailer import Message as Msg, Mailer
from marrow.mailer.exc import TransportFailedException, MessageFailedException

from baruwa.lib.dates import now
from baruwa.lib.misc import REPORTS
from baruwa.lib.query import UserFilter
from baruwa.model.meta import Session
from baruwa.model.domains import Domain
from baruwa.lib.graphs import PDFReport
from baruwa.lib.query import ReportQuery
from baruwa.model.messages import Message
from baruwa.model.accounts import User
from baruwa.commands import BaseCommand, set_lang, get_conf_options


PKGNAME = 'baruwa'
REPORTS_MAP = dict(monthly=3, weekly=2, daily=1)


def workout_path():
    "Workout the path to the baruwa installation"
    base = get_python_lib()
    if not os.path.exists(os.path.join(base, 'baruwa', 'templates')):
        import baruwa as bwp
        base = os.path.dirname(os.path.dirname(os.path.abspath(bwp.__file__)))
    return base


def check_report_type(option, opt_str, value, parser):
    "Check validity of report type option"
    if value is None:
        raise OptionValueError("Option: %s is required" % option)
    if value not in ['user', 'domain']:
        raise OptionValueError("%s is not a valid option for %s\n"
                                "\t\t\tSupported options are [user, domain]"
                                % (value, opt_str))
    setattr(parser.values, option.dest, value)


def check_period(option, opt_str, value, parser):
    "Check the validity of the period option"
    if value is None:
        raise OptionValueError("Option: %s is required" % option)
    if value not in ['daily', 'weekly', 'monthly']:
        raise OptionValueError("%s is not a valid option for %s\n"
                                "\t\t\tSupported options are "
                                "[daily, weekly, monthly]"
                                % (value, opt_str))
    setattr(parser.values, option.dest, value)


def get_users():
    "Get report users"
    users = Session.query(User).filter(User.active == True)\
            .filter(User.send_report == True).all()
    return users


def pie_report_query(user, reportid, num_of_days):
    "Run report query"
    query = ReportQuery(user, reportid)
    if int(num_of_days) > 0:
        numofdays = datetime.timedelta(days=num_of_days)
        startdate = now().date() - numofdays
        query = query.get().filter(Message.timestamp > str(startdate))
        data = query[:10]
    else:
        data = query.get()[:10]
    return data


def message_totals_report(model, num_of_days):
    "Message totals report"
    query = Session.query(Message.date,
                        func.count(Message.date).label('mail_total'),
                        func.sum(case([(Message.virusinfected > 0, 1)],
                        else_=0)).label('virus_total'),
                        func.sum(case([(and_(Message.virusinfected ==
                        0, Message.spam > 0), 1)], else_=0))\
                        .label('spam_total'), func.sum(Message.size)\
                        .label('total_size')).group_by(Message.date)\
                        .order_by(desc(Message.date))
    if isinstance(model, User):
        uquery = UserFilter(Session, model, query)
        query = uquery.filter()
    else:
        query = query.filter(Domain.name == model.name)
    if int(num_of_days) > 0:
        numofdays = datetime.timedelta(days=num_of_days)
        startdate = now().date() - numofdays
        query = query.filter(Message.timestamp > str(startdate))
    data = query.all()
    return data


def domain_pie_query(domain, reportid, num_of_days=0):
    "Run domain query"
    queryfield = getattr(Message, REPORTS[reportid]['address'])
    orderby = REPORTS[reportid]['sort']
    query = Session.query(queryfield.label('address'),
                        func.count(queryfield).label('count'),
                        func.sum(Message.size).label('size'))
    if reportid == '10':
        query = query.filter(queryfield != u'127.0.0.1')\
                        .group_by(queryfield)\
                        .order_by(desc(orderby))
    else:
        query = query.filter(queryfield != u'')\
                        .group_by(queryfield)\
                        .order_by(desc(orderby))
    if reportid in ['5', '6', '7', '8']:
        query = query.filter(Message.to_domain == domain)
    else:
        query = query.filter(func._(or_(Message.from_domain == domain,
                                        Message.to_domain == domain)))
    if int(num_of_days) > 0:
        numofdays = datetime.timedelta(days=num_of_days)
        startdate = now().date() - numofdays
        query = query.filter(Message.timestamp > str(startdate))
    data = query[:10]
    return data
    


class SendPdfReports(BaseCommand):
    "Create an admin user account"
    BaseCommand.parser.add_option('-t', '--report-type',
        help='Report type [user, domain]',
        dest='report_type',
        type='str',
        default='user',
        action='callback',
        callback=check_report_type,)
    BaseCommand.parser.add_option('-p', '--report-period',
        help='Report period [daily, weekly, monthly]',
        dest='report_period',
        type='str',
        default='daily',
        action='callback',
        callback=check_period,)
    BaseCommand.parser.add_option('-d', '--number-of-days',
        help='Restrict to number of days',
        dest='number_of_days',
        type='int',
        default=0,)
    summary = """Send summary PDF reports"""
    group_name = 'baruwa'

    def command(self):
        "run command"
        self.init()
        self.language = 'en'
        self.host_url = self.conf['baruwa.default.url']
        self.send_from = self.conf['baruwa.reports.sender']
        self.num_of_days = self.options.number_of_days
        base = workout_path()
        path = os.path.join(base, 'baruwa', 'templates')
        self.logo = os.path.join(base, 'baruwa', 'public', 'imgs', 'logo.png')
        self.localedir = os.path.join(base, 'baruwa', 'i18n')
        cache_dir = os.path.join(self.conf['cache_dir'], 'templates')

        self.mako_lookup = TemplateLookup(
                        directories=[path],
                        error_handler=handle_mako_error,
                        module_directory=cache_dir,
                        input_encoding='utf-8',
                        default_filters=['escape'],
                        output_encoding='utf-8',
                        encoding_errors='replace',
                        imports=['from webhelpers.html import escape']
                        )

        self.mailer = Mailer(get_conf_options(self.conf))
        self.mailer.start()
        if self.options.report_type == 'user':
            users = get_users()
            for user in users:
                self._process_user_report(user)
        else:
            period = REPORTS_MAP[self.options.report_period]
            domains = Session.query(Domain).filter(Domain.status == True)\
                            .filter(Domain.report_every == period).all()
            for domain in domains:
                admins = set()
                self.translator = set_lang(domain.language,
                                            PKGNAME,
                                            self.localedir)
                for org in domain.organizations:
                    for admin in org.admins:
                        admins.add(admin)
                pdf_file = self._process_domain_report(domain)
                for admin in admins:
                    self._send_domain_report(pdf_file, domain.site_url, admin)
        self.mailer.stop()

    def _send_domain_report(self, pdf_file, host_url, admin):
        "Send a domain report"
        _ = self.translator.ugettext
        template = self.mako_lookup.get_template('/email/pdfreports.txt')
        text = template.render(user=admin, url=host_url)
        displayname = '%s %s' % (admin.firstname or '', admin.lastname or '')
        email = Msg(author=[(_('Baruwa Reports'), self.send_from)],
                        to=[(displayname, admin.email)],
                        subject=_('Baruwa usage report'))
        email.plain = text
        email.attach('baruwa-reports.pdf',
                    data=pdf_file,
                    maintype='application',
                    subtype='pdf')
        try:
            self.mailer.send(email)
        except (TransportFailedException, MessageFailedException), err:
            print >> sys.stderr, ("Error sending to: %s, Error: %s" %
                    (admin.email, err))

    def _process_domain_report(self, domain):
        "Process domain report"
        sentry = 0
        _ = self.translator.ugettext
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
        pdfcreator = PDFReport(self.logo, _('Baruwa mail report'))
        for reportid in ['1', '2', '3', '4', '5', '6', '7', '8', '10']:
            sortby = reports[reportid]['sort']
            data = domain_pie_query(domain, reportid, self.num_of_days)
            if data:
                sentry += 1
                pdfcreator.add(data, reports[reportid]['title'],
                                pieheadings, sortby)
        data = message_totals_report(domain, self.num_of_days)
        if data:
            if not sentry:
                sentry += 1
            pdfcreator.add(data, _('Message Totals'), totalsheaders, chart='bar')
        if sentry:
            pdf_file = base64.b64encode(pdfcreator.build())
            return pdf_file
        return None

    def _process_user_report(self, user):
        "Process user report"
        sentry = 0
        language = self.language
        host_url = self.host_url

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
        translator = set_lang(language, PKGNAME, self.localedir)
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
        pdfcreator = PDFReport(self.logo, _('Baruwa mail report'))
        for reportid in ['1', '2', '3', '4', '5', '6', '7', '8', '10']:
            sortby = reports[reportid]['sort']
            if user.account_type == 3 and reportid in ['7', '8']:
                data = None
            else:
                data = pie_report_query(user, reportid, self.num_of_days)
            if data:
                sentry += 1
                pdfcreator.add(data, reports[reportid]['title'],
                            pieheadings, sortby)
        data = message_totals_report(user, self.num_of_days)
        if data:
            if not sentry:
                sentry += 1
            pdfcreator.add(data, _('Message Totals'), totalsheaders, chart='bar')
        if sentry:
            pdf_file = base64.b64encode(pdfcreator.build())
            template = self.mako_lookup.get_template('/email/pdfreports.txt')
            text = template.render(user=user, url=host_url)
            displayname = '%s %s' % (user.firstname or '', user.lastname or '')
            email = Msg(author=[(_('Baruwa Reports'), self.send_from)],
                            to=[(displayname, user.email)],
                            subject=_('Baruwa usage report'))
            email.plain = text
            email.attach('baruwa-reports.pdf',
                        data=pdf_file,
                        maintype='application',
                        subtype='pdf')
            try:
                self.mailer.send(email)
            except (TransportFailedException, MessageFailedException), err:
                print >> sys.stderr, ("Error sending to: %s, Error: %s" %
                        (user.email, err))