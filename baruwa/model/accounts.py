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
"""Accounts SQLAlchemy models
"""

import bcrypt
# import hashlib

from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.orm import relationship, backref
from sqlalchemy.types import DateTime, Boolean, Float
from sqlalchemy.schema import PrimaryKeyConstraint, UniqueConstraint
from sqlalchemy.types import UnicodeText, TIMESTAMP
from sqlalchemy.types import Integer, Unicode, SmallInteger, BigInteger

from baruwa.model.meta import Base
from baruwa.lib.custom_ddl import utcnow


domain_owners = Table(
    'domain_owners', Base.metadata,
    Column('organization_id', Integer, ForeignKey('organizations.id')),
    Column('domain_id', Integer, ForeignKey('maildomains.id')),
    PrimaryKeyConstraint('organization_id', 'domain_id'),
)

domain_users = Table(
    'domain_users', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('domain_id', Integer, ForeignKey('maildomains.id')),
    PrimaryKeyConstraint('user_id', 'domain_id'),
)

organizations_admins = Table(
    'organizations_admins', Base.metadata,
    Column('organization_id', Integer, ForeignKey('organizations.id')),
    Column('user_id', Integer, ForeignKey('users.id')),
    PrimaryKeyConstraint('organization_id', 'user_id'),
)


class User(Base):
    """User Model"""
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True)
    username = Column(Unicode(255), unique=True)
    firstname = Column(Unicode(255))
    lastname = Column(Unicode(255))
    __password = Column('password', Unicode(255))
    email = Column(Unicode(255), unique=True)
    timezone = Column(Unicode(255), default=u'UTC')
    account_type = Column(SmallInteger(), default=3, index=True)
    created_on = Column(DateTime(timezone=True), server_default=utcnow())
    last_login = Column(DateTime(timezone=True), server_default=utcnow())
    active = Column(Boolean(), default=True)
    local = Column(Boolean(), default=False)
    send_report = Column(Boolean(), default=True)
    spam_checks = Column(Boolean(), default=True)
    low_score = Column(Float(), default=0.0)
    high_score = Column(Float(), default=0.0)
    lists = relationship('List', backref='user',
                        cascade='delete, delete-orphan')
    addresses = relationship('Address', backref='user',
                        cascade='delete, delete-orphan')
    domains = relationship('Domain', secondary=domain_users,
                        backref='users')
    organizations = relationship('Group', secondary=organizations_admins,
                                backref='admins')
    signatures = relationship('UserSignature', backref='user',
                        cascade='delete, delete-orphan')

    __mapper_args__ = {'order_by':id}

    def __init__(self, username, email):
        "init"
        self.username = username
        self.email = email

    def set_password(self, password):
        "sets the password to a hash"
        self.__password = bcrypt.hashpw(password, bcrypt.gensalt())

    def validate_password(self, password):
        "validate the password"
        if isinstance(password, unicode):
            password = password.encode('utf-8')
        return (self.active and
                self.local and
                (bcrypt.hashpw(password, self.__password) == self.__password))

    def to_csv(self):
        "return only csv attributes"
        csvdict = {}
        for field in ['username',
                    'email',
                    'account_type',
                    'active',
                    'firstname',
                    'lastname',
                    'send_report',
                    'spam_checks',
                    'low_score',
                    'high_score',
                    'timezone']:
            try:
                csvdict[field] = str(getattr(self, field))
            except UnicodeEncodeError:
                value = getattr(self, field)
                csvdict[field] = value.encode('utf-8')
        return csvdict

    def tojson(self):
        "Return JSON"
        if self.account_type == 1:
            user_icon = 'imgs/user_admin.png'
        elif self.account_type == 2:
            user_icon = 'imgs/user_dadmin.png'
        else:
            user_icon = 'imgs/user.png'
        return dict(
                        id=self.id,
                        username=self.username,
                        fullname=self.firstname + ' ' + self.lastname,
                        email=self.email,
                        userimg=user_icon,
                        statusimg='imgs/tick.png' if self.active else 'imgs/minus.png'
                    )

    @property
    def is_superadmin(self):
        "Check if user is super admin"
        return self.account_type == 1

    @property
    def is_admin(self):
        "Check if user is an admin"
        return self.account_type == 1 or self.account_type == 2

    @property
    def is_domain_admin(self):
        "Check if user is a domain admin"
        return self.account_type == 2

    @property
    def is_peleb(self):
        "Check if user is just an ordinary joe"
        return self.account_type == 3 and self.active


class Group(Base):
    """Group model"""
    __tablename__ = 'organizations'

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255), index=True, unique=True)
    domains = relationship('Domain', secondary=domain_owners,
                            backref='organizations')

    __mapper_args__ = {'order_by':id}

    # def __init__(self, name):
    #     "init"
    #     self.name = name


class Address(Base):
    "Alias addresses"
    __tablename__ = "addresses"
    __table_args__ = (UniqueConstraint('address', 'user_id'), {})

    id = Column(BigInteger, primary_key=True)
    address = Column(Unicode(255), index=True)
    enabled = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey('users.id'))

    __mapper_args__ = {'order_by':id}

    def __init__(self, address):
        "init"
        self.address = address

    def to_csv(self):
        "Return CSV"
        # values = [self.address, self.enabled]
        #         return [str(value) for value in values]
        return dict(address=self.address,
                    enabled='True' if self.enabled else 'False')


class Relay(Base):
    "Relay settings"
    __tablename__ = 'relaysettings'

    id = Column(Integer, primary_key=True)
    address = Column(Unicode(255), index=True)
    username = Column(Unicode(255))
    __password = Column('password', Unicode(255))
    enabled = Column(Boolean, default=True)
    org_id = Column(Integer, ForeignKey('organizations.id'))
    org = relationship('Group', backref=backref('relaysettings', order_by=id))

    __mapper_args__ = {'order_by':id}

    def set_password(self, password):
        "sets the password to a hash"
        self.__password = bcrypt.hashpw(password, bcrypt.gensalt())

    # def _hash_password(self, raw_pass):
    #     "return hashed password"
    #     return bcrypt.hashpw(raw_pass, bcrypt.gensalt())


class ResetToken(Base):
    "Password reset token"
    __tablename__ = 'passwdtokens'

    id = Column(Integer, primary_key=True)
    token = Column(UnicodeText, unique=True)
    timestamp = Column(TIMESTAMP(timezone=True), server_default=utcnow())
    used = Column(Boolean(), default=False)
    user_id = Column(Integer, ForeignKey('users.id'))

    def __init__(self, token, user_id):
        "Accept token arg"
        self.token = token
        self.user_id = user_id
