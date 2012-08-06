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

"reports models"
from sqlalchemy import Column, ForeignKey, select, union_all
from sqlalchemy.orm import relationship, backref
from sqlalchemy.types import Unicode, Integer, BigInteger
from sqlalchemy.types import SmallInteger, Float, UnicodeText
from sqlalchemy.sql.expression import Alias

from baruwa.model.meta import Base


class SavedFilter(Base):
    "Saved Filters"
    __tablename__ = 'filters'

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255), unique=True)
    field = Column(Unicode(30))
    option = Column(SmallInteger)
    value = Column(Unicode(255))
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User', backref=backref('filters', order_by=id))

    __mapper_args__ = {'order_by':id}

    def __init__(self, name, field, option, user):
        "init"
        self.name = name
        self.field = field
        self.option = option
        self.user = user


class SrcMessageTotals(Base):
    "From domain totals"
    __tablename__ = 'srcmsgtotals'

    id = Column(UnicodeText, primary_key=True)
    total = Column(BigInteger, index=True)
    volume = Column(BigInteger, index=True)
    spam = Column(BigInteger)
    virii = Column(BigInteger)
    infected = Column(BigInteger)
    otherinfected = Column(BigInteger)
    runtotal = Column(Float, index=True)


class DstMessageTotals(Base):
    "To domain totals"
    __tablename__ = 'dstmsgtotals'

    id = Column(UnicodeText, primary_key=True)
    total = Column(BigInteger, index=True)
    volume = Column(BigInteger, index=True)
    spam = Column(BigInteger)
    virii = Column(BigInteger)
    infected = Column(BigInteger)
    otherinfected = Column(BigInteger)
    runtotal = Column(Float, index=True)


dst_table = DstMessageTotals.__table__
src_table = SrcMessageTotals.__table__
msg_table = Alias(union_all(select([src_table]), select([dst_table])), 'a')


class MessageTotals(Base):
    "Message totals"
    __table__ = msg_table
