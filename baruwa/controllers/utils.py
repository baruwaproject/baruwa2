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
import logging
import gettext

from pylons import config, response
from pylons.i18n.translation import get_lang
from beaker.cache import cache_region, region_invalidate

from baruwa.lib.base import BaseController
from baruwa.lib.misc import quote_js

log = logging.getLogger(__name__)


LIBHEAD = """
/* gettext library */

var catalog = new Array();
"""

LIBFOOT = """

function gettext(msgid) {
  var value = catalog[msgid];
  if (typeof(value) == 'undefined') {
    return msgid;
  } else {
    return (typeof(value) == 'string') ? value : value[0];
  }
}

function ngettext(singular, plural, count) {
  value = catalog[singular];
  if (typeof(value) == 'undefined') {
    return (count == 1) ? singular : plural;
  } else {
    return value[pluralidx(count)];
  }
}

function gettext_noop(msgid) { return msgid; }

function pgettext(context, msgid) {
  var value = gettext(context + '\x04' + msgid);
  if (value.indexOf('\x04') != -1) {
    value = msgid;
  }
  return value;
}

function npgettext(context, singular, plural, count) {
  var value = ngettext(context + '\x04' + singular, context + '\x04' + plural, count);
  if (value.indexOf('\x04') != -1) {
    value = ngettext(singular, plural, count);
  }
  return value;
}
"""

SIMPLEPLURAL = """
function pluralidx(count) { return (count == 1) ? 0 : 1; }
"""

INTERPOLATE = r"""
function interpolate(fmt, obj, named) {
  if (named) {
    return fmt.replace(/%\(\w+\)s/g, function(match){return String(obj[match.slice(2,-2)])});
  } else {
    return fmt.replace(/%s/g, function(match){return String(obj.shift())});
  }
}
"""

PLURALIDX = r"""
function pluralidx(n) {
  var v=%s;
  if (typeof(v) == 'boolean') {
    return v ? 1 : 0;
  } else {
    return v;
  }
}
"""


class UtilsController(BaseController):

    def js_localization(self):
        "return localized strings from cache or compute"
        locale = get_lang()[0]
        if self.langchange:
            region_invalidate(self._js_localization, None, 'baruwajs', locale)
        return self._js_localization(locale)

    @cache_region('long_term', 'baruwajs')
    def _js_localization(self, locale):
        "Return dict of localized strings for JS"
        locale_t = {}
        path = os.path.join(config['pylons.paths']['root'], 'i18n')
        try:
            catalog = gettext.translation('baruwajs', path, [locale])
        except IOError:
            catalog = None
        if catalog is not None:
            locale_t.update(catalog._catalog)
        src = [LIBHEAD]
        plural = None
        if '' in locale_t:
            for l in locale_t[''].split('\n'):
                if l.startswith('Plural-Forms:'):
                    plural = l.split(':', 1)[1].strip()
        if plural is not None:
            plural = [el.strip() for el in plural.split(';')
            if el.strip().startswith('plural=')][0].split('=', 1)[1]
            src.append(PLURALIDX % plural)
        else:
            src.append(SIMPLEPLURAL)
        csrc = []
        pdict = {}
        for k, v in locale_t.items():
            if k == '':
                continue
            if isinstance(k, basestring):
                csrc.append("catalog['%s'] = '%s';\n" % (quote_js(k),
                quote_js(v)))
            elif isinstance(k, tuple):
                if k[0] not in pdict:
                    pdict[k[0]] = k[1]
                else:
                    pdict[k[0]] = max(k[1], pdict[k[0]])
                csrc.append("catalog['%s'][%d] = '%s';\n" % (quote_js(k[0]),
                k[1], quote_js(v)))
            else:
                raise TypeError(k)
        csrc.sort()
        for k, v in pdict.items():
            src.append("catalog['%s'] = [%s];\n" % (quote_js(k),
            ','.join(["''"] * (v + 1))))
        src.extend(csrc)
        src.append(LIBFOOT)
        src.append(INTERPOLATE)
        src = ''.join(src)
        response.headers['Pragma'] = 'public'
        response.headers['Cache-Control'] = 'max-age=0'
        response.headers['Content-Type'] = 'text/javascript;charset=utf-8'
        return src
