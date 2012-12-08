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
"Send Quarantine reports"

import os
import sys
import base64
import hashlib
import datetime

from sqlalchemy import desc
from routes.util import url_for
from mako.lookup import TemplateLookup
from pylons.error import handle_mako_error
from sqlalchemy.sql.expression import case, and_, or_
from marrow.mailer import Message as Msg, Mailer

from baruwa.model.meta import Session
from baruwa.model.accounts import User
from baruwa.lib.dates import now
from baruwa.lib.query import UserFilter
from baruwa.model.messages import Message, Release
from baruwa.commands import BaseCommand, set_lang, get_conf_options


def gen_uuid(account):
    "Generates a uuid"
    seed = "%s%s%s" % (account.username, account.email, now())
    messageuuid = hashlib.sha1(seed).hexdigest()
    return messageuuid


class QuarantineReports(BaseCommand):
    "Send quarantine reports"
    BaseCommand.parser.add_option('-o', '--newer-than', dest='days',
        help='only messages newer than days ago',
        type='int', default=0)
    summary = 'Send quarantine reports'
    # usage = 'NAME '
    group_name = 'baruwa'

    def command(self):
        "run command"
        self.init()
        import baruwa
        here = os.path.dirname(
                    os.path.dirname(os.path.abspath(baruwa.__file__))
                )
        path = os.path.join(here, 'baruwa', 'templates')
        logo = os.path.join(here, 'baruwa', 'public', 'imgs', 'logo.png')
        localedir = os.path.join(here, 'baruwa', 'i18n')
        cache_dir = os.path.join(self.conf['cache_dir'], 'templates')
        pkgname = 'baruwa'

        if not os.path.exists(logo):
            print sys.STDERR ("The logo image: %s does not exist" % logo)
            sys.exit(2)

        with open(logo) as handle:
            logo = base64.b64encode(handle.read())

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

        users = Session.query(User)\
                .filter(User.active == True)\
                .filter(User.send_report == True)

        previous_records = Session\
                        .query(Release.messageid)\
                        .order_by(desc('timestamp'))

        for user in users:
            messages = Session.query(Message.id, Message.timestamp,
                            Message.from_address, Message.to_address,
                            Message.subject,
                            case([(and_(Message.spam > 0,
                                Message.virusinfected == 0,
                                Message.nameinfected == 0,
                                Message.otherinfected == 0,
                                ), True)],
                                else_=False).label('spam'),
                            Message.to_domain)\
                            .filter(Message.isquarantined > 0)\
                            .filter(or_(Message.spam > 0,
                                    Message.nameinfected > 0,
                                    Message.otherinfected > 0))\
                            .order_by(desc('timestamp'))

            query = UserFilter(Session, user, messages)
            messages = query.filter()
            if int(self.options.days) > 0:
                a_day = datetime.timedelta(days=self.options.days)
                startdate = datetime.date.today() - a_day
                messages = messages.filter(Message.timestamp > str(startdate))
            messages = messages.filter(~Message.id.in_(previous_records)) 
            messages = messages[:25]

            if messages:
                lang = 'en'
                host_urls = dict([(domain.name, domain.site_url)
                            for domain in user.domains
                            if domain.status == True])
                langs = [domain.language for domain in user.domains
                        if domain.language != 'en']
                if langs:
                    lang = langs.pop(0)
                translator = set_lang(lang, pkgname, localedir)
                _ = translator.ugettext
                def make_release_records(spam):
                    "map function"
                    uuid = gen_uuid(user)
                    spam.uuid = uuid
                    return Release(uuid=uuid, messageid=spam.id)
                torelease = [make_release_records(spam) for spam in messages]
                template = mako_lookup.get_template('/email/quarantine.html')
                html = template.render(messages=messages,
                                host_urls=host_urls, url=url_for,
                                default_url=self.conf['baruwa.default.url'])
                template = mako_lookup.get_template('/email/quarantine.txt')
                text = template.render(messages=messages)
                displayname = "%s %s" % (user.firstname, user.lastname)
                email = Msg(author=[(_('Baruwa Reports'),
                                self.conf['baruwa.reports.sender'])],
                                to=[(displayname, user.email)],
                                subject=_('Baruwa quarantine report'))
                email.plain = text
                email.rich = html
                email.attach('logo.png',
                            data=logo,
                            maintype='image',
                            subtype='png',
                            inline=True)
                mailer.send(email)
                Session.add_all(torelease)
                Session.commit()
        mailer.stop()
