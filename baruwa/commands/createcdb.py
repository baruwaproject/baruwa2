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
"Generate MTA cdb files"
import os


from baruwa.tasks.settings import create_ms_settings
from baruwa.commands import BaseCommand, change_user
from baruwa.tasks.mta import create_relay_domains, create_relay_hosts, \
    create_relay_proto_domains, create_ldap_domains,\
    create_ldap_data, create_callback_domains, create_domain_lists, \
    create_route_data, create_auth_data, \
    create_smtp, create_lmtp, create_ratelimit, \
    create_post_smtp_av, create_av_disabled, create_mta_settings


class CreateCDBCommand(BaseCommand):
    "Create CDB files command"

    summary = 'Generates cdb lookup files for Exim'
    group_name = 'baruwa'

    def command(self):
        "command"
        self.init()
        change_user("baruwa", "exim")
        oldmask = os.umask(027)

        # generate
        create_relay_domains()
        create_relay_hosts()
        create_relay_proto_domains(1)
        create_relay_proto_domains(2)
        create_ldap_domains()
        create_ldap_data()
        create_callback_domains()
        create_domain_lists(1)
        create_domain_lists(2)
        create_route_data()
        create_auth_data()
        create_smtp(1)
        create_smtp(2)
        create_lmtp(1)
        create_lmtp(2)
        create_post_smtp_av()
        create_av_disabled()
        create_ratelimit()
        for num in range(1, 11):
            create_mta_settings(num)
        create_ms_settings()
        os.umask(oldmask)
