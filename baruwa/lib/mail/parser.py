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

"""Parse an email into a dictionary structure"""

import pyzmail

from base64 import encodestring
from email.utils import formataddr
from htmlentitydefs import entitydefs

# from lxml import etree
from lxml.html.clean import Cleaner
from lxml.etree import XMLSyntaxError
from lxml.html import defs, tostring

from baruwa.lib.crypto.hashing import md5
from baruwa.lib.mail.html import get_style
from baruwa.lib.mail import local_fromstring
from baruwa.lib.regex import HTMLTITLE_RE, HTMLENTITY_RE
from baruwa.lib.mail.css import sanitize_style, sanitize_css
from baruwa.lib.regex import CSS_COMMENT_RE, UNICODE_ENTITY_RE, XSS_RE


UNCLEANTAGS = ['html', 'title', 'head', 'link', 'a', 'body', 'base']
ENCODINGS = ('utf8', 'latin1', 'windows-1252', 'ascii')


def html_entity_decode_char(match):
    "Decode HTML entity"
    try:
        return unicode(entitydefs[match.group(1)], "Latin1")
    except KeyError:
        return match.group(0)


def html_entity_decode(string):
    "Decode HTML String"
    return HTMLENTITY_RE.sub(html_entity_decode_char, string)


def uni2char(match):
    "Convert unicode entity to char"
    try:
        return chr(int(match.groups()[0], 16))
    except ValueError:
        return u''


def clean_payload(payload):
    "Custom clean methods"
    if not payload:
        return ''
    payload = html_entity_decode(html_entity_decode(payload))
    try:
        payload = UNICODE_ENTITY_RE.sub(uni2char, payload)
    except UnicodeDecodeError:
        payload = u''
    payload = CSS_COMMENT_RE.sub('', payload)
    return payload


def set_body_class(payload, body_class):
    "Set the body class attribute to the top tag"
    if body_class:
        payload = local_fromstring(payload)
        payload.attrib['class'] = body_class
        payload = tostring(payload)
    return payload


def get_body_style(payload, target='#email-html-part'):
    "Get the style attribute of the body tag"
    try:
        html = local_fromstring(payload)
        [body] = html.xpath('//body')
        raw = sanitize_style(body.attrib.get('style', u''))
        body_class = body.attrib.get('class', u'')
        style = "%s {%s}" % (target, raw) if raw else u''
        return style, body_class
    except (ValueError, XMLSyntaxError):
        return None, None


def clean_styles(payload):
    "Cleanup styles"
    if not payload:
        return ''

    html = local_fromstring(payload)
    walker = html.getiterator()
    for tag in walker:
        if 'style' in tag.keys():
            newstyle = sanitize_style(tag.get('style'))
            if newstyle:
                tag.set('style', newstyle)
                if XSS_RE.findall(tag.get('style')):
                    tag.attrib.pop('style')
            else:
                tag.attrib.pop('style')
        if tag.tag == 'style':
            tag.drop_tree()
    return tostring(html)


def decode(strg, encodings=ENCODINGS, charset=None):
    "Decode string"
    if charset is not None:
        try:
            return strg.decode(charset, 'ignore')
        except LookupError:
            pass

    for encoding in encodings:
        try:
            return strg.decode(encoding)
        except UnicodeDecodeError:
            pass
    return strg.decode('ascii', 'ignore')


def sanitize_payload(payload):
    "Sanitize HTML"
    if not payload:
        return '', ''
    styles = []
    payload = clean_payload(payload)
    body_style, body_class = get_body_style(payload)
    if body_style:
        styles.append(body_style)
    safe_attrs = set(defs.safe_attrs)
    safe_attrs.add('style')
    cleaner = Cleaner(remove_tags=UNCLEANTAGS,
                    safe_attrs_only=True,
                    safe_attrs=safe_attrs)
    payload = HTMLTITLE_RE.sub('', payload)
    try:
        html = cleaner.clean_html(payload)
    except ValueError:
        payload = bytes(bytearray(payload, encoding='utf-8'))
        html = cleaner.clean_html(payload)
    except XMLSyntaxError:
        html = ''
    mainstyle = sanitize_css(get_style(html))
    if mainstyle:
        styles.append(decode(mainstyle))
    style = u'\n'.join(styles)
    html = clean_styles(CSS_COMMENT_RE.sub('', html))
    html = set_body_class(html, body_class)
    return html.strip(), style.strip()


class EmailParser(object):
    """Parses a email message"""
    def __init__(self, path):
        if not hasattr(path, 'readlines'):
            path = open(path, 'r')
        self.msg = pyzmail.PyzMessage.factory(path)
        self.parts = []
        self.headers = {}
        self.attachments = []

    def get_headers(self):
        "Get the message headers"
        for header in ['Subject', 'To', 'From', 'Date', 'Message-ID']:
            if header in ['To', 'From']:
                self.headers[header.lower()] = \
                    formataddr(self.msg.get_address(header.lower()))
            elif header == 'Subject':
                self.headers[header.lower()] = \
                    self.msg.get_subject()
            else:
                self.headers[header.lower()] = \
                    self.msg.get_decoded_header(header.lower(), '')

    def parse(self):
        "Parse a message and return a dict"
        has_text = False
        has_html = False

        self.get_headers()
        for part in self.msg.mailparts:
            style = None
            if part.is_body:
                try:
                    payload, _ = pyzmail.parse.decode_text(part.get_payload(),
                            part.charset, None)
                except LookupError:
                    payload, _ = pyzmail.parse.decode_text(part.get_payload(),
                            None, None)
                if part.type == 'text/html':
                    payload, style = sanitize_payload(payload)
                    has_html = True
                else:
                    has_text = True
                msg = dict(type=part.type, content=payload,
                            is_body=part.is_body,
                            style=style)
                self.parts.append(msg)
            else:
                viewable_parts = ('text/', 'image/', 'message/delivery-statu')
                if (part.type.startswith(viewable_parts) and
                    part.part.get_param('attachment', None,
                    'Content-Disposition') is None):
                    if part.type == 'text/html':
                        payload, _ = pyzmail.parse\
                                        .decode_text(part.get_payload(),
                                        part.charset, None)
                        payload, style = sanitize_payload(payload)
                    elif part.type in ['text/plain',
                                        'message/delivery-status']:
                        payload, _ = pyzmail.parse\
                                        .decode_text(part.get_payload(),
                                        part.charset, None)
                    else:
                        payload = ''
                    msg = dict(type=part.type,
                                content=payload,
                                is_body=part.is_body,
                                style=style,
                                filename=part.sanitized_filename)
                    self.parts.append(msg)
                else:
                    msg = dict(type=part.type,
                                content_type=part.type,
                                filename=part.sanitized_filename)
                    self.attachments.append(msg)
        is_multipart = has_text and has_html
        return dict(headers=self.headers, parts=self.parts,
                    attachments=self.attachments,
                    content_type='message/rfc822',
                    has_text=has_text, has_html=has_html,
                    is_multipart=is_multipart)

    def get_attachment(self, attach_id):
        "Get and return an attachment"
        for part in self.msg.mailparts:
            hasl = md5(part.sanitized_filename)
            if part.is_body or (part.type.startswith('image/') and
                            part.part.get_param('attachment', None,
                            'Content-Disposition') is None):
                continue
            if hasl == attach_id:
                return dict(attachment=encodestring(part.get_payload()),
                            name=part.sanitized_filename,
                            mimetype=part.type)
        return None

    def get_img(self, imgid):
        "Return an embedded image"
        for part in self.msg.mailparts:
            if part.is_body:
                continue
            if (imgid.replace('__xoxo__', '/') in
                (part.content_id,
                part.filename,
                part.sanitized_filename)):
                return dict(content_type=part.type,
                            img=encodestring(part.get_payload()),
                            name=part.sanitized_filename)
        return None
