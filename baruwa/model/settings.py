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

"settings models"
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.types import Unicode, Integer, Boolean, UnicodeText
from sqlalchemy.types import BigInteger, TIMESTAMP

from baruwa.lib.custom_ddl import utcnow
from baruwa.model.meta import Base


class ConfigSettings(Base):
    "Configuration settings"
    __tablename__ = 'configurations'
    __table_args__ = (UniqueConstraint('server_id', 'internal'), {})

    id = Column(Integer, primary_key=True)
    internal = Column(Unicode(255))
    external = Column(Unicode(255))
    value = Column(Unicode(255))
    section = Column(Integer)
    server_id = Column(Integer, ForeignKey('servers.id'))

    def __init__(self, internal, external, section):
        "Init"
        self.internal = internal
        self.external = external
        self.section = section


class Server(Base):
    "Server class"
    __tablename__ = 'servers'

    id = Column(Integer, primary_key=True)
    hostname = Column(Unicode(255), unique=True)
    enabled = Column(Boolean, default=True, index=True)
    configurations = relationship('ConfigSettings',
                        backref=backref('server', order_by=id),
                        cascade="all, delete, delete-orphan")

    __mapper_args__ = {'order_by': id}

    def __init__(self, hostname, enabled):
        "init"
        self.hostname = hostname
        self.enabled = enabled

    def tojson(self):
        "Return JSON"
        return dict(
                    id=self.id,
                    hostname=self.hostname,
                    statusimg='imgs/tick.png' if self.enabled else 'imgs/minus.png'
                    )


class DomSignature(Base):
    "Domain signature"
    __tablename__ = 'domain_signatures'
    __table_args__ = (UniqueConstraint('signature_type', 'domain_id'), {})

    id = Column(BigInteger, primary_key=True)
    signature_type = Column(Integer)
    signature_content = Column(UnicodeText)
    enabled = Column(Boolean, default=False)
    domain_id = Column(Integer, ForeignKey('maildomains.id'))
    image = relationship('DomSigImg',
                        backref=backref('signature', order_by=id),
                        cascade='all, delete, delete-orphan')
    __mapper_args__ = {'order_by': id}


class UserSignature(Base):
    "User signature"
    __tablename__ = 'user_signatures'
    __table_args__ = (UniqueConstraint('signature_type', 'user_id'), {})

    id = Column(BigInteger, primary_key=True)
    signature_type = Column(Integer)
    signature_content = Column(UnicodeText)
    enabled = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    image = relationship('UserSigImg',
                        backref=backref('signature', order_by=id),
                        cascade='all, delete, delete-orphan')

    __mapper_args__ = {'order_by': id}


class DomSigImg(Base):
    "Domain Signature image"
    __tablename__ = 'dom_sigimgs'
    __table_args__ = (UniqueConstraint('name', 'domain_id'), {})

    id = Column(BigInteger, primary_key=True)
    content_type =  Column(Unicode(100))
    name =  Column(Unicode(150))
    image = Column(UnicodeText)
    domain_id = Column(Integer, ForeignKey('maildomains.id'))
    sign_id = Column(Integer, ForeignKey('domain_signatures.id'))

    __mapper_args__ = {'order_by': id}


class UserSigImg(Base):
    "User Signature image"
    __tablename__ = 'user_sigimgs'
    __table_args__ = (UniqueConstraint('name', 'user_id'), {})

    id = Column(BigInteger, primary_key=True)
    content_type =  Column(Unicode(100))
    name =  Column(Unicode(150))
    image = Column(UnicodeText)
    user_id = Column(Integer, ForeignKey('users.id'))
    sign_id = Column(Integer, ForeignKey('user_signatures.id'))

    __mapper_args__ = {'order_by': id}


class IndexerCounter(Base):
    "Indexing counters"
    __tablename__ = 'indexer_counters'

    tablename = Column(Unicode(255), primary_key=True)
    maxts = Column(TIMESTAMP(timezone=True),
                    server_default=utcnow(),
                    index=True,
                    nullable=False)


class IndexerKillList(Base):
    "Keyword kill list"
    __tablename__ = 'indexer_killlist'

    id = Column(BigInteger, primary_key=True)
    ts = Column(TIMESTAMP(timezone=True),
                server_default=utcnow(),
                nullable=False,
                primary_key=True)
    tablename = Column(Unicode(255),
                nullable=False,
                primary_key=True)


class DKIMKeys(Base):
    "DKIM keys"
    __tablename__ = 'dkim_keys'

    id = Column(BigInteger, primary_key=True)
    pri_key = Column(UnicodeText)
    pub_key = Column(UnicodeText)
    enabled = Column(Boolean, default=False)
    domain_id = Column(Integer, ForeignKey('maildomains.id'))
