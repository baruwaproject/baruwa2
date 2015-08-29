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
"""cache functions"""

from pylons import config
from pylibmc import Client

LOCK_EXPIRE = 60 * 5


def cache(localconfig=None):
    "cache object"
    if localconfig:
        server = localconfig.get('baruwa.memcached.host', '127.0.0.1')
    else:
        server = config.get('baruwa.memcached.host', '127.0.0.1')
    beh = {"tcp_nodelay": True, "ketama": True}
    conn = Client([server], binary=True, behaviors=beh)
    return conn


def acquire_lock(key, localconfig=None, timeout=LOCK_EXPIRE):
    "acquire lock"
    return cache(localconfig).add(key, 'true', timeout)


def release_lock(key, localconfig=None):
    "release the lock"
    cache(localconfig).delete(key)


def release_lock_after(key, timeout, localconfig=None):
    "release the lock after timeout"
    cache(localconfig).replace(key, 'true', timeout)
