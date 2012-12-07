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
"""The application's model objects"""

from sqlalchemy import event
from sqlalchemy.sql import text

from baruwa.model.meta import Session, Base
from baruwa.model.lists import List
from baruwa.model.reports import SavedFilter
from baruwa.model.accounts import User, Address, Group
from baruwa.model.status import MailQueueItem, AuditLog
from baruwa.model.settings import ConfigSettings, Server, UserSigImg
from baruwa.model.settings import DomSignature, UserSignature, DomSigImg
from baruwa.model.settings import IndexerCounter, IndexerKillList, DKIMKeys
from baruwa.model.auth import LDAPSettings, RadiusSettings
from baruwa.model.domains import Domain, DeliveryServer
from baruwa.model.domains import AuthServer, DomainAlias
from baruwa.model.messages import Message, Archive, SARule, Release

from baruwa.lib.regex import CLEANRE
from baruwa.lib.outputformats import SignatureCleaner

try:
    from baruwa.model.invite import InviteToken
except ImportError:
    pass


def sanitize_signature(mapper, connection, target):
    "clean up signature before storing to DB"
    uncleantags = ['html', 'head', 'link', 'body', 'base']
    if target.signature_type == '1' or target.signature_type == 1:
        target.signature_content = CLEANRE.sub('', target.signature_content)
    else:
        cleaner = SignatureCleaner(remove_tags=uncleantags,
                                    safe_attrs_only=False)
        target.signature_content = cleaner.clean_html(target.signature_content)


def delete_totals(mapper, connection, target):
    "Delete totals for the domain"
    query1 = text("DELETE FROM srcmsgtotals WHERE id='dom:'")
    query2 = text("DELETE FROM dstmsgtotals WHERE id='dom:'")
    Session.execute(query1, params=dict(dom=target.name))
    Session.execute(query2, params=dict(dom=target.name))

event.listen(UserSignature, 'before_insert', sanitize_signature)
event.listen(DomSignature, 'before_insert', sanitize_signature)
event.listen(UserSignature, 'before_update', sanitize_signature)
event.listen(DomSignature, 'before_update', sanitize_signature)
event.listen(Domain, 'after_delete', delete_totals)
event.listen(DomainAlias, 'after_delete', delete_totals)


def init_model(engine):
    """Call me before using any of the tables or classes in the model"""
    Session.configure(bind=engine)
