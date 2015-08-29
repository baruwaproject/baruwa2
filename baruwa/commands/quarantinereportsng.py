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
"Send Quarantine reports"

import os
import sys
# import time
import base64
import datetime

import arrow

from babel.util import UTC
from sqlalchemy import desc
from routes.util import url_for
from marrow.mailer import Message as Msg, Mailer
from sqlalchemy.sql.expression import case, and_, or_, between, true
from marrow.mailer.exc import TransportFailedException, MessageFailedException

from baruwa.lib.dates import make_tz
from baruwa.model.meta import Session
from baruwa.lib.query import UserFilter
from baruwa.model.messages import Message, Release
from baruwa.model.accounts import User, domain_users
from baruwa.model.accounts import domain_owners as dom_owns
from baruwa.lib.cache import acquire_lock, release_lock_after
from baruwa.model.accounts import organizations_admins as oas
from baruwa.commands import BaseCommand, set_lang, get_conf_options, \
    gen_uuid, workout_path, get_theme_dirs, change_user, get_mako_lookup


class QuarantineReports(BaseCommand):
    "Send quarantine reports"
    BaseCommand.parser.add_option('-o', '--newer-than',
        help='Report on messages this number of days back',
        dest='num_days',
        type='int',
        default=1,)
    BaseCommand.parser.add_option('-m', '--max-records',
        help='Maximum number of messages to return',
        dest='max_msgs',
        type='int',
        default=25,)
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
    summary = """Send quarantine reports"""
    group_name = 'baruwa'

    def _send_msg(self, user, messages):
        "Send email report"
        lang = 'en'
        host_urls = dict([(domain.name, domain.site_url)
                    for domain in user.domains
                    if domain.status is True])
        langs = [domain.language for domain in user.domains
                if domain.language != 'en']
        if langs:
            lang = langs.pop(0)
        translator = set_lang(lang, 'baruwa', self.localedir)
        _ = translator.ugettext
        tmpldir, assetdir, cache_dir = get_theme_dirs(user.domains,
                                            self.themebase,
                                            self.conf['cache_dir'])

        def make_release_records(spam):
            "map function"
            uuid = gen_uuid(user)
            spam.uuid = uuid
            return Release(uuid=uuid, messageid=spam.id)
        if user.is_peleb:
            torelease = [make_release_records(spam)
                        for spam in messages]
        if tmpldir is None or assetdir is None:
            mako_lookup = self.mako_lookup
            logo = self.logo
        else:
            mako_lookup = get_mako_lookup(tmpldir, cache_dir)
            logo = os.path.join(assetdir, 'imgs', 'logo.png')
            if os.path.exists(logo):
                with open(logo) as handle:
                    logo = base64.b64encode(handle.read())
            else:
                logo = self.logo
        template = mako_lookup.get_template('/email/quarantine.html')
        html = template.render(messages=messages,
                        host_urls=host_urls,
                        url=url_for,
                        config=self.conf,
                        tzinfo=make_tz(user.timezone or UTC),
                        userid=user.id)
        template = mako_lookup.get_template('/email/quarantine.txt')
        text = template.render(messages=messages,
                            config=self.conf,
                            tzinfo=make_tz(user.timezone or UTC))
        displayname = "%s %s" % (user.firstname or '', user.lastname or '')
        pname = dict(name=self.conf.get('baruwa.custom.name', 'Baruwa'))
        productname = _('%(name)s Reports') % pname
        subject = _('%(name)s Quarantine Report') % pname
        email = Msg(author=[(productname,
                        self.conf['baruwa.reports.sender'])],
                        to=[(displayname, user.email)],
                        subject=subject)
        email.plain = text
        email.rich = html
        email.attach('logo.png',
                    data=logo,
                    maintype='image',
                    subtype='png',
                    inline=True)

        try:
            self.mailer.send(email)
            if 'torelease' in locals():
                Session.add_all(torelease)
                Session.commit()
        except (TransportFailedException, MessageFailedException), err:
            print >> sys.stderr, ("Error sending to: %s, Error: %s" %
                    (user.email, err))

    def _process_report(self, user):
        "Process users quarantine report"
        messages = Session.query(Message.id, Message.timestamp,
                        Message.from_address, Message.to_address,
                        Message.subject,
                        case([(and_(Message.spam > 0,
                            Message.virusinfected == 0,
                            Message.nameinfected == 0,
                            Message.otherinfected == 0,), True)],
                            else_=False).label('spam'),
                        Message.to_domain)\
                        .filter(Message.isquarantined > 0)\
                        .filter(or_(Message.spam > 0,
                                Message.nameinfected > 0,
                                Message.otherinfected > 0))\
                        .order_by(desc('timestamp'))
        query = UserFilter(Session, user, messages)
        messages = query.filter()
        if int(self.options.num_days) > 0:
            a_day = datetime.timedelta(days=self.options.num_days)
        else:
            a_day = datetime.timedelta(days=1)
        current_time = arrow.utcnow()
        startdate = current_time - a_day
        messages = messages.filter(between(Message.timestamp,
                                    startdate.datetime,
                                    current_time.datetime))
        messages = messages.filter(~Message.id.in_(self.previous_records))
        messages = messages[:self.options.max_msgs]
        if messages:
            self._send_msg(user, messages)

    def _get_exclude_users(self):
        """Get exclude org users"""
        query1 = Session.query(User)\
                .join(domain_users,
                    User.id == domain_users.c.user_id)\
                .join(dom_owns,
                    dom_owns.c.domain_id == domain_users.c.domain_id)\
                .filter(dom_owns.c.organization_id !=
                        self.options.exclude_org)\
                .filter(User.active == true())\
                .filter(User.send_report == true())
        query2 = Session.query(User)\
                .join(oas, User.id == oas.c.user_id)\
                .filter(User.active == true())\
                .filter(User.send_report == true())\
                .filter(User.account_type == 2)\
                .filter(oas.c.organization_id !=
                        self.options.exclude_org)
        users = query1.all()
        users.extend(query2.all())
        return users

    def _get_org_users(self):
        """Get org users"""
        query1 = Session.query(User)\
                .join(domain_users,
                    User.id == domain_users.c.user_id)\
                .join(dom_owns, dom_owns.c.domain_id ==
                    domain_users.c.domain_id)\
                .filter(dom_owns.c.organization_id ==
                    self.options.org_id)\
                .filter(User.active == true())\
                .filter(User.send_report == true())
        query2 = Session.query(User)\
                .join(oas, User.id == oas.c.user_id)\
                .filter(User.active == true())\
                .filter(User.send_report == true())\
                .filter(User.account_type == 2)\
                .filter(oas.c.organization_id ==
                        self.options.org_id)
        users = query1.all()
        users.extend(query2.all())
        return users

    def command(self):
        "run the command"
        self.init()
        change_user("baruwa", "baruwa")
        if self.options.org_id and self.options.exclude_org:
            print "\nThe -i and -e options are mutually exclusive\n"
            print self.parser.print_help()
            sys.exit(2)

        if acquire_lock('quarantinereportsng', self.conf):
            try:
                send_at = int(self.conf.get('baruwa.send.reports.at', 07))
                self.themebase = self.conf.get('baruwa.themes.base',
                                        '/usr/share/baruwa/themes')
                self.mailer = Mailer(get_conf_options(self.conf))
                self.mailer.start()
                base = workout_path()
                if os.path.exists(os.path.join(self.themebase, 'templates',
                        'default')):
                    path = os.path.join(self.themebase, 'templates',
                                        'default')
                    cache_dir = os.path.join(self.conf['cache_dir'],
                                            'templates', 'default')
                    logo = os.path.join(self.themebase, 'assets', 'default',
                                        'imgs', 'logo.png')
                else:
                    path = os.path.join(base, 'baruwa', 'templates')
                    cache_dir = os.path.join(self.conf['cache_dir'],
                                        'templates')
                    logo = os.path.join(base, 'baruwa', 'public',
                                        'imgs', 'logo.png')
                self.localedir = os.path.join(base, 'baruwa', 'i18n')
                self.mako_lookup = get_mako_lookup(path, cache_dir)
                if not os.path.exists(logo):
                    print >> sys.stderr, "The logo image: %s does not exist" \
                            % logo
                    sys.exit(2)
                with open(logo) as handle:
                    logo = base64.b64encode(handle.read())
                self.logo = logo

                if self.options.org_id:
                    users = self._get_org_users()
                elif self.options.exclude_org:
                    users = self._get_exclude_users()
                else:
                    users = Session.query(User)\
                            .filter(User.active == true())\
                            .filter(User.send_report == true())

                self.previous_records = Session\
                                        .query(Release.messageid)\
                                        .order_by(desc('timestamp'))
                for user in users:
                    # Timezone support
                    user_time = arrow.now(user.timezone)
                    if user_time.hour != send_at:
                        if self.options.force_send:
                            print "Force send used sending anyway to %s" % \
                                    user.username
                        else:
                            print "Skipped %s not scheduled for this time" % \
                                    user.username
                            continue
                    self._process_report(user)
                self.mailer.stop()
            finally:
                Session.close()
                # time.sleep(300)
                release_lock_after('quarantinereportsng', 300, self.conf)
