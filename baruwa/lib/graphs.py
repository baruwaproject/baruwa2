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

"Graphing functions"
import os

from cStringIO import StringIO

from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.platypus import Spacer, Table, TableStyle, Paragraph
from reportlab.platypus import PageBreak, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from webhelpers.number import format_byte_size

from baruwa.lib.outputformats import BaruwaPDFTemplate

PIE_COLORS = ['#FF0000', '#ffa07a', '#deb887', '#d2691e', '#008b8b',
            '#006400', '#ff8c00', '#ffd700', '#f0e68c', '#000000']
PIE_CHART_COLORS = [HexColor(pie_color) for pie_color in PIE_COLORS]

pdfmetrics.registerFont(TTFont('Vera', 'Vera.ttf'))
pdfmetrics.registerFont(TTFont('VeraBd', 'VeraBd.ttf'))
pdfmetrics.registerFont(TTFont('VeraIt', 'VeraIt.ttf'))
pdfmetrics.registerFont(TTFont('VeraBI', 'VeraBI.ttf'))
pdfmetrics.registerFontFamily('Vera',
                    normal='Vera',
                    bold='VeraBd',
                    italic='VeraIt',
                    boldItalic='VeraBI')

TABLE_STYLE = TableStyle([
    ('FONT', (0, 0), (-1, -1), 'Vera'),
    ('FONT', (0, 0), (-1, 0), 'VeraBd'),
    ('FONTSIZE', (0, 0), (-1, -1), 8),
    ('GRID', (0, 0), (-1, -1), 0.15, colors.black),
    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
    ('ALIGN', (4, 1), (-1, -1), 'CENTER'),
    ('ALIGN', (0, 0), (0, -1), 'CENTER'),
    ('VALIGN', (4, 1), (-1, -1), 'MIDDLE'),
    ('SPAN', (4, 1), (-1, -1)),
])

PIE_TABLE = TableStyle([
    ('FONT', (0, 0), (-1, 0), 'VeraBd'),
    ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
    ('ALIGN', (1, 0), (-1, 0), 'RIGHT'),
    ('FONTSIZE', (1, 0), (-1, 0), 10),
    ('LINEBELOW', (0, 0), (-1, -1), 0.15, colors.black),
])


STYLES = getSampleStyleSheet()

CUSTOM_HEADING1 = ParagraphStyle(
    name="custheading1", 
    fontName="Vera",
    parent=STYLES['Heading1'], 
)

CUSTOM_HEADING6 = ParagraphStyle(
    name="custheading6", 
    fontName="VeraBd",
    parent=STYLES['Heading6'], 
)


class MessageTotalsGraph(Drawing):
    "Draws a line graph"

    def __init__(self, width=600, height=250, *args, **kwargs):
        Drawing.__init__(self, width, height, *args, **kwargs)

        self.add(HorizontalLineChart(), name='chart')
        self.chart.x = 0
        self.chart.y = 0
        self.chart.height = 225
        self.chart.width = 500
        self.chart.joinedLines = 1
        self.chart.categoryAxis.categoryNames = ['']
        self.chart.categoryAxis.labels.boxAnchor = 'n'
        self.chart.valueAxis.valueMin = 0
        self.chart.valueAxis.valueMax = 60
        self.chart.valueAxis.valueStep = 15
        self.chart.lines[0].strokeWidth = 2
        self.chart.lines[1].strokeWidth = 2
        self.chart.lines[2].strokeWidth = 2
        self.chart.lines[0].strokeColor = colors.green
        self.chart.lines[1].strokeColor = colors.pink
        self.chart.lines[2].strokeColor = colors.red


class PieChart(Drawing):
    "Draws a pie chart"

    def __init__(self, width=100, height=100, *args, **kwargs):
        Drawing.__init__(self, width, height, *args, **kwargs)
        self.add(Pie(), name='chart')
        #transparent = colors.Color(255, 255, 255, alpha=0.5)
        #print dir(transparent)
        #print dir(self)
        #self.setFillColor(transparent)

        for i in range(10):
            self.chart.slices[i].fillColor = PIE_CHART_COLORS[i]
            self.chart.slices[i].labelRadius = 1.4
            self.chart.slices[i].fontName = 'Helvetica'
            self.chart.slices[i].fontSize = 8


class BarChart(Drawing):
    "Draws a bar chart"

    def __init__(self, width=600, height=250, *args, **kwargs):
        Drawing.__init__(self, width, height, *args, **kwargs)

        self.add(VerticalBarChart(), name='chart')
        self.add(HorizontalLineChart(), name='plot')
        self.chart.x = 10
        self.chart.y = 10
        self.chart.width = 500
        self.chart.height = 225
        self.chart.strokeColor = None
        self.chart.valueAxis.valueMin = 0
        #self.chart.valueAxis.valueMax = 50
        #self.chart.valueAxis.valueStep = 10
        self.chart.data = [(1, 2, 5), ]
        self.chart.categoryAxis.visible = 1
        self.chart.bars[0].fillColor = colors.green
        self.chart.bars[1].fillColor = colors.pink
        self.chart.bars[2].fillColor = colors.red
        self.chart.categoryAxis.categoryNames = ['']
        self.plot.x = 10
        self.plot.y = 10
        self.plot.width = 500
        self.plot.height = 225
        self.plot.valueAxis.visible = 0
        #self.plot.valueAxis.valueMin = 0
        #print dir(self.plot.valueAxis)
        self.plot.lines[0].strokeColor = colors.blue


class SpamChart(Drawing):
    "Draws a spam chart"

    def __init__(self, width=940, height=250, *args, **kwargs):
        Drawing.__init__(self, width, height, *args, **kwargs)

        self.add(VerticalBarChart(), name='chart')
        self.chart.x = 30
        self.chart.y = 15
        self.chart.width = 930
        self.chart.height = 220
        self.chart.strokeColor = None
        self.chart.valueAxis.valueMin = 0
        self.chart.data = [(1, 2, 5), ]
        self.chart.categoryAxis.visible = 1
        self.chart.bars[0].fillColor = colors.blue
        self.chart.categoryAxis.categoryNames = ['']


class PDFReport(object):
    """Generates a PDF report"""

    def __init__(self, logo, title='Baruwa mail report'):
        "Init"
        self.pdf = StringIO()
        self.doc = BaruwaPDFTemplate(self.pdf, topMargin=50, bottomMargin=18)
        img = u''
        if os.path.exists(logo):
            img = Image(logo)
        logobj = [(img, title)]
        logo_table = Table(logobj, [2.0 * inch, 5.4 * inch])
        logo_table.setStyle(PIE_TABLE)
        self.parts = [logo_table]
        self.parts.append(Spacer(1, 20))
        self.sentry = 0

    def _draw_square(self, color):
        "draws a square"
        square = Drawing(5, 5)
        sqr = Rect(0, 2.5, 5, 5)
        sqr.fillColor = color
        sqr.strokeColor = color
        square.add(sqr)
        return square

    def _pie_chart(self, data, title, headers, sortby):
        "Build PIE chart"
        headings = [headers]
        rows = [[self._draw_square(PIE_CHART_COLORS[index]),
                getattr(row, 'address'), getattr(row, 'count'),
                format_byte_size(getattr(row, 'size')), '']
                for index, row in enumerate(data)]
        if len(rows) and len(rows) != 10:
            missing = 10 - len(rows)
            add_rows = [('', '', '', '', '')
                        for ind in range(missing)]
            rows.extend(add_rows)
        if not rows:
            return

        headings.extend(rows)
        piedata = [getattr(row, sortby) for row in data]
        total = sum(piedata)
        labels = [("%.1f%%" % ((1.0 * getattr(row, sortby)
                    / total) * 100)) for row in data]

        pie = PieChart()
        pie.chart.labels = labels
        pie.chart.data = piedata
        headings[1][4] = pie

        table_with_style = Table(headings, [0.2 * inch,
                            2.8 * inch, 0.5 * inch,
                            0.7 * inch, 3.2 * inch])
        table_with_style.setStyle(TABLE_STYLE)
        paragraph = Paragraph(title, CUSTOM_HEADING1)

        self.parts.append(paragraph)
        self.parts.append(table_with_style)
        self.parts.append(Spacer(1, 70))
        if (self.sentry % 2) == 0:
            self.parts.append(PageBreak())

    def _bar_chart(self, data, title, headers):
        "Build the bar chart"
        self.parts.append(Paragraph(title, CUSTOM_HEADING1))
        rows = [(
                Table([[self._draw_square(colors.white),
                    Paragraph(headers['date'], CUSTOM_HEADING6)]],
                    [0.35 * inch, 1.13 * inch, ]),
                Table([[self._draw_square(colors.green),
                    Paragraph(headers['mail'], CUSTOM_HEADING6)]],
                    [0.35 * inch, 1.13 * inch, ]),
                Table([[self._draw_square(colors.pink),
                    Paragraph(headers['spam'], CUSTOM_HEADING6)]],
                    [0.35 * inch, 1.13 * inch, ]),
                Table([[self._draw_square(colors.red),
                    Paragraph(headers['virus'], CUSTOM_HEADING6)]],
                    [0.35 * inch, 1.13 * inch, ]),
                Table([[self._draw_square(colors.blue),
                    Paragraph(headers['volume'], CUSTOM_HEADING6)]],
                    [0.35 * inch, 1.13 * inch, ]),
                ),]
        if not data:
            return
        graph, rows = build_barchart(data,
                                    rows=rows,
                                    header=headers['totals'])
        graph_table = Table([[graph], ], [7.4 * inch])
        self.parts.append(graph_table)
        self.parts.append(Spacer(1, 20))
        graph_table = Table(rows, [1.48 * inch, 1.48 * inch,
        1.48 * inch, 1.48 * inch, 1.48 * inch])
        graph_table.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('FONT', (0, 0), (-1, -1), 'Helvetica'),
                ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.15, colors.black),
                ('FONT', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        self.parts.append(graph_table)

    def add(self, data, title, headers, sortby=None, chart='pie'):
        """Add the charts"""
        self.sentry += 1
        if chart == 'pie':
            self._pie_chart(data, title, headers, sortby)
        if chart == 'bar':
            self._bar_chart(data, title, headers)
        else:
            pass

    def build(self):
        """Generate the PDF"""
        self.doc.title = 'Baruwa Usage Reports'
        self.doc.build(self.parts)
        pdf = self.pdf.getvalue()
        self.pdf.close()
        return pdf


def build_barchart(data, rows=None, header=None):
    "Builds a BarChart from Data supplied"
    if rows is None:
        graph = BarChart(950, 250)
        graph.chart.x = 30
        graph.chart.y = 15
        graph.chart.width = 940
        graph.chart.height = 220
        graph.plot.x = 30
        graph.plot.y = 15
        graph.plot.width = 940
        graph.plot.height = 220
    else:
        graph = BarChart()
    dates = []
    mail_size = []
    mail_total = []
    spam_total = []
    virus_total = []
    for ind, msg in enumerate(data):
        if ind % 10:
            dates.append('')
        else:
            dates.append(str(msg.date))
        mail_total.append(int(msg.mail_total))
        spam_total.append(int(msg.spam_total))
        virus_total.append(int(msg.virus_total))
        mail_size.append(int(msg.total_size))
        if rows:
            rows.append((str(msg.date),
                        msg.mail_total,
                        msg.spam_total,
                        msg.virus_total,
                        format_byte_size(msg.total_size)))
    graph.chart.data = [tuple(mail_total),
                        tuple(spam_total),
                        tuple(virus_total)]
    graph.plot.data = [tuple(mail_size)]
    graph.chart.categoryAxis.categoryNames = dates
    graph.plot.categoryAxis.categoryNames = dates
    if rows:
        rows.append((header,
                    sum(mail_total),
                    sum(spam_total),
                    sum(virus_total),
                    format_byte_size(sum(mail_size))))
        return graph, rows

    return graph


def build_spam_chart(data):
    "Build the SPAM distribution chart"
    graph = SpamChart()
    scores = []
    counts = []
    for record in data:
        scores.append(str(record.score))
        counts.append(record.count)
    graph.chart.data = [tuple(counts)]
    graph.chart.categoryAxis.categoryNames = scores
    return graph
    
