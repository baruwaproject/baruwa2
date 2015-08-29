# -*- coding: utf-8 -*-
# Baruwa - Web 2.0 MailScanner front-end.
# Copyright (C) 2010-2015  Andrew Colin Kissa <andrew@topdog.za.net>
# vim: ai ts=4 sts=4 et sw=4

"Baruwa tasks"

from baruwa.tasks.organizations import importdomains
from baruwa.tasks.domains import test_smtp_server, exportdomains
from baruwa.tasks.accounts import importaccounts, exportaccounts
from baruwa.tasks.messages import (release_message, preview_msg,
    process_quarantined_msg, update_autorelease)
from baruwa.tasks.status import (update_audit_log, export_auditlog,
    systemstatus, salint, bayesinfo, preview_queued_msg, process_queued_msgs)
from baruwa.tasks.settings import (create_spam_checks, create_virus_checks,
    create_spam_actions, create_highspam_actions, create_lists,
    create_message_size, create_language_based, create_sign_clean,
    create_spam_scores, create_highspam_scores, create_html_sigs,
    create_text_sigs, create_sig_imgs, create_sig_img_names, get_ruleset,
    create_content_rules, create_content_ruleset, create_local_scores,
    create_ms_settings, save_dkim_key, delete_dkim_key, reload_exim,
    delete_sig, save_dom_sig, save_user_sig)
from baruwa.tasks.mta import (create_relay_domains, create_relay_hosts,
    create_relay_proto_domains, create_ldap_domains, create_ldap_data,
    create_callback_domains, create_domain_lists, create_route_data,
    create_auth_data, create_smtp, create_lmtp, create_post_smtp_av,
    create_av_disabled, create_ratelimit, create_mta_settings)
try:
    from baruwa.tasks.invite import create_mx_records, delete_mx_records
    assert create_mx_records
    assert delete_mx_records
except ImportError:
    pass

assert release_message
assert preview_msg
assert process_quarantined_msg
assert update_autorelease
assert test_smtp_server
assert exportdomains
assert importdomains
assert importaccounts
assert exportaccounts
assert update_audit_log
assert export_auditlog
assert systemstatus
assert salint
assert bayesinfo
assert preview_queued_msg
assert process_queued_msgs
assert preview_queued_msg
assert process_queued_msgs
assert delete_sig
assert save_dom_sig
assert save_user_sig
assert save_dkim_key
assert delete_dkim_key
assert reload_exim
assert create_spam_checks
assert create_virus_checks
assert create_spam_actions
assert create_highspam_actions
assert create_lists
assert create_message_size
assert create_language_based
assert create_sign_clean
assert create_spam_scores
assert create_highspam_scores
assert create_html_sigs
assert create_text_sigs
assert create_sig_imgs
assert create_sig_img_names
assert create_relay_domains
assert create_relay_hosts
assert create_relay_proto_domains
assert create_ldap_domains
assert create_ldap_data
assert create_callback_domains
assert create_domain_lists
assert create_route_data
assert create_auth_data
assert create_smtp
assert create_lmtp
assert create_post_smtp_av
assert create_av_disabled
assert create_ratelimit
assert get_ruleset
assert create_content_rules
assert create_content_ruleset
assert create_mta_settings
assert create_local_scores
assert create_ms_settings
