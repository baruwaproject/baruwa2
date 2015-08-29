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
"Authentication models"

from sqlalchemy import Column, ForeignKey
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.types import Integer, Unicode, Boolean, UnicodeText

from baruwa.model.meta import Base


class LDAPSettings(Base):
    "ldap settings"
    __tablename__ = 'ldapsettings'
    __table_args__ = (UniqueConstraint('auth_id', 'basedn'), {})

    id = Column(Integer, primary_key=True)
    basedn = Column(Unicode(255))
    nameattribute = Column(Unicode(255))
    emailattribute = Column(Unicode(255))
    binddn = Column(Unicode(255))
    bindpw = Column(Unicode(255))
    usetls = Column(Boolean, default=False)
    usesearch = Column(Boolean, default=False)
    searchfilter = Column(UnicodeText)
    search_scope = Column(Unicode(15))
    emailsearchfilter = Column(UnicodeText)
    emailsearch_scope = Column(Unicode(15))
    auth_id = Column(Integer, ForeignKey('authservers.id'))

    def from_form(self, form):
        """Set attributes from a form"""
        for field in form:
            if field.name == 'csrf_token':
                continue
            setattr(self, field.name, field.data)

    def apijson(self):
        """Return JSON for the API"""
        mdict = {}
        for attr in ['id', 'basedn', 'nameattribute', 'emailattribute',
                    'binddn', 'usetls', 'usesearch', 'searchfilter',
                    'search_scope', 'emailsearchfilter', 'emailsearch_scope']:
            mdict[attr] = getattr(self, attr)
        mdict['authserver'] = dict(id=self.authservers.id)
        return mdict


class RadiusSettings(Base):
    "radius settings"
    __tablename__ = 'radiussettings'

    id = Column(Integer, primary_key=True)
    secret = Column(Unicode(255))
    timeout = Column(Integer, default=0)
    auth_id = Column(Integer, ForeignKey('authservers.id'))

    def from_form(self, form):
        """Set attributes from a form"""
        for field in form:
            if field.name == 'csrf_token':
                continue
            setattr(self, field.name, field.data)

    def apijson(self):
        """Return JSON for the API"""
        mdict = {}
        for attr in ['id', 'timeout']:
            mdict[attr] = getattr(self, attr)
        mdict['authserver'] = dict(id=self.authservers.id)
        return mdict
