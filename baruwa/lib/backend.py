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
"Backend functions"

from baruwa.lib.mq import FANOUT_XCHG
from baruwa.tasks.mta import (create_relay_domains, create_relay_hosts,
    create_relay_proto_domains, create_ldap_domains, create_ldap_data,
    create_callback_domains, create_domain_lists, create_route_data,
    create_auth_data, create_smtp, create_lmtp, create_post_smtp_av,
    create_av_disabled, create_ratelimit, create_mta_settings)
from baruwa.tasks.settings import (create_language_based, create_message_size,
    create_highspam_scores, create_spam_scores, create_highspam_actions,
    create_spam_actions, create_virus_checks, create_spam_checks,
    update_serial, create_lists, get_ruleset, create_content_rules,
    create_content_ruleset, create_local_scores)


def backend_user_update(user, force=False):
    "Perform required backend updates"
    update = False
    if force or user.spam_checks is False:
        create_spam_checks.apply_async(exchange=FANOUT_XCHG)
        update = True
    if force or user.low_score > 0:
        create_spam_scores.apply_async(exchange=FANOUT_XCHG)
        update = True
    if force or user.high_score > 0:
        create_highspam_scores.apply_async(exchange=FANOUT_XCHG)
        update = True
    if update:
        update_serial.apply_async(exchange=FANOUT_XCHG)


def update_domain_backend(domain, force=False):
    "Update the required backend files"
    create_relay_domains.apply_async(exchange=FANOUT_XCHG)
    create_callback_domains.apply_async(exchange=FANOUT_XCHG)
    create_post_smtp_av.apply_async(exchange=FANOUT_XCHG)
    create_av_disabled.apply_async(exchange=FANOUT_XCHG)
    create_ldap_domains.apply_async(exchange=FANOUT_XCHG)
    create_smtp.apply_async(args=[1], exchange=FANOUT_XCHG)
    create_lmtp.apply_async(args=[1], exchange=FANOUT_XCHG)
    create_smtp.apply_async(args=[2], exchange=FANOUT_XCHG)
    create_lmtp.apply_async(args=[2], exchange=FANOUT_XCHG)
    create_route_data.apply_async(exchange=FANOUT_XCHG)
    update = False
    if force or domain.language != 'en':
        create_language_based.apply_async(exchange=FANOUT_XCHG)
        update = True
    if force or domain.message_size != '0':
        create_message_size.apply_async(exchange=FANOUT_XCHG)
        update = True
    if force or domain.high_score > 0:
        create_highspam_scores.apply_async(exchange=FANOUT_XCHG)
        update = True
    if force or domain.low_score > 0:
        create_spam_scores.apply_async(exchange=FANOUT_XCHG)
        update = True
    if force or domain.highspam_actions != 2:
        create_highspam_actions.apply_async(exchange=FANOUT_XCHG)
        update = True
    if force or domain.spam_actions != 2:
        create_spam_actions.apply_async(exchange=FANOUT_XCHG)
        update = True
    if force or domain.virus_checks is False or \
            domain.virus_checks_at_smtp is False:
        create_virus_checks.apply_async(exchange=FANOUT_XCHG)
        update = True
    if force or domain.spam_checks is False:
        create_spam_checks.apply_async(exchange=FANOUT_XCHG)
        update = True
    if update:
        update_serial.apply_async(exchange=FANOUT_XCHG)


def update_relay_backend(relay, force=False):
    "Update the required backend files"
    update = False
    create_relay_hosts.apply_async(exchange=FANOUT_XCHG)
    create_auth_data.apply_async(exchange=FANOUT_XCHG)
    create_ratelimit.apply_async(exchange=FANOUT_XCHG)
    if force or relay.high_score > 0:
        create_highspam_scores.apply_async(exchange=FANOUT_XCHG)
        update = True
    if force or relay.low_score > 0:
        create_spam_scores.apply_async(exchange=FANOUT_XCHG)
        update = True
    if force or relay.highspam_actions != 2:
        create_highspam_actions.apply_async(exchange=FANOUT_XCHG)
        update = True
    if force or relay.spam_actions != 2:
        create_spam_actions.apply_async(exchange=FANOUT_XCHG)
        update = True
    if update:
        update_serial.apply_async(exchange=FANOUT_XCHG)


def update_destination_backend(protocol):
    """Update the required backend files"""
    create_smtp.apply_async(args=[1], exchange=FANOUT_XCHG)
    create_lmtp.apply_async(args=[1], exchange=FANOUT_XCHG)
    create_smtp.apply_async(args=[2], exchange=FANOUT_XCHG)
    create_lmtp.apply_async(args=[2], exchange=FANOUT_XCHG)
    create_relay_proto_domains.apply_async(args=[protocol],
                                        exchange=FANOUT_XCHG)
    create_route_data.apply_async(exchange=FANOUT_XCHG)


def update_auth_backend(protocol):
    """Update the required backend files"""
    if protocol == 5:
        create_ldap_domains.apply_async(exchange=FANOUT_XCHG)


def update_ldap_backend():
    """Update the required backend file"""
    create_ldap_data.apply_async(exchange=FANOUT_XCHG)


def update_lists_backend(list_type):
    """Update the required backend files"""
    create_lists.apply_async(args=[list_type], exchange=FANOUT_XCHG)
    create_domain_lists.apply_async(args=[list_type], exchange=FANOUT_XCHG)
    update_serial.apply_async(exchange=FANOUT_XCHG)


def get_ruleset_data(filename, hostname):
    """Get ruleset data"""
    task = get_ruleset.apply_async(args=[filename], queue=hostname)
    task.wait(30)
    if task.result:
        rules = task.result
    else:
        rules = []
    return rules


def backend_create_content_rules(policy_id, policy_name, remove=None):
    """Create content rules"""
    create_content_rules.apply_async(args=[policy_id, policy_name, remove],
                                    exchange=FANOUT_XCHG)


def backend_create_content_ruleset():
    """Create content ruleset"""
    create_content_ruleset.apply_async(exchange=FANOUT_XCHG)


def backend_create_mta_settings(setting_type):
    """Create MTA settings files"""
    create_mta_settings.apply_async(args=[setting_type], exchange=FANOUT_XCHG)


def backend_create_local_scores():
    """Create local scores"""
    create_local_scores.apply_async(exchange=FANOUT_XCHG)
