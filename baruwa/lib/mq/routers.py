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

"celery routers for baruwa"

class BaruwaRouter(object):
    """Route tasks to workers"""

    def route_for_task(self, task, args=None, kwargs=None):
        #print "=" * 100, task
        if task in ['delete-signature-files', 'save-domain-signature',
                    'save-user-signature']:
            return dict(exchange='msbackend',
                        exchange_type='fanout',
                        routing_key='mstasks')
        if task in ['import-accounts', 'import-domains', 'export-accounts',
            'export-domains', 'process-quarantine', 'test-smtp-server']:
            return dict(exchange='default',
                        exchange_type='default',
                        routing_key='default')
        if task in ['get-bayes-info', 'get-system-status', 'preview-message',
            'process-quarantined-msg', 'release-message',
            'spamassassin-lint']:
            #print '+' * 10
            hostname = kwargs.get('hostname')
            return dict(queue=hostname)
            # return dict(exchange=host,
            #             #exchange_type='default',
            #             routing_key=hostname)
        return None
        