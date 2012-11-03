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

"""Parse an email into a dictionary structure"""

import email
import base64
import codecs

from email.Header import decode_header
from email.utils import parseaddr, formataddr

from baruwa.lib.mail.html import CustomCleaner
from baruwa.lib.regex import HTMLTITLE_RE, I18N_HEADER_MATCH


UNCLEANTAGS = ['html', 'title', 'head', 'link', 'a', 'body', 'base']


def get_header(header_text, default="ascii"):
    "Decode and return the header"
    if not header_text:
        return header_text

    sections = decode_header(header_text)
    parts = []
    for section, encoding in sections:
        try:
            parts.append(section.decode(encoding or default, 'replace'))
        except LookupError:
            parts.append(section.decode(default, 'replace'))
    return u' '.join(parts)
    # return u' '.join(section.decode(enc or default, 'replace')
    #                 for section, enc in sections)


def return_text_part(part):
    "Encodes the message as utf8"
    body = part.get_payload(decode=True)
    charset = part.get_content_charset('latin1')
    try:
        codecs.lookup(charset)
    except LookupError:
        charset = 'ascii'
    try:
        text = body.decode(charset, 'replace')
    except UnicodeError:
        text = body.decode('ascii', 'replace')
    return text


def parse_attached_msg(msg):
    "Parse and attached message"
    content_type = msg.get_content_type()
    return dict(filename='rfc822.txt', content_type=content_type)

def decode_email(raw_email):
    "Decodes an email address"
    if raw_email is None:
        return u''

    if I18N_HEADER_MATCH.match(raw_email):
        name, email_addr = parseaddr(get_header(raw_email))
    else:
        name, email_addr = parseaddr(raw_email)
        name = get_header(name)
        email_addr = get_header(email_addr)
    full_addr = formataddr((name, email_addr))
    return full_addr

class EmailParser(object):
    """Parses a email message"""
    def __init__(self, path):
        if hasattr(path, 'readlines'):
            self.msg = email.message_from_file(path)
        else:
            with open(path, 'r') as fip:
                self.msg = email.message_from_file(fip)
        self.parts = []
        self.headers = {}
        self.attachments = []

    def process_headers(self, msg):
        "Populate the headers"
        for header in ['Subject', 'To', 'From', 'Date', 'Message-ID']:
            if header in ['To', 'From']:
                self.headers[header.lower()] = decode_email(msg[header])
            else:
                self.headers[header.lower()] = get_header(msg[header])

    def parse(self):
        "Parse a message and return a dict"
        self.process_headers(self.msg)
        self.process_msg(self.msg, self.parts, self.attachments)
        return dict(headers=self.headers, parts=self.parts,
                    attachments=self.attachments,
                    content_type='message/rfc822')

    def process_msg(self, message, parts, attachments):
        "Recursive message processing"

        content_type = message.get_content_type()
        attachment = message.get_param('attachment',
                    None, 'Content-Disposition')
        if content_type == 'message/rfc822':
            [attachments.append(parse_attached_msg(msg))
                for msg in message.get_payload()]
            return True

        if message.is_multipart():
            if content_type == 'multipart/alternative':
                for par in reversed(message.get_payload()):
                    if self.process_msg(par, parts, attachments):
                        return True
            else:
                [self.process_msg(par, parts, attachments)
                    for par in message.get_payload()]
            return True
        success = False

        if (content_type == 'text/html' and attachment is None):
            parts.append(dict(type='html',
                        content=self.return_html_part(message)))
            success = True
        elif (content_type.startswith('text/') and attachment is None):
            parts.append(dict(type='text',
                        content=return_text_part(message)))
            success = True
        elif (content_type.startswith('image/') and attachment is None):
            parts.append(dict(type='image',
                        content=message.get_payload(decode=True),
                        name=message.get_param('name', None, 'Content-Type'),
                        content_type=content_type))
            success = True
        filename = message.get_filename(None)
        if filename and not attachment is None:
            attachments.append(dict(filename=get_header(filename),
                                content_type=content_type))
            success = True
        return success

    def return_html_part(self, part):
        "Sanitize the html and return utf8"
        charset = part.get_content_charset('latin1')
        try:
            codecs.lookup(charset)
        except LookupError:
            charset = 'ascii'
        #return self.sanitize_html(body.decode(charset, 'replace'))
        body = part.get_payload(decode=True)
        return self.sanitize_html(body.decode(charset, 'replace'))

    def get_attachment(self, attach_id):
        "Get and return an attachment"
        num = 0
        attach_id = int(attach_id)

        for part in self.msg.walk():
            attachment = part.get_param('attachment',
                        None, 'Content-Disposition')
            if not attachment is None:
                filename = part.get_filename(None)
                if filename:
                    num += 1
                if attach_id == num:
                    if part.is_multipart():
                        data = part.as_string()
                    else:
                        data = part.get_payload(decode=True)
                    filename = get_header(filename)
                    return dict(attachment=base64.encodestring(data),
                                name=filename,
                                mimetype=part.get_content_type())
        return None

    def get_img(self, imgid):
        "Return an embedded image"
        for part in self.msg.walk():
            content_id = part.get('Content-Id', '').strip('<>')
            filename = part.get_filename()
            if imgid.replace('__xoxo__', '/') in (content_id, filename):
                content = part.get_payload(decode=True)
                return dict(content_type=part.get_content_type(),
                            img=base64.encodestring(content),
                            name=filename)
        return None

    def sanitize_html(self, msg):
        "Clean up html"
        cleaner = CustomCleaner(style=True,
                                remove_tags=UNCLEANTAGS,
                                safe_attrs_only=True)
        # workaround to bug in lxml which does not remove title
        msg = HTMLTITLE_RE.sub('', msg)
        html = cleaner.clean_html(msg)
        return html

