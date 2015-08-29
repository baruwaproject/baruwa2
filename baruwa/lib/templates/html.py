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
"HTML processing template functions"
from pylons import url
from webhelpers.html import literal
from pylons.i18n.translation import ugettext
from webhelpers.html.tags import link_to
from lxml.html import tostring, iterlinks

from baruwa.lib.helpers import flash
from baruwa.lib.mail import local_fromstring
from baruwa.lib.templates.helpers import media_url


def image_fixups(content, msgid, archive, richformat, allowimgs):
    "Replace the CID links stored messages"
    html = local_fromstring(content)
    for element, attribute, link, _ in iterlinks(html):
        if not link.startswith('cid:'):
            if not allowimgs and attribute == 'src':
                element.attrib['src'] = '%simgs/blocked.gif' % media_url()
                element.attrib['title'] = link
                if richformat:
                    if archive:
                        displayurl = url('message-preview-archived-with-imgs',
                                        msgid=msgid)
                    else:
                        displayurl = url('message-preview-with-imgs',
                                        msgid=msgid)
                    flash(ugettext('This message contains external'
                        ' images, which have been blocked. ') +
                        literal(link_to(ugettext('Display images'),
                                displayurl)))
        else:
            imgname = link.replace('cid:', '')
            if archive:
                imgurl = url('messages-preview-archived-img',
                            img=imgname.replace('/', '__xoxo__'),
                            msgid=msgid)
            else:
                imgurl = url('messages-preview-img',
                            img=imgname.replace('/', '__xoxo__'),
                            msgid=msgid)
            element.attrib['src'] = imgurl            
    return tostring(html)


def img_fixups(content, queueid, allowimgs, richformat):
    "Replace the CID links in Queued messages"
    html = local_fromstring(content)
    for element, attribute, link, _ in iterlinks(html):
        if not link.startswith('cid:'):
            if not allowimgs and attribute == 'src':
                element.attrib['src'] = '%simgs/blocked.gif' % media_url()
                element.attrib['title'] = link
                if richformat:
                    flash(ugettext('This message contains external '
                    'images, which have been blocked. ') +
                    literal(link_to(ugettext('Display images'),
                    url('queue-preview-with-imgs', queueid=queueid))))
        else:
            imgname = link.replace('cid:', '')
            element.attrib['src'] = url('queue-preview-img',
                                    imgid=imgname.replace('/', '__xoxo__'),
                                    queueid=queueid)
    return tostring(html)
