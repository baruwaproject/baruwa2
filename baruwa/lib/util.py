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
"API Utility functions"
import json
import logging

from httplib import responses

from webob import Response
from pylons import request
from webob.exc import status_map


log = logging.getLogger(__name__)


def api_abort(status_code=None, detail="", headers=None, comment=None):
    """Abort an API request"""
    exc_class = status_map[status_code]

    class APIException(exc_class):
        "Overide the WebOb exception class"
        def __call__(self, environ, start_response):
            "Return the HTTP response"
            self.content_type = 'text/javascript; charset=utf-8'
            self.body = json.dumps(self.detail)
            return Response.__call__(self, environ, start_response)

    if not detail.strip():
        try:
            detail = responses[int(status_code)]
        except KeyError:
            detail = 'Unknown Error'
    detail = dict(error=detail, code=status_code)
    exc = APIException(detail=detail, headers=headers, comment=comment)
    log.debug("Aborting API request with status: %s,detail: %r, headers: %r,"
              " comment: %r", status_code, detail, headers, comment)
    request.environ['pylons.status_code_redirect'] = True
    raise exc.exception
