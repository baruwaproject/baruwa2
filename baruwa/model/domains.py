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
"""Domains SQLAlchemy models
"""

from sqlalchemy.types import BigInteger
from sqlalchemy import Column, ForeignKey
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.orm import relationship, backref
from sqlalchemy.types import Integer, Unicode, SmallInteger, Boolean, Float

from baruwa.model.meta import Base


class Domain(Base):
    "Domains"
    __tablename__ = 'maildomains'

    id = Column(BigInteger, primary_key=True)
    name = Column(Unicode(255), unique=True)
    site_url = Column(Unicode(255))
    status = Column(Boolean, default=True)
    delivery_mode = Column(SmallInteger, default=1)
    spam_actions = Column(SmallInteger, default=3)
    highspam_actions = Column(SmallInteger, default=3)
    smtp_callout = Column(Boolean, default=False)
    ldap_callout = Column(Boolean, default=False)
    spam_checks = Column(Boolean, default=True)
    virus_checks = Column(Boolean, default=True)
    low_score = Column(Float(), default=0)
    high_score = Column(Float(), default=0)
    message_size = Column(Unicode(12), default=u'0')
    language = Column(Unicode(2), default=u'en')
    timezone = Column(Unicode(255), default=u'UTC')
    report_every = Column(SmallInteger, default=3)
    servers = relationship('DeliveryServer',
                            backref=backref('domains', order_by=id),
                            cascade='delete, delete-orphan')
    authservers = relationship('AuthServer',
                            backref=backref('domains', order_by=id),
                            cascade='delete, delete-orphan')
    aliases = relationship('DomainAlias',
                            backref=backref('domain', order_by=id),
                            cascade='delete, delete-orphan')
    signatures = relationship('DomSignature',
                            backref=backref('domain', order_by=id),
                            cascade='delete, delete-orphan')
    dkimkeys = relationship('DKIMKeys',
                            backref=backref('domain', order_by=id),
                            cascade='delete, delete-orphan')

    __mapper_args__ = {'order_by':id}

    # def __init__(self, name, site_url):
    #     "init"
    #     self.name = name
    #     self.site_url = site_url

    def to_csv(self):
        "Return CSV"
        csvdict = {}
        for field in ['name', 'site_url', 'status', 'smtp_callout',
                    'ldap_callout', 'virus_checks', 'spam_checks',
                    'spam_actions', 'highspam_actions', 'low_score',
                    'high_score', 'message_size', 'delivery_mode',
                    'language', 'report_every', 'timezone']:
            try:
                csvdict[field] = str(getattr(self, field))
            except UnicodeEncodeError:
                value = getattr(self, field)
                csvdict[field] = value.encode('utf-8')
        return csvdict

    def tojson(self):
        "Return JSON"
        jsondict = dict(
                        id=self.id,
                        name=self.name,
                        status=self.status,
                        statusimg='imgs/tick.png' if self.status else 'imgs/minus.png'
                        )
        jsondict['organizations'] = [{'name': org.name, 'id': org.id}
                                    for org in self.organizations]
        return jsondict


class DomainAlias(Base):
    "Domain alias"
    __tablename__ = 'domainalias'

    id = Column(BigInteger, primary_key=True)
    name = Column(Unicode(255), unique=True)
    status = Column(Boolean, default=True)
    domain_id = Column(Integer, ForeignKey('maildomains.id'))

    __mapper_args__ = {'order_by':id}

    def to_csv(self):
        "Return CSV"
        return dict(
            da_name=self.name,
            da_status=str(self.status)
        )


class DeliveryServer(Base):
    "Destination server"
    __tablename__ = 'destinations'
    __table_args__ = (UniqueConstraint('address', 'port', 'domain_id'), {})

    id = Column(Integer, primary_key=True)
    address = Column(Unicode(255))
    protocol = Column(SmallInteger, default=1)
    port = Column(Integer, default=25)
    enabled = Column(Boolean, default=True)
    domain_id = Column(Integer, ForeignKey('maildomains.id'))

    __mapper_args__ = {'order_by':id}

    def to_csv(self):
        "Return CSV"
        return dict(
            ds_address=self.address,
            ds_protocol=str(self.protocol),
            ds_port=str(self.port),
            ds_enabled=str(self.enabled)
        )

    # def __init__(self, address, protocol):
    #     "init"
    #     self.address = address
    #     self.protocol = protocol


class AuthServer(Base):
    "Authentication server"
    __tablename__ = 'authservers'
    __table_args__ = (UniqueConstraint('address', 'protocol', 'domain_id'),
                    {})

    id = Column(Integer, primary_key=True)
    address = Column(Unicode(255))
    protocol = Column(SmallInteger)
    port = Column(Integer)
    enabled = Column(Boolean, default=True)
    split_address = Column(Boolean, default=False)
    user_map_template = Column(Unicode(255))
    domain_id = Column(Integer, ForeignKey('maildomains.id'))
    ldapsettings = relationship('LDAPSettings',
                                backref=backref('authservers', order_by=id),
                                cascade='delete, delete-orphan')
    radiussettings = relationship('RadiusSettings',
                                backref=backref('authservers', order_by=id),
                                cascade='delete, delete-orphan')

    __mapper_args__ = {'order_by':id}

    def to_csv(self):
        "Return CSV"
        return dict(
            as_address=self.address,
            as_protocol=str(self.protocol),
            as_port=str(self.port),
            as_enabled=str(self.enabled),
            as_split_address=str(self.split_address),
            as_user_map_template=self.user_map_template,
        )

    # def __init__(self, address, protocol):
    #     "init"
    #     self.address = address
    #     self.protocol = protocol