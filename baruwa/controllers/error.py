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
import cgi

from pylons import request, tmpl_context as c
# from paste.urlparser import PkgResourcesParser
from webhelpers.html.builder import literal
from pylons.i18n.translation import _

from baruwa.lib.base import BaseController, render


class ErrorController(BaseController):
    """Generates error documents as and when they are required.

    The ErrorDocuments middleware forwards to ErrorController when error
    related status codes are returned from the application.

    This behaviour can be altered by changing the parameters to the
    ErrorDocuments middleware in your config/middleware.py file.

    """
    def document(self):
        """Render the error document"""
        resp = request.environ.get('pylons.original_response')
        code = cgi.escape(request.GET.get('code', ''))
        content = cgi.escape(request.GET.get('message', ''))
        if resp:
            content = literal(resp.status)
            code = code or cgi.escape(str(resp.status_int))
        if not code:
            raise Exception(_('No status code found'))
        c.code = code
        c.message = content
        return render('/general/error.html')

    # def img(self, id):
    #     """Serve Pylons' stock images"""
    #     return self._serve_file('/'.join(['media/img', id]))
    # 
    # def style(self, id):
    #     """Serve Pylons' stock stylesheets"""
    #     return self._serve_file('/'.join(['media/style', id]))
    # 
    # def _serve_file(self, path):
    #     """Call Paste's FileApp (a WSGI application) to serve the file
    #     at the specified path
    #     """
    #     request = self._py_object.request
    #     request.environ['PATH_INFO'] = '/%s' % path
    #     return PkgResourcesParser('pylons', 'pylons')(request.environ, self.start_response)
