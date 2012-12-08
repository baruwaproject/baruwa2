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

"status models"

from sqlalchemy import Column
# from pylons.i18n.translation import lazy_ugettext as _
from sqlalchemy.types import Unicode, UnicodeText, Integer
from sqlalchemy.types import DateTime, SmallInteger, TIMESTAMP, BigInteger

from baruwa.lib.custom_ddl import utcnow
from baruwa.model.meta import Base


CATEGORY_MAP = {1: 'Read',
                2: 'Update',
                3: 'Create',
                4: 'Delete',
                5: 'Export',
                6: 'Auth'}


class MailQueueItem(Base):
    "Mail queue items"
    __tablename__ = 'mailq'

    id = Column(Integer, primary_key=True)
    messageid = Column(Unicode(255))
    timestamp = Column(DateTime(timezone=True), server_default=utcnow())
    from_address = Column(Unicode(255), index=True)
    to_address = Column(Unicode(255), index=True)
    from_domain = Column(Unicode(255), index=True)
    to_domain = Column(Unicode(255), index=True)
    subject = Column(UnicodeText)
    hostname = Column(UnicodeText)
    size = Column(Integer)
    attempts = Column(Integer)
    lastattempt = Column(DateTime(timezone=True), server_default=utcnow())
    direction = Column(SmallInteger, default=1, index=True)
    reason = Column(UnicodeText)
    flag = Column(SmallInteger, default=0)

    __mapper_args__ = {'order_by':timestamp}

    def __init__(self, messageid):
        self.messageid = messageid


class AuditLog(Base):
    "Audit Log items"
    __tablename__ = 'auditlog'

    id = Column(BigInteger, primary_key=True)
    username = Column(Unicode(255))
    category = Column(SmallInteger, default=1, index=True)
    info = Column(UnicodeText)
    hostname = Column(UnicodeText)
    remoteip = Column(UnicodeText)
    timestamp = Column(TIMESTAMP(timezone=True),
                    server_default=utcnow())

    __mapper_args__ = {'order_by':timestamp}

    def __init__(self, username, category, info, hostname,
                remoteip, timestamp=None):
        "init"
        self.username = username
        self.category = category
        self.info = info
        self.hostname = hostname
        self.remoteip = remoteip
        if timestamp:
            self.timestamp = timestamp

    #@property
    def tojson(self):
        "JSON friendly format"
        return dict(username=self.username,
                    category=unicode(CATEGORY_MAP[self.category]),
                    info=self.info,
                    hostname=self.hostname,
                    remoteip=self.remoteip,
                    timestamp=str(self.timestamp.strftime('%Y-%m-%d %H:%M')))
