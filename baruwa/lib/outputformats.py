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

import csv

from StringIO import StringIO

from lxml.html import defs
from lxml.html.clean import Cleaner
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate
#from reportlab.lib.pdfencrypt import StandardEncryption


class CSVWriter:
    """A CSV writer
    """
    def __init__(self, handle, formt):
        self.stream = handle
        self.writer = csv.DictWriter(self.stream, formt)

    def writeasobj(self, rows):
        "write csv"
        try:
            head = rows[0]
            headings = head.keys()
            hdict = {}
            for key in headings:
                hdict[key] = key.capitalize()
            output = [hdict]
            for row in rows:
                row = row.__dict__
                del row['_labels']
                output.append(row)
            self.writer.writerows(output)
        except IndexError:
            pass


class SignatureCleaner(Cleaner):
    """Over ride Cleaner to allow the font face attribute"""
    def __call__(self, doc):
        "clean signatures"
        Cleaner.__call__(self, doc)
        safe_attrs = set(defs.safe_attrs)
        safe_attrs.add('face')
        for elm in doc.iter():
            attrib = elm.attrib
            for aname in attrib.keys():
                if aname not in safe_attrs:
                    del attrib[aname]


def build_csv(rows, keys):
    "Build a CSV file"
    try:
        csvfile = StringIO()
        writer = csv.DictWriter(csvfile, keys)
        heading = {}
        for key in keys:
            heading[key] = "'%s'" % key
        writer.writerow(heading)
        writer.writerows(rows)
        return csvfile.getvalue()
    finally:
        csvfile.close()


class BaruwaPDFTemplate(SimpleDocTemplate):
    "Baruwa customization"

    def __init__(self, filename, **kwargs):
        "Overide to provide baruwa defaults"
        SimpleDocTemplate.__init__(self, filename, **kwargs)
        #self.encrypt = StandardEncryption('', canModify=0)
        self.pagesize = A4
        self.author = 'Baruwa 2.0'
