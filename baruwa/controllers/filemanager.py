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

import os
import json
import imghdr
import base64
import logging

import magic

from pylons import request, response, session, config, tmpl_context as c, url
from pylons.controllers.util import abort
from pylons.i18n.translation import _
from repoze.what.predicates import not_anonymous
from repoze.what.plugins.pylonshq import ControllerProtector

from baruwa.lib.base import BaseController
from baruwa.model.meta import Session
from baruwa.model.settings import DomSigImg, UserSigImg
from baruwa.forms.misc import Fmgr
from baruwa.tasks.settings import delete_sig
from baruwa.lib.auth.predicates import check_domain_ownership, check_dom_access

log = logging.getLogger(__name__)


@ControllerProtector(not_anonymous())
class FilemanagerController(BaseController):
    def __before__(self):
        "set context"
        BaseController.__before__(self)
        if self.identity:
            c.user = self.identity['user']
        else:
            c.user = None

    def index(self, domainid=None, userid=None):
        "Index"
        action = request.GET.get('action', None)
        if not action:
            body = dict(success=False,
                        error=_("Action not supported"),
                        errorno=255)
            response.headers['Content-Type'] = 'application/json'
            return json.dumps(body)

        kw = {}
        if domainid:
            requesturl = url('fm-domains', domainid=domainid)
            model = DomSigImg
            domain = self._get_domain(domainid)
            if not domain:
                abort(404)
            if (not c.user.is_superadmin and not
                check_domain_ownership(c.user.id, domainid)):
                abort(404)
            ownerattr = 'domain_id'
            kw[ownerattr] = domainid
            ownerid = domainid
        else:
            requesturl = url('fm-users', userid=userid)
            model = UserSigImg
            user = self._get_user(userid)
            if not user:
                abort(404)
            if c.user.is_peleb and c.user.id != user.id:
                abort(403)
            if not c.user.is_superadmin and c.user.id != user.id:
                orgs = [org.id for org in c.user.organizations]
                doms = [dom.id for dom in user.domains]
                if not check_dom_access(orgs, doms):
                    abort(403)
            ownerattr = 'user_id'
            kw[ownerattr] = userid
            ownerid = userid
        if action == 'auth':
            body = dict(success=True,
                        data=dict(
                            move=dict(enabled=False,
                                    handler=requesturl),
                            rename=dict(enabled=False,
                                    handler=requesturl),
                            remove=dict(enabled=True,
                                    handler=requesturl),
                            mkdir=dict(enabled=False,
                                    handler=requesturl),
                            upload=dict(enabled=True,
                                    handler=requesturl + '?action=upload',
                                    accept_ext=['gif', 'jpg', 'png']),
                            baseUrl='')
                        )
        elif action == 'list':
            imgq = Session.query(model).filter_by(**kw).all()
            imgs = {}
            def builddict(img):
                sigtype = 'domains' if domainid else 'users'
                format = img.name.split('.')[-1] or 'png'
                imgs[img.name] = url('fm-view-img',
                                    sigtype=sigtype,
                                    imgid=img.id,
                                    format=format)
            [builddict(img) for img in imgq]
            body = dict(success=True,
                        data=dict(
                            directories={},
                            files=imgs)
                        )
        elif action == 'upload':
            form = Fmgr(request.POST, csrf_context=session)
            if request.POST and form.validate():
                try:
                    count = Session.query(model).filter_by(**kw).count()
                    if count > 0:
                        raise ValueError(_('Only one image is permitted per signature'))
                    imgdata = request.POST['handle']
                    mime = magic.Magic(mime=True)
                    content_type = mime.from_buffer(imgdata.file.read(1024))
                    imgdata.file.seek(0)
                    chunk = imgdata.file.read()
                    ext = imghdr.what('./xxx', chunk)
                    if not ext in ['gif', 'jpg', 'png', 'jpeg']:
                        raise ValueError(_('The uploaded file is not acceptable'))
                    name = form.newName.data or 'sigimage.%s' % ext
                    name = os.path.basename(name)
                    dbimg = model()
                    dbimg.name = name
                    dbimg.image = base64.encodestring(chunk)
                    dbimg.content_type = content_type
                    setattr(dbimg, ownerattr, ownerid)
                    imgdata.file.close()
                    Session.add(dbimg)
                    Session.commit()
                    respond = _('File has been uploaded')
                except ValueError, msg:
                    if 'imgdata' in locals() and hasattr(imgdata, 'file'):
                        imgdata.file.close()
                    respond = msg
            else:
                respond = _('Invalid upload request')
            return respond
        elif action == 'remove':
            fname = request.GET.get('file', None)
            imgs = Session.query(model).filter(model.name == fname).all()
            basedir = config.get('ms.signatures.base', '/etc/MailScanner/signatures')
            files = []
            for img in imgs:
                if userid:
                    imgfile = os.path.join(basedir, 'users', user.username,
                                            img.name)
                else:
                    imgfile = os.path.join(basedir, 'domains', domain.name,
                                            img.name)
                files.append(imgfile)
                Session.delete(img)
            Session.commit()
            respond = _('The file has been deleted')
            body = dict(success=True, data=respond)
            delete_sig.apply_async(args=[files])
        else:
            body = dict(success=False,
                        error=_("Action not supported"),
                        errorno=255)
        response.headers['Content-Type'] = 'application/json'
        return json.dumps(body)

    def view_img(self, imgid, sigtype):
        "Display a signature image"
        if sigtype == 'domains':
            model = DomSigImg
        else:
            model = UserSigImg

        img = Session.query(model).get(imgid)
        if not img:
            abort(404)

        response.headers['Content-Type'] = img.content_type
        return base64.decodestring(img.image)
