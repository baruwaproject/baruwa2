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
"""Routes configuration

The more specific and detailed routes should be defined first so they
may take precedent over the more generic routes. For more information
refer to the routes manual at http://routes.groovie.org/docs/
"""
from routes import Mapper


def make_map(config):
    """Create, configure and return the routes Mapper"""
    urlmap = Mapper(directory=config['pylons.paths']['controllers'],
                 always_scan=config['debug'])
    urlmap.minimization = False
    urlmap.explicit = False

    # The ErrorController route (handles 404/500 error pages); it should
    # likely stay at the top, ensuring it can always be resolved
    urlmap.connect('/error/{action}', controller='error')
    urlmap.connect('/error/{action}/{id}', controller='error')

    mqstatus_reqs = dict(serverid=R"\d+",
                    queue=R"(inbound|outbound)",
                    direction=R"(dsc|asc)",
                    order_by=R"(timestamp|from_address|"
                            "to_address|subject|size|attempts)")
    list_reqs = dict(list_type=R"[1-2]",
                    page=R"\d+",
                    direction=R"(dsc|asc)",
                    order_by=R"(id|to_address|from_address)")

    # CUSTOM ROUTES HERE
    urlmap.connect("flag",
                    "imgs/flags/{country}.png",
                    _static=True)
    urlmap.connect('home',
                    '/{.format}',
                    controller='messages',
                    action='index')
    urlmap.connect('toplevel',
                    '/{controller}{.format}',
                    action='index')
    urlmap.connect('jsi18n',
                    '/jsi18n.js',
                    controller='utils',
                    action='js_localization')
    urlmap.connect('home',
                    '/',
                    controller='messages',
                    action='index')

    # accounts
    with urlmap.submapper(path_prefix="/accounts",
            controller="accounts") as submap:
        submap.connect("accounts-login",
                "/login",
                action="login")
        submap.connect("account-detail",
                r"/detail/{userid:\d+}{.format}",
                action="detail")
        submap.connect("account-edit",
                r"/edit/{userid:\d+}",
                action="edit")
        submap.connect("account-delete",
                r"/delete/{userid:\d+}",
                action="delete")
        submap.connect('accounts-byorg',
                r'/byorg/{orgid:\d+}',
                action='index')
        submap.connect('accounts-bydom',
                r'/domain/{domid:\d+}',
                action='index')
        submap.connect('account-pages',
                r'/{page:\d+}{.format}',
                action='index')
        submap.connect('accounts-byorg-pages',
                r'/byorg/{orgid:\d+}/{page:\d+}{.format}',
                action='index')
        submap.connect('accounts-bydom-pages',
                r'/domain/{domid:\d+}/{page:\d+}{.format}',
                action='index')
        submap.connect('accounts-pwreset',
                '/passwd/reset',
                action='passwdreset')
        submap.connect('accounts-pw-token-reset',
                '/passwd/confirm/{token}',
                action='pwtokenreset')
        submap.connect('accounts-set-lang',
                '/setlang',
                action='set_language')
        submap.connect('accounts-pw-change',
                r'/pwchange/{userid:\d+}',
                action='pwchange')
        submap.connect('accounts-pw-uchange',
                r'/upwchange/{userid:\d+}',
                action='upwchange')
        submap.connect("address-add",
                r"/address/add/{userid:\d+}",
                action="addaddress")
        submap.connect("address-edit",
                r"/address/edit/{addressid:\d+}",
                action="editaddress")
        submap.connect("address-delete",
                r"/address/delete/{addressid:\d+}",
                action="deleteaddress")
        submap.connect('accounts-import',
                r'/domain/import/{domainid:\d+}',
                action='import_accounts')
        submap.connect('accounts-export',
                '/domain/export',
                action='export_accounts')
        submap.connect('accounts-export-bydom',
                r'/domain/export/{domainid:\d+}',
                action='export_accounts')
        submap.connect('accounts-export-byorg',
                r'/byorg/export/{orgid:\d+}',
                action='export_accounts')
        submap.connect('accounts-confirm-delete',
                '/confirm/delete',
                action='confirm_delete')
        submap.connect('accounts-search',
                '/search',
                action='search')
        submap.connect('accounts-import-status',
                '/domain/import/status/{taskid}',
                action='import_status')
        submap.connect('accounts-export-status',
                '/domain/export/status/{taskid}',
                action='export_status')
        submap.connect('accounts-set-items',
                '/setitems{.format}',
                action='setnum')
    # domains
    with urlmap.submapper(path_prefix="/domains",
            controller="domains") as submap:
        submap.connect('domain-detail',
                r'/detail/{domainid:\d+}{.format}',
                action='detail')
        submap.connect('domain-add-byorg',
                r'/byorg/{orgid:\d+}/add',
                action='add')
        submap.connect('domain-edit',
                r'/edit/{domainid:\d+}',
                action='edit')
        submap.connect('domain-delete',
                r'/delete/{domainid:\d+}',
                action='delete')
        submap.connect('dserver-add',
                r'/adddestination/{domainid:\d+}',
                action='adddestination')
        submap.connect('dserver-test',
                r'/testdestination/{destinationid:\d+}',
                action='testdestination')
        submap.connect('dserver-edit',
                r'/editdestination/{destinationid:\d+}',
                action='editdestination')
        submap.connect('dserver-delete',
                r'/deletedestination/{destinationid:\d+}',
                action='deletedestination')
        submap.connect('domain-pages',
                r'/{page:\d+}{.format}',
                action='index')
        submap.connect('domains-byorg',
                r'/byorg/{orgid:\d+}{.format}',
                action='index')
        submap.connect('domains-byorg-pages',
                r'/byorg/{orgid:\d+}/{page:\d+}{.format}',
                action='index')
        submap.connect('domains-add-auth',
                r'/addauth/{domainid:\d+}',
                action='add_auth')
        submap.connect('domains-edit-auth',
                r'/editauth/{authid:\d+}',
                action='edit_auth')
        submap.connect('domains-delete-auth',
                r'/delauth/{authid:\d+}',
                action='delete_auth')
        submap.connect('domains-auth-settings',
                r'/authsettings/{domainid:\d+}{sid:\d+}{.format}',
                action='auth_settings')
        submap.connect('domains-auth-settings-with-protocol',
                r'/authsettings/{proto:\d+}/{domainid:\d+}/{sid:\d+}{.format}',
                action='auth_settings')
        submap.connect('domains-rulesets',
                r'/rulesets/{domainid:\d+}',
                action='rulesets')
        submap.connect('domains-add-alias',
                r'/{domainid:\d+}/alias/add',
                action='addalias')
        submap.connect('domains-edit-alias',
                r'/alias/edit/{aliasid:\d+}',
                action='editalias')
        submap.connect('domains-delete-alias',
                r'/alias/delete/{aliasid:\d+}',
                action='deletealias')
        submap.connect('domains-confirm-delete',
                '/confirm/delete',
                action='confirm_delete')
        submap.connect('domains-search',
                '/search',
                action='search')
        submap.connect('domains-export',
                '/export',
                action='export_domains')
        submap.connect('domains-export-byorg',
                r'/export/{orgid:\d+}',
                action='export_domains')
        submap.connect('domains-export-status',
                '/export/status/{taskid}',
                action='export_status')
        submap.connect('domains-set-items',
                '/setitems{.format}',
                action='setnum')
    # messages
    with urlmap.submapper(path_prefix="/messages",
            controller="messages") as submap:
        submap.connect('message-detail',
                r'/detail/{msgid:\d+}{.format}',
                action='detail')
        submap.connect('message-archive',
                r'/archive/{msgid:\d+}{.format}',
                action='detail',
                archive=True)
        submap.connect('message-preview',
                r'/preview/{msgid:\d+}{.format}',
                action='preview')
        submap.connect('message-preview-html',
                r'/preview-html/{msgid:\d+}{.format}',
                action='preview',
                richformat=True)
        submap.connect('message-archive-preview',
                r'/archived/preview/{msgid:\d+}{.format}',
                action='preview',
                archive=True)
        submap.connect('message-archive-preview-html',
                r'/archived/preview-html/{msgid:\d+}{.format}',
                action='preview',
                archive=True,
                richformat=True)
        submap.connect('message-preview-with-imgs',
                r'/preview-with-imgs/{msgid:\d+}{.format}',
                action='preview',
                allowimgs=True,
                richformat=True)
        submap.connect('message-preview-archived-with-imgs',
                r'/preview-archived-with-imgs/{msgid:\d+}{.format}',
                action='preview',
                allowimgs=True,
                archive=True,
                richformat=True)
        submap.connect('message-autorelease',
                '/autorelease/{uuid}',
                action='autorelease')
        submap.connect('messages-attach-dw',
                r'/download/{msgid:\d+}/{attachment}',
                action='preview')
        submap.connect('messages-archived-attach-dw',
                r'/archived/download/{msgid:\d+}/{attachment}',
                action='preview',
                archive=True)
        submap.connect('messages-preview-img',
                r'/preview/{msgid:\d+}/{img}',
                action='preview')
        submap.connect('messages-preview-archived-img',
                r'/archived/preview/{msgid:\d+}/{img}',
                action='preview',
                archive=True)
        submap.connect('messages-paging',
                r'/{action}/{order_by}/{direction}/{page:\d+}{.format}')
        submap.connect('messages-qtn-paging',
        r'/quarantine/{section}/{order_by}/{direction}/{page:\d+}{.format}',
                action='quarantine')
        submap.connect('message-qtn-section',
                '/quarantine/{section}{.format}',
                action='quarantine')
        submap.connect('messages-bulk-process',
                '/process/{taskid}{.format}',
                action='process')
        submap.connect('messages-ajax-relayedvia',
                r'/ajax/relayed/{msgid:\d+}',
                action='relayed_via')
        submap.connect('messages-archived-ajax-relayedvia',
                r'/ajax-relayed-archived/{msgid:\d+}',
                action='relayed_via',
                archive=True)
        submap.connect('messages-set-items',
                '/setitems{.format}',
                action='setnum')
    # reports
    with urlmap.submapper(path_prefix="/reports",
            controller="reports") as submap:
        submap.connect('reports-display',
                r'/display/{reportid:\d+}{.format}',
                action='display')
        submap.connect('delete-filter',
                r'/filters/delete/{filterid:\d+}{.format}',
                action='delete')
        submap.connect('save-filter',
                r'/filters/save/{filterid:\d+}{.format}',
                action='save')
        submap.connect('delete-storedfilter',
                r'/storedfilters/delete/{filterid:\d+}{.format}',
                action='delete_stored')
        submap.connect('load-filter',
                r'/storedfilters/load/{filterid:\d+}{.format}',
                action='load')
        submap.connect('reports-ajax-filters',
                '/ajax/filters',
                action='show_filters')
        submap.connect('reports-ajax-filter-form',
                '/ajax/filterform',
                action='add_filters')
    # settings
    with urlmap.submapper(path_prefix="/settings",
            controller="settings") as submap:
        submap.connect('settings-addserver',
                '/node/add',
                action='new_server')
        submap.connect('scanner-edit',
                r'/node/edit/{serverid:\d+}',
                action='edit_server')
        submap.connect('scanner-delete',
                r'/node/delete/{serverid:\d+}',
                action='delete_server')
        submap.connect('settings-scanner',
                r'/node/{serverid:\d+}',
                action='config')
        submap.connect('scanner-section',
                r'/node/{serverid}/section/{sectionid:\d+}',
                action='section')
        submap.connect('settings-pages',
                r'/{page:\d+}{.format}',
                action='index')
        submap.connect('settings-mailscanner',
                '/ms',
                action='section')
        submap.connect('settings-mailscanner-sect',
                r'/ms/{sectionid:\d+}',
                action='section')
        submap.connect('domain-settings',
                r'/domain/{domainid:\d+}',
                action='domain_settings')
        submap.connect('domain-settings-sigs',
                r'/domain/branding/{domainid:\d+}',
                action='domain_sigs')
        submap.connect('domain-settings-rules',
                r'/domain/rules/{domainid:\d+}',
                action='domain_rules')
        submap.connect('domain-dkim',
                r'/domain/dkim/{domainid:\d+}',
                action='domain_dkim')
        submap.connect('domain-dkim-generate',
                r'/domain/dkim/generate/{domainid:\d+}',
                action='domain_dkim_generate')
        submap.connect('domain-dkim-enable',
                r'/domain/dkim/enable/{domainid:\d+}',
                action='domain_dkim_enable')
        submap.connect('domain-sigs-add',
                r'/domain/branding/{domainid:\d+}/add',
                action='add_domain_sigs')
        submap.connect('domain-sigs-edit',
                r'/domain/branding/edit/{sigid:\d+}',
                action='edit_domain_sigs')
        submap.connect('domain-sigs-delete',
                r'/domain/branding/delete/{sigid:\d+}',
                action='delete_domain_sigs')
        submap.connect('account-sigs-add',
                r'/account/branding/{userid:\d+}/add',
                action='add_account_sigs')
        submap.connect('account-sigs-edit',
                r'/account/branding/edit/{sigid:\d+}',
                action='edit_account_sigs')
        submap.connect('account-sigs-delete',
                r'/account/branding/delete/{sigid:\d+}',
                action='delete_account_sigs')
        submap.connect('settings-rulesets',
                r'/rulesets', action='rulesets')
        submap.connect('set-global-policies',
                r'/rulesets/global/settings',
                action='global_policies')
        submap.connect('set-domain-policies',
                r'/rulesets/domains/{domain_id:\d+}',
                action='domain_policies')
        submap.connect('archive-file-policy',
                r'/rulesets/archive-file-policy',
                action='policy_landing',
                policy_type=1)
        submap.connect('archive-mime-policy',
                r'/rulesets/archive-mime-policy',
                action='policy_landing',
                policy_type=2)
        submap.connect('file-policy',
                r'/rulesets/file-policy',
                action='policy_landing',
                policy_type=3)
        submap.connect('mime-policy',
                r'/rulesets/mime-policy',
                action='policy_landing',
                policy_type=4)
        submap.connect('archive-file-policy-pg',
                r'/rulesets/archive-file-policy/{page:\d+}',
                action='policy_landing',
                policy_type=1)
        submap.connect('archive-mime-policy-pg',
                r'/rulesets/archive-mime-policy/{page:\d+}',
                action='policy_landing',
                policy_type=2)
        submap.connect('file-policy-pg',
                r'/rulesets/file-policy/{page:\d+}',
                action='policy_landing',
                policy_type=3)
        submap.connect('mime-policy-pg',
                r'/rulesets/mime-policy/{page:\d+}',
                action='policy_landing',
                policy_type=4)
        submap.connect('clone-policy',
                r'/rulesets/clone/{policy_type:\d+}',
                action='clone_policy')
        submap.connect('view-default-policy',
                r'/rulesets/default/{policy_type:\d+}',
                action='view_default')
        submap.connect('policy-add',
                r'/rulesets/add/{policy_type:\d+}',
                action='add_policy')
        submap.connect('policy-edit',
                r'/rulesets/edit/{policy_id:\d+}',
                action='edit_policy')
        submap.connect('policy-del',
                r'/rulesets/delete/{policy_id:\d+}',
                action='delete_policy')
        submap.connect('policy-rulesets',
                r'/rulesets/policy/{policy_id:\d+}',
                action='policy_rules')
        submap.connect('add-rule',
                r'/rulesets/policy/{policy_id:\d+}/add',
                action='add_rule')
        submap.connect('edit-rule',
                r'/rulesets/rule/edit/{rule_id:\d+}',
                action='edit_rule')
        submap.connect('delete-rule',
                r'/rulesets/rule/delete/{rule_id:\d+}',
                action='delete_rule')
        submap.connect('move-rule',
                r'/rulesets/rule/move/{rule_id:\d+}/{direc:[0-1]}',
                action='move_rule')
        submap.connect('mta-setting',
                r'/mta/settings/{setting_type:\d+}',
                action='mta_landing')
        submap.connect('mta-setting-pg',
                r'/mta/settings/{setting_type:\d+}/{page:\d+}',
                action='mta_landing')
        submap.connect('mta-settings-add',
                r'/mta/settings/add/{setting_type:\d+}',
                action='add_mta_setting')
        submap.connect('mta-settings-edit',
                r'/mta/settings/edit/{setting_id:\d+}',
                action='edit_mta_setting')
        submap.connect('mta-settings-delete',
                r'/mta/settings/delete/{setting_id:\d+}',
                action='del_mta_setting')
        submap.connect('local-scores',
                r'/scores', action='local_scores')
        submap.connect('local-scores-pg',
                r'/scores/{page:\d+}', action='local_scores')
        # submap.connect('add-local-scores',
        #         r'/scores/add', action='add_local_scores')
        # submap.connect('add-local-scores-id',
        #         r'/scores/add/{score_id:\w+}',
        #         action='add_local_scores')
        submap.connect('edit-local-scores',
                r'/scores/edit/{score_id:\w+}',
                action='edit_local_scores')
        # submap.connect('delete-local-scores',
        #         r'/scores/delete/{score_id:\w+}',
        #         action='delete_local_scores')
        submap.connect('settings-set-items',
                '/setitems{.format}',
                action='setnum')
    # lists
    with urlmap.submapper(path_prefix="/lists",
            controller="lists") as submap:
        submap.connect('lists-index',
                '/{list_type:[1-2]}{.format}')
        submap.connect('list-pages',
                r'/{list_type:[1-2]}/{page:\d+}{.format}',
                action='index')
        submap.connect('list-pages-byfield',
                '/{list_type}/{page}/{direction}/{order_by}{.format}',
                action='index',
                requirements=list_reqs)
        submap.connect('lists-add',
                '/add',
                action='new')
        submap.connect('list-delete',
                r'/delete/{listid:\d+}',
                action='list_delete')
        submap.connect('lists-set-items',
                '/setitems{.format}',
                action='setnum')
    # organizations
    with urlmap.submapper(path_prefix="/organizations",
            controller="organizations") as submap:
        submap.connect('org-detail',
                r'/{orgid:\d+}{.format}',
                action='detail')
        submap.connect('orgs-add',
                '/add',
                action='new')
        submap.connect('orgs-edit',
                r'/edit/{orgid:\d+}',
                action='edit')
        submap.connect('orgs-delete',
                r'/delete/{orgid:\d+}',
                action='delete')
        submap.connect('orgs-pages',
                r'/list/{page:\d+}{.format}',
                action='index')
        submap.connect('orgs-add-relay',
                r'/{orgid:\d+}/outbound/add',
                action='add_relay')
        submap.connect('orgs-edit-relay',
                r'/outbound/edit/{settingid:\d+}',
                action='edit_relay')
        submap.connect('orgs-del-relay',
                r'/outbound/delete/{settingid:\d+}',
                action='delete_relay')
        submap.connect('orgs-import-domains',
                r'/import/domains/{orgid:\d+}',
                action='import_domains')
        submap.connect('orgs-import-status',
                '/import/domains/status/{taskid}',
                action='import_status')
        submap.connect('orgs-set-items',
                r'/setitems{.format}',
                action='setnum')
    # status
    with urlmap.submapper(path_prefix="/status",
            controller="status") as submap:
        submap.connect('status-graph',
                '/mail-stats-graph.png',
                action='graph')
        submap.connect('status-host-graph',
                r'/{nodeid}/mail-stats-graph.png',
                action='graph')
        submap.connect('mailq-detail',
                r'/mailq/detail/{queueid:\d+}{.format}',
                action='mailq_detail')
        submap.connect('mailq-preview',
                r'/mailq/preview/{queueid:\d+}',
                action='mailq_preview')
        submap.connect('mailq-preview-html',
                r'/mailq/preview-html/{queueid:\d+}',
                action='mailq_preview',
                richformat=True)
        submap.connect('queue-preview-with-imgs',
                r'/mailq/preview-with-imgs/{queueid:\d+}',
                action='mailq_preview',
                allowimgs=True,
                richformat=True)
        submap.connect('queue-preview-img',
                r'/mailq/preview/{queueid:\d+}/{imgid}',
                action='mailq_preview')
        submap.connect('queue-attach-dw',
                r'/mailq/download/{queueid:\d+}/{attachid:\d+}',
                action='mailq_preview')
        submap.connect('mailq-status',
                '/mailq',
                action='mailq')
        submap.connect('mailq-status-directed',
                r'/mailq/{queue:(inbound|outbound)}{.format}',
                action='mailq')
        submap.connect('mailq-status-paged',
                r'/mailq/{queue:(inbound|outbound)}/{page:\d+}{.format}',
                action='mailq')
        submap.connect('mailq-process',
                '/mailq/process',
                action='process_mailq')
        submap.connect('mailq-status-full',
                r'/mailq/{queue}/{direction}/{order_by}',
                action='mailq')
        submap.connect('mailq-set-items',
                r'/mailq/setitems{.format}',
                action='setnum')
        submap.connect('server-status',
                r'/node/{serverid:\d+}',
                action='server_status')
        submap.connect('server-status-bayes',
                r'/node/{serverid:\d+}/bayesian',
                action='server_bayes_status')
        submap.connect('server-status-sa',
                r'/node/{serverid:\d+}/salint',
                action='server_salint_stat')
        submap.connect('server-status-mq-in',
                r'/node/{serverid:\d+}/mailq/inbound',
                action='mailq',
                queue='inbound')
        submap.connect('server-status-mq-out',
                r'/node/{serverid:\d+}/mailq/outbound',
                action='mailq',
                queue='outbound')
        submap.connect('server-status-mq',
                r'/node/{serverid:\d+}/mailq/{queue}/{direction}/{order_by}',
                action='mailq',
                requirements=mqstatus_reqs)
        submap.connect('server-status-mq-paged',
                r'/mailq/{queue:(inbound|outbound)}/{page:\d+}{.format}',
                action='mailq')
        submap.connect('status-audit-logs',
                r'/audit{.format}',
                action='audit')
        submap.connect('status-audit-log-paged',
                r'/audit/{page:\d+}{.format}',
                action='audit')
        submap.connect('status-audit-export',
                r'/audit/export{.format}',
                action='audit_export')
        submap.connect('status-audit-search-export',
                r'/audit/searchresults/export{.format}',
                action='audit_export',
                isquery=True)
        submap.connect('status-auditlog-export-status',
                r'/audit/export/status/{taskid}',
                action='audit_export_status')
    # file manager
    with urlmap.submapper(path_prefix="/fm",
            controller='filemanager') as submap:
        submap.connect('fm-auth',
                '/auth',
                action='index')
        submap.connect('fm-domains',
                r'/domain/{domainid:\d+}',
                action='index')
        submap.connect('fm-users',
                r'/user/{userid:\d+}',
                action='index')
        submap.connect('fm-view-img',
                r'/{sigtype:(domains|users)}/{imgid}{.format:(gif|png|jpg)}',
                action='view_img')

    # invite
    with urlmap.submapper(path_prefix="/invite",
            controller="invite") as submap:
        submap.connect('invite-register',
                r'/register/{token}',
                action='register')

    urlmap.connect('/{controller}/{action}{.format}')
    urlmap.connect(r'/{controller}/{action}/{id:\d+}{.format}')
    urlmap.connect(r'/{controller}/{action}/{userid:\d+}')
    urlmap.connect(r'/{controller}/{action}/{addressid:\d+}')
    urlmap.connect(r'/{controller}/{action}/{domainid:\d+}')
    urlmap.connect(r'/{controller}/{action}/{id:\d+}')

    return urlmap
