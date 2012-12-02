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
"""Messages SQLAlchemy models
"""

#from datetime import datetime

from pylons.i18n.translation import _
from webhelpers.html import escape
from webhelpers.number import format_byte_size
from webhelpers.text import wrap_paragraphs, truncate
from sqlalchemy import Column
#from sqlalchemy.sql.expression import text
from sqlalchemy.types import Integer, Unicode, String
from sqlalchemy.types import SmallInteger, Boolean, Date, BigInteger
from sqlalchemy.types import UnicodeText, Float, Time, TIMESTAMP

from baruwa.lib.custom_ddl import utcnow
from baruwa.model.meta import Base


class Message(Base):
    "Message model"
    __tablename__ = 'messages'

    id = Column(BigInteger, primary_key=True)
    messageid = Column(Unicode(255), index=True, unique=True)
    actions = Column(Unicode(128))
    clientip = Column(Unicode(128))
    date = Column(Date(timezone=True), index=True)
    from_address = Column(Unicode(255), index=True)
    from_domain = Column(Unicode(255), index=True)
    headers = Column(UnicodeText)
    hostname = Column(UnicodeText)
    highspam = Column(SmallInteger, default=0, index=True)
    rblspam = Column(SmallInteger, default=0)
    saspam = Column(SmallInteger, default=0)
    spam = Column(SmallInteger, default=0, index=True)
    nameinfected = Column(SmallInteger, default=0)
    otherinfected = Column(SmallInteger, default=0)
    isquarantined = Column(SmallInteger, default=0, index=True)
    isarchived = Column(SmallInteger, default=0, index=True)
    sascore = Column(Float, index=True)
    scaned = Column(SmallInteger, default=0, index=True)
    size = Column(Integer)
    blacklisted = Column(SmallInteger, default=0, index=True)
    spamreport = Column(UnicodeText)
    whitelisted = Column(SmallInteger, default=0, index=True)
    subject = Column(UnicodeText)
    time = Column(Time(timezone=True))
    timestamp = Column(TIMESTAMP(timezone=True),
                        server_default=utcnow(),
                        index=True)
    to_address = Column(Unicode(255), index=True)
    to_domain = Column(Unicode(255), index=True)
    virusinfected = Column(SmallInteger, default=0)
    ts = Column(TIMESTAMP(timezone=True),
                server_default=utcnow())

    def __init__(self, messageid):
        "init"
        self.messageid = messageid

    __mapper_args__ = {'order_by':timestamp}

    @property
    def tojson(self):
        "Serialize to json"
        return dict(
                    id=self.id,
                    messageid=self.messageid,
                    actions=self.actions,
                    clientip=self.clientip,
                    date=str(self.date),
                    from_address=self.from_address,
                    from_domain=self.from_domain,
                    headers=self.headers,
                    hostname=self.hostname,
                    highspam=self.highspam,
                    rblspam=self.rblspam,
                    saspam=self.saspam,
                    spam=self.spam,
                    nameinfected=self.nameinfected,
                    otherinfected=self.otherinfected,
                    isquarantined=self.isquarantined,
                    isarchived=self.isarchived,
                    sascore=self.sascore,
                    scaned=self.scaned,
                    size=self.size,
                    blacklisted=self.blacklisted,
                    spamreport=self.spamreport,
                    whitelisted=self.whitelisted,
                    subject=self.subject,
                    time=str(self.time),
                    timestamp=str(self.timestamp),
                    to_address=self.to_address,
                    to_domain=self.to_domain,
                    virusinfected=self.virusinfected,
                )

    @property
    def json(self):
        "recent messages json"
        value = 'white'
        if (self.spam and not self.highspam and not self.blacklisted
            and not self.nameinfected and not self.otherinfected 
            and not self.virusinfected):
            value = 'spam'
        if self.highspam and (not self.blacklisted):
            value = 'highspam'
        if self.whitelisted:
            value = 'whitelisted'
        if self.blacklisted:
            value = 'blacklisted'
        if self.nameinfected or self.virusinfected or self.otherinfected:
            value = 'infected'
        if not self.scaned:
            value = 'gray'
        if (self.spam and (not self.blacklisted) 
            and (not self.virusinfected) 
            and (not self.nameinfected) 
            and (not self.otherinfected)):
            status = _('Spam')
        if self.blacklisted:
            status = _('BS')
        if (self.virusinfected or 
               self.nameinfected or 
               self.otherinfected):
            status = _('Infected')
        if ((not self.spam) and (not self.virusinfected) 
               and (not self.nameinfected) 
               and (not self.otherinfected) 
               and (not self.whitelisted)):
            status = _('Clean')
        if self.whitelisted:
            status = _('AS')
        if not self.scaned:
            status = _('NS')
        return dict(
                    id=self.id,
                    timestamp=self.timestamp.strftime('%A, %d %b %Y %H:%M:%S %Z'),
                    sascore=self.sascore,
                    size=format_byte_size(self.size),
                    subject=escape(truncate((self.subject and self.subject.strip()) or '---', 50)),
                    from_address=escape(wrap_paragraphs(self.from_address, 32)),
                    to_address=escape(wrap_paragraphs(self.to_address or '---', 32)),
                    style=value,
                    status=status,
                )


class Archive(Base):
    "Archive"
    __tablename__ = 'archive'

    id = Column(BigInteger, primary_key=True)
    messageid = Column(Unicode(255), index=True)
    actions = Column(Unicode(255))
    clientip = Column(Unicode(128))
    date = Column(Date(timezone=True), index=True)
    from_address = Column(Unicode(255), index=True)
    from_domain = Column(Unicode(255), index=True)
    headers = Column(UnicodeText)
    hostname = Column(UnicodeText)
    highspam = Column(SmallInteger, default=0, index=True)
    rblspam = Column(SmallInteger, default=0)
    saspam = Column(SmallInteger, default=0)
    spam = Column(SmallInteger, default=0, index=True)
    nameinfected = Column(SmallInteger, default=0)
    otherinfected = Column(SmallInteger, default=0)
    isquarantined = Column(SmallInteger, default=0, index=True)
    isarchived = Column(SmallInteger, default=0, index=True)
    sascore = Column(Float)
    scaned = Column(SmallInteger, default=0, index=True)
    size = Column(Integer)
    blacklisted = Column(SmallInteger, default=0, index=True)
    spamreport = Column(UnicodeText)
    whitelisted = Column(SmallInteger, default=0, index=True)
    subject = Column(UnicodeText)
    time = Column(Time(timezone=True))
    timestamp = Column(TIMESTAMP(timezone=True),
                        server_default=utcnow(),
                        index=True)
    to_address = Column(Unicode(255), index=True)
    to_domain = Column(Unicode(255), index=True)
    virusinfected = Column(SmallInteger, default=0)
    ts = Column(TIMESTAMP(timezone=True), server_default=utcnow())

    def __init__(self, messageid):
        "init"
        self.messageid = messageid

    __mapper_args__ = {'order_by':timestamp}


class SARule(Base):
    "Spamassassin rule"
    __tablename__ = 'sarules'

    id = Column(Unicode(255), primary_key=True)
    description = Column(UnicodeText)
    score = Column(Float, default=0)

    def __init__(self, ruleid, description):
        "init"
        self.id = ruleid
        self.description = description


class Release(Base):
    "quarantine release record"
    __tablename__ = 'releases'

    id = Column(BigInteger, primary_key=True)
    messageid = Column(BigInteger)
    uuid = Column(String(128), unique=True)
    timestamp = Column(TIMESTAMP(timezone=True),
                        server_default=utcnow())
    released = Column(Boolean(), default=False)

    __mapper_args__ = {'order_by':id}

    def __init__(self, messageid, uuid):
        "init"
        self.messageid = messageid
        self.uuid = uuid


class MessageStatus(Base):
    "Message delivery status records"
    __tablename__ = 'messagestatus'

    id = Column(BigInteger, primary_key=True)
    messageid = Column(Unicode(255))
    hostname = Column(UnicodeText)
    ipaddress = Column(Unicode(128))
    port = Column(Integer)
    confirmation = Column(Unicode(255))
    errorno = Column(Integer, server_default='0')
    errorstr = Column(UnicodeText, server_default=u'')
    timestamp = Column(TIMESTAMP(timezone=True),
                        server_default=utcnow())

    __mapper_args__ = {'order_by':timestamp}

    # def __init__(self, messageid, destination, status, info):
    #     "init"
    #     self.messageid = messageid
    #     self.destination = destination
    #     self.status = status
    #     self.info = info
