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
"Lists models"

from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Unicode, Integer, BigInteger
from sqlalchemy.schema import UniqueConstraint

from baruwa.model.meta import Base


class List(Base):
    "List object"
    __tablename__ = 'lists'
    __table_args__ = (UniqueConstraint('from_address', 'to_address'), {})

    id = Column(BigInteger, primary_key=True)
    list_type = Column(Integer, default=1)
    from_address = Column(Unicode(255), index=True)
    to_address = Column(Unicode(255), default=u'any', index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    from_addr_type = Column(Integer)

    __mapper_args__ = {'order_by':id}

    def tojson(self):
        "Return json"
        return dict(
                        id=self.id,
                        #list_type=self.list_type,
                        from_address=self.from_address,
                        to_address=self.to_address,
                    )