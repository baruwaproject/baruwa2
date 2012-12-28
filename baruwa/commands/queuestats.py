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
"Queuestats"
import os
import sys
import fcntl
import warnings

from eventlet.green import subprocess

from baruwa.model.meta import Session
from baruwa.commands import BaseCommand
from baruwa.lib.mail.queue import Mailq
from baruwa.lib.misc import get_config_option
from baruwa.model.status import MailQueueItem

def runquery(queue, direction, ids):
    "run querys"
    for item in queue:
        item['direction'] = direction
        if len(item['to_address']) == 1:
            if item['messageid'] in ids:
                mqitems = Session.query(MailQueueItem)\
                        .filter(MailQueueItem.messageid \
                        == item['messageid']).all()
                for mqitem in mqitems:
                    for key in ['attempts', 'lastattempt', 'direction']:
                        setattr(mqitem, key, item[key])
                    Session.add(mqitem)
            else:
                addrs = item['to_address']
                if '@' in item['from_address']:
                    item['from_domain'] = item['from_address'].split('@')[1]
                for addr in addrs:
                    item['to_address'] = addr
                    item['to_domain'] = addr.split('@')[1]
                    mqitem = MailQueueItem(item['messageid'])
                    for key in item:
                        setattr(mqitem, key, item[key])
                    Session.add(mqitem)
        else:
            addrs = item['to_address']
            for addr in addrs:
                item['to_address'] = addr
                if item['messageid'] in ids:
                    mqitem = Session.query(MailQueueItem)\
                            .filter(MailQueueItem.messageid\
                            == item['messageid'])\
                            .filter(MailQueueItem.to_address\
                            == item['to_address']).one()
                    for key in ['attempts', 'lastattempt', 'direction']:
                        setattr(mqitem, key, item[key])
                else:
                    if '@' in item['from_address']:
                        item['from_domain'] = item['from_address'].split('@')[1]
                    item['to_domain'] = addr.split('@')[1]
                    mqitem = MailQueueItem(item['messageid'])
                    for key in item:
                        setattr(mqitem, key, item[key])
                Session.add(mqitem)
        Session.commit()


def populate_db(queueitems, qdir, direction, preids):
    "process queue"
    if queueitems:
        print >> sys.stderr, ("== Processing queue: %(q)s with "
            "%(i)d items ==" % dict(q=qdir, i=len(queueitems)))
        runquery(queueitems, direction, preids)
    else:
        print >> sys.stderr, "== Skipping queue: %(q)s" % dict(q=qdir)


def process_queue(queuedir, direction):
    "delete flagged items, read in new items"
    print >> sys.stderr, ("== Delete flaged queue items"
                        " from: %(q)s ==") % dict(q=queuedir)
    ditems = Session.query(MailQueueItem.messageid)\
            .filter(MailQueueItem.flag == 1)\
            .filter(MailQueueItem.direction == direction).all()
    mailq = Mailq(queuedir)
    torm = mailq.delete([item.messageid for item in ditems])
    if torm:
        Session.query(MailQueueItem)\
                .filter(MailQueueItem.messageid.in_(torm))\
                .delete(synchronize_session='fetch')
        Session.commit()
    print >> sys.stderr, ("== Deleted %(num)d items from: %(q)s"
            % dict(num=len(torm), q=queuedir))
    mailq()
    return [item['messageid'] for item in mailq], mailq


def update_queue_stats(hostname):
    "Update queue stats"
    inqdir = get_config_option('IncomingQueueDir')
    outqdir = get_config_option('OutgoingQueueDir')

    allids, inqueue = process_queue(inqdir, 1)
    tmpids, outqueue = process_queue(outqdir, 2)
    allids.extend(tmpids)

    dbids = [item.messageid
            for item in Session.query(MailQueueItem.messageid)\
                                .filter(MailQueueItem.hostname == hostname)\
                                .all()]
    remids = [item for item in dbids if not item in allids]
    preids = [item for item in dbids if not item in remids]

    if remids:
        print >> sys.stderr, ("== Deleting %(items)d queue "
                "items from DB ==" % dict(items=len(remids)))
        Session.query(MailQueueItem)\
                .filter(MailQueueItem.messageid.in_(remids))\
                .delete(synchronize_session='fetch')
        Session.commit()

    populate_db(inqueue, inqdir, 1, preids)
    populate_db(outqueue, outqdir, 2, preids)


class QueueStats(BaseCommand):
    "Read the items in the queue and populate DB"
    summary = 'Read the items in the queue and populate DB'
    group_name = 'baruwa'

    def command(self):
        "run command"
        self.init()
        try:
            lockfile = os.path.join(self.conf['baruwa.locks.dir'], 'queuestats.lock')
            with open(lockfile, 'w+') as lock:
                fcntl.lockf(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                pipe = subprocess.Popen(['/bin/hostname'],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
                # hostname = pipe.stdout.read().strip()
                hostname = pipe.communicate()[0]
                pipe.wait(timeout=10)
                hostname = hostname.strip()
                update_queue_stats(hostname)
        except IOError:
            warnings.warn("Queuestats already running !")
            sys.exit(2)
