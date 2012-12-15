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

    #accounts
    with urlmap.submapper(path_prefix="/accounts",
        controller="accounts") as submap:
        submap.connect("accounts-login",
                "/login",
                action="login")
        submap.connect("account-detail",
                "/detail/{userid:\d+}{.format}",
                action="detail")
        submap.connect("account-edit",
                "/edit/{userid:\d+}",
                action="edit")
        submap.connect("account-delete",
                "/delete/{userid:\d+}",
                action="delete")
        submap.connect('accounts-byorg',
                '/byorg/{orgid:\d+}',
                action='index')
        submap.connect('accounts-bydom',
                '/domain/{domid:\d+}',
                action='index')
        submap.connect('account-pages',
                '/{page:\d+}{.format}',
                action='index')
        submap.connect('accounts-byorg-pages',
                '/byorg/{orgid:\d+}/{page:\d+}{.format}',
                action='index')
        submap.connect('accounts-bydom-pages',
                '/domain/{domid:\d+}/{page:\d+}{.format}',
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
                '/pwchange/{userid:\d+}',
                action='pwchange')
        submap.connect('accounts-pw-uchange',
                '/upwchange/{userid:\d+}',
                action='upwchange')
        submap.connect("address-add",
                "/address/add/{userid:\d+}",
                action="addaddress")
        submap.connect("address-edit",
                "/address/edit/{addressid:\d+}",
                action="editaddress")
        submap.connect("address-delete",
                "/address/delete/{addressid:\d+}",
                action="deleteaddress")
        submap.connect('accounts-import',
                '/domain/import/{domainid:\d+}',
                action='import_accounts')
        submap.connect('accounts-export',
                '/domain/export',
                action='export_accounts')
        submap.connect('accounts-export-bydom',
                '/domain/export/{domainid:\d+}',
                action='export_accounts')
        submap.connect('accounts-export-byorg',
                '/byorg/export/{orgid:\d+}',
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
    #domains
    with urlmap.submapper(path_prefix="/domains",
        controller="domains") as submap:
        submap.connect('domain-detail',
                '/detail/{domainid:\d+}{.format}',
                action='detail')
        submap.connect('domain-add-byorg',
                '/byorg/{orgid:\d+}/add',
                action='add')
        submap.connect('domain-edit',
                '/edit/{domainid:\d+}',
                action='edit')
        submap.connect('domain-delete',
                '/delete/{domainid:\d+}',
                action='delete')
        submap.connect('dserver-add',
                '/adddestination/{domainid:\d+}',
                action='adddestination')
        submap.connect('dserver-test',
                '/testdestination/{destinationid:\d+}',
                action='testdestination')
        submap.connect('dserver-edit',
                '/editdestination/{destinationid:\d+}',
                action='editdestination')
        submap.connect('dserver-delete',
                '/deletedestination/{destinationid:\d+}',
                action='deletedestination')
        submap.connect('domain-pages',
                '/{page:\d+}{.format}',
                action='index')
        submap.connect('domains-byorg',
                '/byorg/{orgid:\d+}{.format}',
                action='index')
        submap.connect('domains-byorg-pages',
                '/byorg/{orgid:\d+}/{page:\d+}{.format}',
                action='index')
        submap.connect('domains-add-auth',
                '/addauth/{domainid:\d+}',
                action='add_auth')
        submap.connect('domains-edit-auth',
                '/editauth/{authid:\d+}',
                action='edit_auth')
        submap.connect('domains-delete-auth',
                '/delauth/{authid:\d+}',
                action='delete_auth')
        submap.connect('domains-auth-settings',
                '/authsettings/{domainid:\d+}{.format}',
                action='auth_settings')
        submap.connect('domains-auth-settings-with-protocol',
                '/authsettings/{proto:\d+}/{domainid:\d+}{.format}',
                action='auth_settings')
        submap.connect('domains-rulesets',
                '/rulesets/{domainid:\d+}',
                action='rulesets')
        submap.connect('domains-add-alias',
                '/{domainid:\d+}/alias/add',
                action='addalias')
        submap.connect('domains-edit-alias',
                '/alias/edit/{aliasid:\d+}',
                action='editalias')
        submap.connect('domains-delete-alias',
                '/alias/delete/{aliasid:\d+}',
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
                '/export/{orgid:\d+}',
                action='export_domains')
        submap.connect('domains-export-status',
                '/export/status/{taskid}',
                action='export_status')
        submap.connect('domains-set-items',
                '/setitems{.format}',
                action='setnum')
    #messages
    with urlmap.submapper(path_prefix="/messages",
        controller="messages") as submap:
        submap.connect('message-detail',
                '/detail/{id}{.format}',
                action='detail')
        submap.connect('message-archive',
                '/archive/{id}{.format}',
                action='detail',
                archive=True)
        submap.connect('message-preview',
                '/preview/{id}{.format}',
                action='preview')
        submap.connect('message-archive-preview',
                '/archived/preview/{id}{.format}',
                action='preview',
                archive=True)
        submap.connect('message-preview-with-imgs',
                '/preview-with-imgs/{id}{.format}',
                action='preview',
                allowimgs=True)
        submap.connect('message-preview-archived-with-imgs',
                '/preview-archived-with-imgs/{id}{.format}',
                action='preview',
                allowimgs=True,
                archive=True)
        submap.connect('message-autorelease',
                '/autorelease/{uuid}',
                action='autorelease')
        submap.connect('messages-attach-dw',
                '/download/{id}/{attachment}',
                action='preview')
        submap.connect('messages-archived-attach-dw',
                '/archived/download/{id}/{attachment}',
                action='preview',
                archive=True)
        submap.connect('messages-preview-img',
                '/preview/{id}/{img}',
                action='preview')
        submap.connect('messages-preview-archived-img',
                '/archived/preview/{id}/{img}',
                action='preview',
                archive=True)
        submap.connect('messages-paging',
                '/{action}/{order_by}/{direction}/{page:\d+}{.format}')
        submap.connect('messages-qtn-paging',
                '/quarantine/{section}/{order_by}/{direction}/{page:\d+}{.format}',
                action='quarantine')
        submap.connect('message-qtn-section',
                '/quarantine/{section}{.format}',
                action='quarantine')
        submap.connect('messages-bulk-process',
                '/process/{taskid}{.format}',
                action='process')
        submap.connect('messages-ajax-relayedvia',
                '/ajax/relayed/{id}',
                action='relayed_via')
        submap.connect('messages-archived-ajax-relayedvia',
                '/ajax-relayed-archived/{id}',
                action='relayed_via',
                archive=True)
        submap.connect('messages-set-items',
                '/setitems{.format}',
                action='setnum')
    #reports
    with urlmap.submapper(path_prefix="/reports",
        controller="reports") as submap:
        submap.connect('reports-display',
                '/display/{reportid:\d+}{.format}',
                action='display')
        submap.connect('delete-filter',
                '/filters/delete/{filterid:\d+}{.format}',
                action='delete')
        submap.connect('save-filter',
                '/filters/save/{filterid:\d+}{.format}',
                action='save')
        submap.connect('delete-storedfilter',
                '/storedfilters/delete/{filterid:\d+}{.format}',
                action='delete_stored')
        submap.connect('load-filter',
                '/storedfilters/load/{filterid:\d+}{.format}',
                action='load')
        submap.connect('reports-ajax-filters',
                '/ajax/filters',
                action='show_filters')
        submap.connect('reports-ajax-filter-form',
                '/ajax/filterform',
                action='add_filters')
    #settings
    with urlmap.submapper(path_prefix="/settings",
        controller="settings") as submap:
        submap.connect('settings-addserver',
                '/node/add',
                action='new_server')
        submap.connect('scanner-edit',
                '/node/edit/{serverid:\d+}',
                action='edit_server')
        submap.connect('scanner-delete',
                '/node/delete/{serverid:\d+}',
                action='delete_server')
        submap.connect('settings-scanner',
                '/node/{serverid:\d+}',
                action='config')
        submap.connect('scanner-section',
                '/node/{serverid}/section/{sectionid:\d+}',
                action='section')
        submap.connect('settings-pages',
                '/{page:\d+}{.format}',
                action='index')
        submap.connect('settings-mailscanner',
                '/ms',
                action='section')
        submap.connect('settings-mailscanner-sect',
                '/ms/{sectionid:\d+}',
                action='section')
        submap.connect('domain-settings',
                '/domain/{domainid:\d+}',
                action='domain_settings')
        submap.connect('domain-settings-sigs',
                '/domain/branding/{domainid:\d+}',
                action='domain_sigs')
        submap.connect('domain-settings-rules',
                '/domain/rules/{domainid:\d+}',
                action='domain_rules')
        submap.connect('domain-dkim',
                '/domain/dkim/{domainid:\d+}',
                action='domain_dkim')
        submap.connect('domain-dkim-generate',
                '/domain/dkim/generate/{domainid:\d+}',
                action='domain_dkim_generate')
        submap.connect('domain-dkim-enable',
                '/domain/dkim/enable/{domainid:\d+}',
                action='domain_dkim_enable')
        submap.connect('domain-sigs-add',
                '/domain/branding/{domainid:\d+}/add',
                action='add_domain_sigs')
        submap.connect('domain-sigs-edit',
                '/domain/branding/edit/{sigid:\d+}',
                action='edit_domain_sigs')
        submap.connect('domain-sigs-delete',
                '/domain/branding/delete/{sigid:\d+}',
                action='delete_domain_sigs')
        submap.connect('account-sigs-add',
                '/account/branding/{userid:\d+}/add',
                action='add_account_sigs')
        submap.connect('account-sigs-edit',
                '/account/branding/edit/{sigid:\d+}',
                action='edit_account_sigs')
        submap.connect('account-sigs-delete',
                '/account/branding/delete/{sigid:\d+}',
                action='delete_account_sigs')
        submap.connect('settings-set-items',
                '/setitems{.format}',
                action='setnum')
    #lists
    with urlmap.submapper(path_prefix="/lists",
        controller="lists") as submap:
        submap.connect('lists-index',
                '/{list_type:[1-2]}{.format}')
        submap.connect('list-pages',
                '/{list_type:[1-2]}/{page:\d+}{.format}',
                action='index')
        submap.connect('list-pages-byfield',
                '/{list_type}/{page}/{direction}/{order_by}{.format}',
                action='index',
                requirements=list_reqs)
        submap.connect('lists-add',
                '/add',
                action='new')
        submap.connect('list-delete',
                '/delete/{listid:\d+}',
                action='list_delete')
        submap.connect('lists-set-items',
                '/setitems{.format}',
                action='setnum')
    #organizations
    with urlmap.submapper(path_prefix="/organizations",
        controller="organizations") as submap:
        submap.connect('org-detail',
                '/{orgid:\d+}{.format}',
                action='detail')
        submap.connect('orgs-add',
                '/add',
                action='new')
        submap.connect('orgs-edit',
                '/edit/{orgid:\d+}',
                action='edit')
        submap.connect('orgs-delete',
                '/delete/{orgid:\d+}',
                action='delete')
        submap.connect('orgs-pages',
                '/list/{page:\d+}{.format}',
                action='index')
        submap.connect('orgs-add-relay',
                '/{orgid:\d+}/outbound/add',
                action='add_relay')
        submap.connect('orgs-edit-relay',
                '/outbound/edit/{settingid:\d+}',
                action='edit_relay')
        submap.connect('orgs-del-relay',
                '/outbound/delete/{settingid:\d+}',
                action='delete_relay')
        submap.connect('orgs-import-domains',
                '/import/domains/{orgid:\d+}',
                action='import_domains')
        submap.connect('orgs-import-status',
                '/import/domains/status/{taskid}',
                action='import_status')
        submap.connect('orgs-set-items',
                '/setitems{.format}',
                action='setnum')
    #status
    with urlmap.submapper(path_prefix="/status",
        controller="status") as submap:
        submap.connect('status-graph',
                '/mail-stats-graph.png',
                action='graph')
        submap.connect('status-host-graph',
                '/{nodeid}/mail-stats-graph.png',
                action='graph')
        submap.connect('mailq-detail',
                '/mailq/detail/{queueid}{.format}',
                action='mailq_detail')
        submap.connect('mailq-preview',
                '/mailq/preview/{queueid}',
                action='mailq_preview')
        submap.connect('queue-preview-with-imgs',
                '/mailq/preview-with-imgs/{queueid}',
                action='mailq_preview',
                allowimgs=True)
        submap.connect('queue-preview-img',
                '/mailq/preview/{queueid}/{imgid}',
                action='mailq_preview')
        submap.connect('queue-attach-dw',
                '/mailq/download/{queueid}/{attachid}',
                action='mailq_preview')
        submap.connect('mailq-status',
                '/mailq',
                action='mailq')
        submap.connect('mailq-status-directed',
                '/mailq/{queue:(inbound|outbound)}{.format}',
                action='mailq')
        submap.connect('mailq-status-paged',
                '/mailq/{queue:(inbound|outbound)}/{page:\d+}{.format}',
                action='mailq')
        submap.connect('mailq-process',
                '/mailq/process',
                action='process_mailq')
        submap.connect('mailq-status-full',
                '/mailq/{queue}/{direction}/{order_by}',
                action='mailq')
        submap.connect('mailq-set-items',
                '/mailq/setitems{.format}',
                action='setnum')
        submap.connect('server-status',
                '/node/{serverid:\d+}',
                action='server_status')
        submap.connect('server-status-bayes',
                '/node/{serverid:\d+}/bayesian',
                action='server_bayes_status')
        submap.connect('server-status-sa',
                '/node/{serverid:\d+}/salint',
                action='server_salint_stat')
        submap.connect('server-status-mq-in',
                '/node/{serverid:\d+}/mailq/inbound',
                action='mailq',
                queue='inbound')
        submap.connect('server-status-mq-out',
                '/node/{serverid:\d+}/mailq/outbound',
                action='mailq',
                queue='outbound')
        submap.connect('server-status-mq',
                '/node/{serverid}/mailq/{queue}/{direction}/{order_by}',
                action='mailq',
                requirements=mqstatus_reqs)
        submap.connect('server-status-mq-paged',
                '/mailq/{queue:(inbound|outbound)}/{page:\d+}{.format}',
                action='mailq')
        submap.connect('status-audit-logs',
                '/audit{.format}',
                action='audit')
        submap.connect('status-audit-log-paged',
                '/audit/{page:\d+}{.format}',
                action='audit')
        submap.connect('status-audit-export',
                '/audit/export{.format}',
                action='audit_export')
        submap.connect('status-audit-search-export',
                '/audit/searchresults/export{.format}',
                action='audit_export',
                isquery=True)
        submap.connect('status-auditlog-export-status',
                '/audit/export/status/{taskid}',
                action='audit_export_status')
    #file manager
    with urlmap.submapper(path_prefix="/fm",
        controller='filemanager') as submap:
        submap.connect('fm-auth',
                '/auth',
                action='index')
        submap.connect('fm-domains',
                '/domain/{domainid:\d+}',
                action='index')
        submap.connect('fm-users',
                '/user/{userid:\d+}',
                action='index')
        submap.connect('fm-view-img',
                '/{sigtype:(domains|users)}/{imgid}{.format:(gif|png|jpg)}',
                action='view_img')
    # invite
    with urlmap.submapper(path_prefix="/invite",
        controller="invite") as submap:
        submap.connect('invite-register',
                '/register/{token}',
                action='register')
    
    urlmap.connect('/{controller}/{action}{.format}')
    urlmap.connect('/{controller}/{action}/{id}{.format}')
    urlmap.connect('/{controller}/{action}/{userid:\d+}')
    urlmap.connect('/{controller}/{action}/{addressid:\d+}')
    urlmap.connect('/{controller}/{action}/{domainid:\d+}')
    urlmap.connect('/{controller}/{action}/{id:\d+}')

    return urlmap
