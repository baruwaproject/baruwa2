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

"Cluster functions"
from beaker.cache import cache_region
from celery.exceptions import TimeoutError, QueueNotFound

from baruwa.model.meta import Session
from baruwa.model.settings import Server
from baruwa.tasks.status import systemstatus


@cache_region('system_status', 'cluster-status')
def cluster_status():
    "Check cluster status"
    hosts = Session.query(Server.hostname)\
            .filter(Server.enabled == True).all()
    if not hosts:
        return False
    for host in hosts:
        if host.hostname == 'default':
            continue
        if not host_status(host.hostname):
            return False
    return True


@cache_region('system_status', 'host-status')
def host_status(hostname):
    "Check host status"
    try:
        task = systemstatus.apply_async(queue=hostname)
        task.wait(30)
        hoststatus = task.result
    except (TimeoutError, QueueNotFound):
        return False
    # check load
    if hoststatus['load'][0] > 15:
        return False
    # return quick if any service is not running
    for service in ['mta', 'scanners', 'av']:
        if hoststatus[service] == 0:
            return False
    # check disks
    for part in hoststatus['partitions']:
        if part['percent'] >= 95:
            return False
    return True
    