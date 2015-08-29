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
"Send PDF reports"

import os
import sys
# import time
import datetime

import pytz
import arrow

from base64 import b64encode
from optparse import OptionValueError

from sqlalchemy import desc, func
from marrow.mailer import Message as Msg, Mailer
from sqlalchemy.sql.expression import case, and_, or_, between, true
from marrow.mailer.exc import TransportFailedException, MessageFailedException

from baruwa.lib.misc import REPORTS
from baruwa.lib.query import UserFilter
from baruwa.model.meta import Session
from baruwa.model.domains import Domain
from baruwa.lib.graphs import PDFReport
from baruwa.lib.query import ReportQuery
from baruwa.lib.dates import make_tz
from baruwa.model.messages import Message
from baruwa.model.accounts import User, domain_users
from baruwa.model.accounts import domain_owners as dom_owns
from baruwa.lib.cache import acquire_lock, release_lock_after
from baruwa.commands import BaseCommand, set_lang, change_user, \
    get_conf_options, workout_path, get_theme_dirs, check_period, \
    get_mako_lookup


PKGNAME = 'baruwa'
REPORTS_MAP = dict(monthly=3, weekly=2, daily=1)


def check_report_type(option, opt_str, value, parser):
    "Check validity of report type option"
    if value is None:
        raise OptionValueError("Option: %s is required" % option)
    if value not in ['user', 'domain']:
        raise OptionValueError("%s is not a valid option for %s\n"
                                "\t\t\tSupported options are [user, domain]"
                                % (value, opt_str))
    setattr(parser.values, option.dest, value)


def get_users(only_org, exclude_org):
    "Get report users"
    if only_org:
        users = Session.query(User)\
            .join(domain_users, User.id == domain_users.c.user_id)\
            .join(dom_owns, dom_owns.c.domain_id == domain_users.c.domain_id)\
            .filter(dom_owns.c.organization_id == only_org)\
            .filter(User.active == true())\
            .filter(User.send_report == true()).all()
    elif exclude_org:
        users = Session.query(User)\
            .join(domain_users, User.id == domain_users.c.user_id)\
            .join(dom_owns, dom_owns.c.domain_id == domain_users.c.domain_id)\
            .filter(dom_owns.c.organization_id != exclude_org)\
            .filter(User.active == true())\
            .filter(User.send_report == true()).all()
    else:
        users = Session.query(User).filter(User.active == true())\
            .filter(User.send_report == true()).all()
    return users


def get_domains(only_org, exclude_org, reportperiod):
    "Get domains"
    if only_org:
        domains = Session.query(Domain)\
                    .join(dom_owns, Domain.id == dom_owns.c.domain_id)\
                    .filter(dom_owns.c.organization_id == only_org)\
                    .filter(Domain.status == true())\
                    .filter(Domain.report_every == reportperiod).all()
    elif exclude_org:
        domains = Session.query(Domain)\
                    .join(dom_owns, Domain.id == dom_owns.c.domain_id)\
                    .filter(dom_owns.c.organization_id != exclude_org)\
                    .filter(Domain.status == true())\
                    .filter(Domain.report_every == reportperiod).all()
    else:
        domains = Session.query(Domain)\
                    .filter(Domain.status == true())\
                    .filter(Domain.report_every == reportperiod).all()
    return domains


def pie_report_query(user, reportid, num_of_days):
    "Run report query"
    query = ReportQuery(user, reportid)
    if int(num_of_days) > 0:
        numofdays = datetime.timedelta(days=num_of_days)
        current_time = arrow.utcnow()
        startdate = current_time - numofdays
        query = query.get().filter(between(Message.timestamp,
                                    startdate.datetime,
                                    current_time.datetime))
        data = query[:10]
    else:
        data = query.get()[:10]
    return data


def message_totals_report(model, num_of_days, tmz):
    "Message totals report"
    query = Session.query(
            func.date(func.timezone(tmz, Message.timestamp))
                .label('ldate'),
            func.count('ldate').label('mail_total'),
            func.sum(case([(Message.virusinfected > 0, 1)], else_=0))
                .label('virus_total'),
            func.sum(case([(and_(Message.virusinfected == 0,
                    Message.spam > 0), 1)],
                    else_=0)).label('spam_total'),
            func.sum(Message.size).label('total_size'))\
            .group_by('ldate')\
            .order_by(desc('ldate'))
    if isinstance(model, User):
        uquery = UserFilter(Session, model, query)
        query = uquery.filter()
    else:
        query = query.filter(or_(Message.from_domain == model.name,
                                Message.to_domain == model.name))
    if int(num_of_days) > 0:
        numofdays = datetime.timedelta(days=num_of_days)
        current_time = arrow.utcnow()
        startdate = current_time - numofdays
        query = query.filter(between(Message.timestamp,
                                    startdate.datetime,
                                    current_time.datetime))
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
        current_time = arrow.utcnow()
        startdate = current_time - numofdays
        query = query.filter(between(Message.timestamp,
                                    startdate.datetime,
                                    current_time.datetime))
    data = query[:10]
    return data


class SendPdfReports(BaseCommand):
    "Sends PDF reports"
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
    BaseCommand.parser.add_option('-i', '--org-id',
        help="Process only this organization's accounts",
        dest='org_id',
        type='int',
        default=None,)
    BaseCommand.parser.add_option('-e', '--excluded-org',
        help="Exclude this organization's accounts",
        dest='exclude_org',
        type='int',
        default=None,)
    BaseCommand.parser.add_option('-f', '--force',
        help="Force sending of reports even if not in timezone",
        dest='force_send',
        action="store_true",
        default=False,)
    summary = """Send summary PDF reports"""
    group_name = 'baruwa'

    def _set_theme(self, domains):
        "Setup theme for user or for domain"
        # theme support
        tmpldir, assetdir, cache_dir = get_theme_dirs(domains,
                                            self.themebase,
                                            self.conf['cache_dir'])
        if tmpldir is None or assetdir is None:
            mako_lookup = self.mako_lookup
            logo = self.logo
        else:
            mako_lookup = get_mako_lookup(tmpldir, cache_dir)
            logo = os.path.join(assetdir, 'imgs', 'logo.png')
            if not os.path.exists(logo):
                logo = self.logo

        return mako_lookup, logo

    def _send_domain_report(self, pdf_file, host_url, admin, domain):
        "Send a domain report"
        if pdf_file:
            mako_lookup, _ = self._set_theme([domain])
            _ = self.translator.ugettext
            template = mako_lookup.get_template('/email/pdfreports.txt')
            text = template.render(user=admin, url=host_url, config=self.conf)
            displayname = '%s %s' % (admin.firstname or '',
                                    admin.lastname or '')
            pname = dict(name=self.conf.get('baruwa.custom.name', 'Baruwa'),
                        domain=domain.name)
            productname = _('%(name)s Reports') % pname
            subject = _('%(name)s: %(domain)s Usage Report') % pname
            email = Msg(author=[(productname, self.send_from)],
                            to=[(displayname, admin.email)],
                            subject=subject)
            email.plain = text
            reportname = self.conf.get('baruwa.custom.name', 'baruwa')\
                            .replace(' ', '-').lower()
            email.attach('%s-%s-reports.pdf' % (reportname, domain.name),
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
        # theme support
        _, logo = self._set_theme([domain])

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
                        'title': _('Total messages [ After SMTP ]')}}
        pieheadings = ('', _('Address'), _('Count'), _('Volume'), '')
        totalsheaders = dict(date=_('Date'), mail=_('Mail totals'),
                        spam=_('Spam totals'), virus=_('Virus totals'),
                        volume=_('Mail volume'), totals=_('Totals'))
        pname = _('%s Mail Report') % \
                self.conf.get('baruwa.custom.name', 'Baruwa')
        pdfcreator = PDFReport(logo, pname)
        for reportid in ['1', '2', '3', '4', '5', '6', '7', '8', '10']:
            sortby = reports[reportid]['sort']
            data = domain_pie_query(domain.name, reportid, self.num_of_days)
            if data:
                sentry += 1
                pdfcreator.add(data, reports[reportid]['title'],
                                pieheadings, sortby)
        data = message_totals_report(domain,
                                    self.num_of_days,
                                    domain.timezone)
        if data:
            if not sentry:
                sentry += 1
            pdfcreator.add(data,
                            _('Message Totals'),
                            totalsheaders,
                            chart='bar')
        if sentry:
            pdf_file = b64encode(pdfcreator.build())
            return pdf_file
        return None

    def _process_user_report(self, user):
        "Process user report"
        sentry = 0
        language = self.language
        host_url = self.host_url
        timezone = self.timezone

        if user.is_peleb:
            domains = [(domain.site_url,
                        domain.language,
                        domain.timezone)
                        for domain in user.domains
                        if domain.status is True]
            if domains:
                host_url, language, timezone = domains.pop(0)
        if language == 'en' and 'domains' in locals() and domains:
            while domains:
                _, language = domains.pop(0)
                if language != 'en':
                    break

        # theme support
        mako_lookup, logo = self._set_theme(user.domains)

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
                        'title': _('Total messages [ After SMTP ]')}}
        pieheadings = ('', _('Address'), _('Count'), _('Volume'), '')
        totalsheaders = dict(date=_('Date'), mail=_('Mail totals'),
                        spam=_('Spam totals'), virus=_('Virus totals'),
                        volume=_('Mail volume'), totals=_('Totals'))
        pname = _('%s Usage Report') % self.conf.get('baruwa.custom.name',
                                                    'Baruwa')
        pdfcreator = PDFReport(logo, pname)
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
        data = message_totals_report(user, self.num_of_days, timezone)
        if data:
            if not sentry:
                sentry += 1
            pdfcreator.add(data,
                            _('Message Totals'),
                            totalsheaders,
                            chart='bar')
        if sentry:
            pdf_file = b64encode(pdfcreator.build())
            template = mako_lookup.get_template('/email/pdfreports.txt')
            text = template.render(user=user, url=host_url, config=self.conf)
            displayname = '%s %s' % (user.firstname or '', user.lastname or '')
            pname = dict(name=self.conf.get('baruwa.custom.name', 'Baruwa'),
                        email=user.email)
            productname = _('%(name)s Reports') % pname
            subject = _('%(name)s: %(email)s Usage Report') % pname
            email = Msg(author=[(productname, self.send_from)],
                            to=[(displayname, user.email)],
                            subject=subject)
            email.plain = text
            reportname = self.conf.get('baruwa.custom.name', 'baruwa')\
                            .replace(' ', '-').lower()
            email.attach('%s-reports.pdf' % reportname,
                        data=pdf_file,
                        maintype='application',
                        subtype='pdf')
            try:
                self.mailer.send(email)
            except (TransportFailedException, MessageFailedException), err:
                print >> sys.stderr, ("Error sending to: %s, Error: %s" %
                        (user.email, err))

    def _process_domains(self):
        "process domains"
        period = REPORTS_MAP[self.options.report_period]
        domains = get_domains(self.options.org_id,
                            self.options.exclude_org,
                            period)

        for domain in domains:
            domain_time = arrow.now(domain.timezone)
            if domain_time.hour != self.send_at:
                if self.options.force_send:
                    print "Force send used sending anyway to %s" % \
                            domain.name
                else:
                    print "Skipped %s not scheduled for this time" \
                            % domain.name
                    continue
            admins = set()
            self.translator = set_lang(domain.language,
                                        PKGNAME,
                                        self.localedir)
            for org in domain.organizations:
                if (self.options.exclude_org and
                    self.options.exclude_org == org.id):
                    continue
                for admin in org.admins:
                    admins.add(admin)
            pdf_file = self._process_domain_report(domain)
            for admin in admins:
                self._send_domain_report(pdf_file,
                    domain.site_url, admin, domain)

    def _process_users(self):
        """Process users"""
        users = get_users(self.options.org_id,
                    self.options.exclude_org)
        for user in users:
            user_time = arrow.now(user.timezone)
            if user_time.hour != self.send_at:
                if self.options.force_send:
                    print "Force send used sending anyway to %s" % \
                            user.username
                else:
                    print "Skipped %s not scheduled for this time" \
                            % user.username
                    continue
            self._process_user_report(user)

    def command(self):
        "run command"
        self.init()
        change_user("baruwa", "baruwa")
        if self.options.org_id and self.options.exclude_org:
            print "\nThe -i and -e options are mutually exclusive\n"
            print self.parser.print_help()
            sys.exit(2)
        try:
            make_tz(self.conf['baruwa.timezone'])
        except pytz.exceptions.UnknownTimeZoneError:
            print "\n Timezone: %s is unknown\n" % self.conf['baruwa.timezone']
            sys.exit(2)

        if acquire_lock('pdfreportsng', self.conf):
            try:
                self.send_at = int(self.conf.get('baruwa.send.reports.at', 07))
                self.language = 'en'
                self.host_url = self.conf['baruwa.default.url']
                self.send_from = self.conf['baruwa.reports.sender']
                self.timezone = self.conf['baruwa.timezone']
                self.num_of_days = self.options.number_of_days
                base = workout_path()
                self.themebase = self.conf.get('baruwa.themes.base',
                                        '/usr/share/baruwa/themes')
                if os.path.exists(os.path.join(self.themebase, 'templates',
                        'default')):
                    path = os.path.join(self.themebase, 'templates',
                                'default')
                    self.logo = os.path.join(self.themebase, 'assets',
                                'default', 'imgs', 'logo.png')
                    cache_dir = os.path.join(self.conf['cache_dir'],
                                'templates', 'default')
                else:
                    path = os.path.join(base, 'baruwa', 'templates')
                    self.logo = os.path.join(base, 'baruwa', 'public',
                                'imgs', 'logo.png')
                    cache_dir = os.path.join(self.conf['cache_dir'],
                                'templates')

                self.localedir = os.path.join(base, 'baruwa', 'i18n')
                self.mako_lookup = get_mako_lookup(path, cache_dir)
                self.mailer = Mailer(get_conf_options(self.conf))
                self.mailer.start()
                if self.options.report_type == 'user':
                    self._process_users()
                else:
                    self._process_domains()
                self.mailer.stop()
            finally:
                Session.close()
                # time.sleep(300)
                release_lock_after('pdfreportsng', 300, self.conf)
