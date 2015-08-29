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
"Error controller"
import cgi

from pylons import tmpl_context as c
from pylons import request, response
from pylons.i18n.translation import _
from webhelpers.html.builder import literal

from baruwa.lib.base import BaseController


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
        if request.environ.get('REQUEST_URI', '').startswith('/api'):
            response.headers['Content-Type'] = resp.headers['Content-Type']
            return resp.body or literal(resp.status)
        if resp:
            content = literal(resp.status)
            code = code or cgi.escape(str(resp.status_int))
        if not code:
            raise Exception(_('No status code found'))
        c.code = code
        c.message = content
        return self.render('/general/error.html')
