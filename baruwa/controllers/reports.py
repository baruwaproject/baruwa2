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
"Reports controller"

import os
import json
import logging
import threading

from cStringIO import StringIO

from pylons import request, response, session, tmpl_context as c, url, config
from pylons.controllers.util import abort, redirect
from pylons.i18n.translation import _
from repoze.what.predicates import not_anonymous
from repoze.what.plugins.pylonshq import ActionProtector
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from reportlab.lib import colors
from reportlab.graphics import renderPM
from webhelpers.number import format_byte_size

from baruwa.lib.dates import now
from baruwa.lib.base import BaseController, render
from baruwa.lib.helpers import flash, flash_alert
from baruwa.lib.outputformats import CSVWriter
from baruwa.lib.query import DynaQuery, UserFilter, ReportQuery
from baruwa.lib.query import sa_scores, message_totals, MsgCount
from baruwa.lib.graphs import PIE_COLORS, build_spam_chart
from baruwa.lib.audit import audit_log
from baruwa.model.meta import Session
from baruwa.model.messages import Message
from baruwa.model.reports import SavedFilter
from baruwa.lib.caching_query import FromCache
from baruwa.lib.graphs import PieChart, PDFReport, build_barchart
from baruwa.lib.templates.helpers import country_flag, get_hostname
from baruwa.forms.reports import FilterForm, FILTER_BY, FILTER_ITEMS
from baruwa.lib.audit.msgs.reports import REPORTVIEW_MSG, REPORTDL_MSG

log = logging.getLogger(__name__)


REPORTS = {
            '1': {'address': 'from_address', 'sort': 'count',
                'title': _('Top Senders by Quantity')},
            '2': {'address': 'from_address', 'sort': 'size',
                'title': _('Top Senders by Volume')},
            '3': {'address': 'from_domain', 'sort': 'count',
                'title': _('Top Sender Domains by Quantity')},
            '4': {'address': 'from_domain', 'sort': 'size',
                'title': _('Top Sender Domains by Volume')},
            '5': {'address': 'to_address', 'sort': 'count',
                'title': _('Top Recipients by Quantity')},
            '6': {'address': 'to_address', 'sort': 'size',
                'title': _('Top Recipients by Volume')},
            '7': {'address': 'to_domain', 'sort': 'count',
                'title': _('Top Recipient Domains By Quantity')},
            '8': {'address': 'to_domain', 'sort': 'size',
                'title': _('Top Recipient Domains By Volume')},
            '9': {'address': '', 'sort': '',
                'title': _('Spam Score distribution')},
            '10': {'address': 'clientip', 'sort': 'count',
                'title': _('Top mail hosts by quantity')},
            '11': {'address': '', 'sort': '',
                'title': _('Total messages [ After SMTP ]')}
            }


JSON_HEADER = 'application/json; charset=utf-8'
PDF_HEADER = 'application/pdf; charset=utf-8'


def processfilters(filt, filters):
    loaded = False
    for thefilter in filters:
        if (int(thefilter['filter']) == filt.option and
            thefilter['value'] == filt.value and
            thefilter['field'] == filt.field):
            loaded = True
    return {'id': filt.id, 'name': filt.name,
            'value': filt.value, 'field': filt.field,
            'filter': filt.option, 'loaded': loaded}

lock = threading.RLock()


class ReportsController(BaseController):
    @ActionProtector(not_anonymous())
    def __before__(self):
        "set context"
        BaseController.__before__(self)
        if self.identity:
            c.user = self.identity['user']
        else:
            c.user = None
        c.selectedtab = 'reports'

    def __after__(self):
        "Clean up"
        if hasattr(self, 'imgfile'):
            self.imgfile.close()

    def _get_filter(self, filterid):
        "utility to return filter object"
        try:
            cachekey = u'filter-%s' % filterid
            q = Session.query(SavedFilter).filter(SavedFilter.id==filterid)\
                .options(FromCache('sql_cache_short', cachekey))
            if self.invalidate:
                q.invalidate()
            savedfilter = q.one()
        except NoResultFound:
            savedfilter = None
        return savedfilter

    def _save_filter(self, filt):
        "utility to save filters to session"
        if not session.get('filter_by', False):
            session['filter_by'] = []
            session['filter_by'].append(filt)
            session.save()
        else:
            if not filt in session['filter_by']:
                session['filter_by'].append(filt)
                session.save()

    def _png(self, data, reportid):
        "PNG"
        if int(reportid) == 11:
            chart = build_barchart(data)
        elif int(reportid) == 9:
            chart = build_spam_chart(data)
        else:
            piedata = [getattr(row, REPORTS[reportid]['sort'])
                        for row in data]
            total = sum(piedata)
            labels = [("%.1f%%" % ((1.0 * getattr(row,
                        REPORTS[reportid]['sort']) / total) * 100))
                        for row in data]
            chart = PieChart(350, 284)
            chart.chart.labels = labels
            chart.chart.data = piedata
            chart.chart.width = 200
            chart.chart.height = 200
            chart.chart.x = 90
            chart.chart.y = 30
            chart.chart.slices.strokeWidth = 1
            chart.chart.slices.strokeColor = colors.black

        self.imgfile = StringIO()
        renderPM.drawToFile(chart, self.imgfile, 'PNG',
                        bg=colors.HexColor('#FFFFFF'))

    def _csv(self, data):
        "output to csv"
        try:
            self.csvfile = StringIO()
            head = data[0]
            format = head.keys()
            csvwriter = CSVWriter(self.csvfile, format)
            csvwriter.writeasobj(data)
        except IndexError:
            pass

    def _generate_png(self, data, reportid):
        "Generate PNG images on the fly"
        lock.acquire()
        try:
            self._png(data, reportid)
            response.content_type = 'image/png'
            response.headers['Cache-Control'] = 'max-age=0'
            pngdata = self.imgfile.getvalue()
            response.headers['Content-Length'] = len(pngdata)
        except:
            abort(404)
        finally:
            self.imgfile.close()
            lock.release()
        return pngdata

    def _generate_csv(self, data, reportid):
        "Generate CSV files on the fly"
        lock.acquire()
        try:
            self._csv(data)
            response.content_type = 'text/csv'
            response.headers['Cache-Control'] = 'max-age=0'
            csvdata = self.csvfile.getvalue()
            disposition = ('attachment; filename=%s.csv' %
                            REPORTS[reportid]['title'].replace(' ', '_'))
            response.headers['Content-Disposition'] = str(disposition)
            response.headers['Content-Length'] = len(csvdata)
        except:
            abort(404)
        finally:
            self.csvfile.close()
            lock.release()
        return csvdata

    def _generate_pdf(self, data, reportid):
        "Generate PDF's on the fly"
        logo = os.path.join(config['pylons.paths']['static_files'],
                            'imgs', 'logo.png')
        lock.acquire()
        try:
            pdfcreator = PDFReport(logo, _('Baruwa mail report'))
            sortby = REPORTS[reportid]['sort']
            if reportid in ['1', '2', '3', '4', '5', '6', '7', '8', '10']:
                pieheadings = ('', _('Address'), _('Count'), _('Volume'), '')
                pdfcreator.add(data, REPORTS[reportid]['title'],
                                pieheadings, sortby)
            if reportid == '11':
                totalsheaders = dict(date=_('Date'), mail=_('Mail totals'),
                                spam=_('Spam totals'),
                                virus=_('Virus totals'),
                                volume=_('Mail volume'),
                                totals=_('Totals'))
                pdfcreator.add(data, _('Message Totals'), totalsheaders,
                                chart='bar')
            response.headers['Content-Type'] = PDF_HEADER
            disposition = ('attachment; filename=%s.pdf' %
            REPORTS[reportid]['title'].replace(' ', '_'))
            response.headers['Content-Disposition'] = str(disposition)
            pdfdata = pdfcreator.build()
            response.headers['Content-Length'] = len(pdfdata)
        finally:
            lock.release()
        return pdfdata

    # def _get_count(self):
    #     "Get message count"
    #     countq = MsgCount(Session, c.user)
    #     return countq()

    def _get_data(self, format=None, success=None, errors=None):
        "Get report data"
        filters = session.get('filter_by', [])
        query = Session.query(func.max(Message.timestamp).label('oldest'),
                            func.min(Message.timestamp).label('newest'))
        uquery = UserFilter(Session, c.user, query)
        query = uquery.filter()
        # count = self._get_count()
        countq = MsgCount(Session, c.user)
        count = countq()
        cachekey = u'savedfilters-%s' % c.user.username
        sfq = Session.query(SavedFilter)\
                .filter(SavedFilter.user == c.user)\
                .options(FromCache('sql_cache_short', cachekey))
        if self.invalidate:
            sfq.invalidate()
        savedfilters = sfq.all()
        if filters:
            dynq = DynaQuery(Message, query, filters)
            query = dynq.generate()
            dcountq = Session.query(func.count(Message.id).label('count'))
            dcountqi = UserFilter(Session, c.user, dcountq)
            dcountq = dcountqi.filter()
            dyncq = DynaQuery(Message, dcountq, filters)
            dcountq = dyncq.generate()
            dcount = dcountq.one()
            count = dcount.count
        cachekey = u'report-aggregates-%s' % c.user.username
        query = query.options(FromCache('sql_cache_short', cachekey))
        if self.invalidate:
            query.invalidate()
        data = query.all()
        saved_filters = [processfilters(filt, filters)
                        for filt in savedfilters]
        if format is None:
            return data, count, filters, saved_filters
        else:
            if format == 'json':
                data = data[0]
                filterdict = dict(FILTER_ITEMS)
                filterbydict = dict(FILTER_BY)
                active_filters = [dict(filter_field=unicode(filterdict[filt['field']]),
                                    filter_by=unicode(filterbydict[filt['filter']]),
                                    filter_value=unicode(filt['value']))
                                    for filt in filters]
                try:
                    newest = data.newest.strftime("%Y-%m-%d %H:%M")
                    oldest = data.oldest.strftime("%Y-%m-%d %H:%M")
                except AttributeError:
                    newest = ''
                    oldest = ''
                datadict = dict(count=count, newest=newest, oldest=oldest)
                jsondata = dict(success=success, data=datadict, errors=errors,
                                active_filters=active_filters,
                                saved_filters=saved_filters)
                return jsondata

    def index(self, format=None):
        "Index page"
        c.form = FilterForm(request.POST, csrf_context=session)
        errors = ''
        success = True
        if request.POST and c.form.validate():
            fitem = dict(field=c.form.filtered_field.data,
                        filter=c.form.filtered_by.data,
                        value=c.form.filtered_value.data)
            self._save_filter(fitem)
        elif request.POST and not c.form.validate():
            success = False
            key = c.form.errors.keys()
            msgs = [unicode(gkey) for gkey in c.form.errors[key[0]]] 
            errors = dict(field=key[0], msg=', '.join(msgs))
        if success:
            self.invalidate = True
        if format == 'json':
            response.headers['Content-Type'] = JSON_HEADER
            jsondata = self._get_data(format, success, errors)
            return json.dumps(jsondata)
        data, count, filters, saved_filters = self._get_data()
        c.data = data
        c.count = count
        c.active_filters = filters
        c.saved_filters = saved_filters
        c.FILTER_BY = FILTER_BY
        c.FILTER_ITEMS = FILTER_ITEMS
        return render('/reports/index.html')

    def display(self, reportid, format=None):
        "Display a report"
        try:
            c.report_title = REPORTS[reportid]['title']
        except KeyError:
            abort(404)

        filters = session.get('filter_by', [])
        if reportid in ['1', '2', '3', '4', '5', '6', '7', '8', '10']:
            rquery = ReportQuery(c.user, reportid, filters)
            query = rquery()
            cachekey = u'reportquery-%s-%s' % (c.user.username, reportid)
            query = query.options(FromCache('sql_cache_short', cachekey))
            data = query[:10]
            if format == 'png':
                return self._generate_png(data, reportid)
            if format == 'csv':
                info = REPORTDL_MSG % dict(r=c.report_title, f='csv')
                audit_log(c.user.username,
                        1, unicode(info), request.host,
                        request.remote_addr, now())
                return self._generate_csv(data, reportid)
            jsondata = [dict(tooltip=getattr(item, 'address'),
                        y=getattr(item, REPORTS[reportid]['sort']),
                        stroke='black', color=PIE_COLORS[index],
                        size=getattr(item, 'size'))
                        for index, item in enumerate(data)]
            template = '/reports/piereport.html'
        if reportid == '9':
            query = sa_scores(Session, c.user)
            if filters:
                dynq = DynaQuery(Message, query, filters)
                query = dynq.generate()
            cachekey = u'sascores-%s' % c.user.username
            query = query.options(FromCache('sql_cache_short', cachekey))
            data = query.all()
            if format == 'json':
                scores = []
                counts = []
                for row in data:
                    scores.append(dict(value=int(row.score),
                                text=str(row.score)))
                    counts.append(dict(y=int(row.count), tooltip=(_('Score ') +
                                str(row.score) + ': ' + str(row.count))))
                jsondata = dict(scores=scores, count=counts)
            elif format == 'png':
                return self._generate_png(data, reportid)
            else:
                jsondata = {}
                jsondata['labels'] = [{'value': index + 1,
                                    'text': str(item.score)}
                                    for index, item in enumerate(data)]
                jsondata['scores'] = [item.count for item in data]
                template = '/reports/barreport.html'
        if reportid == '10':
            if format == 'json':
                data = [[item.address.strip(),
                        get_hostname(item.address.strip()),
                        country_flag(item.address.strip()),
                        item.count, format_byte_size(item.size)]
                        for item in data]
            template = '/reports/relays.html'
        if reportid == '11':
            query = message_totals(Session, c.user)
            if filters:
                dynq = DynaQuery(Message, query, filters)
                query = dynq.generate()
            cachekey = u'msgtotals-%s' % c.user.username
            query = query.options(FromCache('sql_cache_short', cachekey))
            data = query.all()
            if format == 'png':
                return self._generate_png(data, reportid)
            elif format == 'json':
                dates = []
                mail_total = []
                spam_total = []
                size_total = []
                virus_total = []
                for row in data:
                    dates.append(str(row.date))
                    mail_total.append(int(row.mail_total))
                    spam_total.append(int(row.spam_total))
                    virus_total.append(int(row.virus_total))
                    size_total.append(int(row.total_size))
                jsondata = dict(dates=[dict(value=index + 1, text=date)
                                for index, date in enumerate(dates)],
                            mail=[dict(y=total,
                                tooltip=(_('Mail totals on ') +
                                dates[index] + ': ' + str(total)))
                                for index, total in enumerate(mail_total)],
                            spam=[dict(y=total,
                                tooltip=(_('Spam totals on ') +
                                dates[index] + ': ' + str(total)))
                                for index, total in enumerate(spam_total)],
                            virii=[dict(y=total,
                                tooltip=(_('Virus totals on ') +
                                dates[index] + ': ' + str(total)))
                                for index, total in enumerate(virus_total)],
                            volume=size_total, mail_total=sum(mail_total),
                            spam_total=sum(spam_total),
                            virus_total=sum(virus_total),
                            volume_total=sum(size_total))
                try:
                    vpct = "%.1f" % ((1.0 * sum(virus_total) /
                                    sum(mail_total)) * 100)
                    spct = "%.1f" % ((1.0 * sum(spam_total) /
                                    sum(mail_total)) * 100)
                except ZeroDivisionError:
                    vpct = "0.0"
                    spct = "0.0"
                jsondata['vpct'] = vpct
                jsondata['spct'] = spct
                data = [dict(date=str(row.date),
                        mail_total=row.mail_total,
                        spam_total=row.spam_total,
                        virus_total=row.virus_total,
                        size_total=format_byte_size(row.total_size),
                        virus_percent="%.1f" % ((1.0 * int(row.virus_total) /
                        int(row.mail_total)) * 100),
                        spam_percent="%.1f" % ((1.0 * int(row.spam_total) /
                        int(row.mail_total)) * 100)) for row in data]
            elif format == 'csv':
                info = REPORTDL_MSG % dict(r=c.report_title, f='csv')
                audit_log(c.user.username,
                        1, unicode(info), request.host,
                        request.remote_addr, now())
                return self._generate_csv(data, reportid)
            else:
                jsondata = dict(mail=[],
                                spam=[],
                                virus=[],
                                volume=[],
                                labels=[])
                for index, item in enumerate(data):
                    jsondata['spam'].append(item.spam_total)
                    jsondata['mail'].append(item.mail_total)
                    jsondata['virus'].append(item.virus_total)
                    jsondata['volume'].append(item.total_size)
                    jsondata['labels'].append(dict(text=str(item.date),
                                            value=index))
                template = '/reports/listing.html'
        if format == 'json':
            response.headers['Content-Type'] = JSON_HEADER
            return json.dumps(dict(items=list(data), pie_data=jsondata))
        if format == 'pdf' and reportid != '9':
            info = REPORTDL_MSG % dict(r=c.report_title, f='pdf')
            audit_log(c.user.username,
                    1, unicode(info), request.host,
                    request.remote_addr, now())
            return self._generate_pdf(data, reportid)
        c.reportid = reportid
        c.chart_data = json.dumps(jsondata)
        c.top_items = data
        c.active_filters = filters
        c.saved_filters = []
        c.FILTER_BY = FILTER_BY
        c.FILTER_ITEMS = FILTER_ITEMS
        c.form = FilterForm(request.POST, csrf_context=session)
        info = REPORTVIEW_MSG % dict(r=c.report_title)
        audit_log(c.user.username,
                1, unicode(info), request.host,
                request.remote_addr, now())
        return render(template)

    def delete(self, filterid, format=None):
        "Delete a temp filter"
        filters = session.get('filter_by', [])
        errors = {}
        success = True
        try:
            del filters[int(filterid)]
        except IndexError:
            msg = _("The filter does not exist")
            if format != 'json':
                flash_alert(msg)
            errors = dict(msg=msg)
            success = False
        if format == 'json':
            response.headers['Content-Type'] = JSON_HEADER
            if not errors:
                self.invalidate = True
            return json.dumps(self._get_data(format, success, errors))
        flash(_("The filter has been removed"))
        redirect(url(controller='reports'))

    def save(self, filterid, format=None):
        "Save a temp filter"
        filters = session.get('filter_by', [])
        try:
            filt = filters[int(filterid)]
            filteritems = dict(FILTER_ITEMS)
            filterby = dict(FILTER_BY)
            name = u"%s %s %s" % (filteritems[filt["field"]],
                                filterby[filt["filter"]],
                                filt["value"])
            saved = SavedFilter(
                        name=name,
                        field=filt["field"],
                        option=filt["filter"],
                        user=c.user
                    )
            saved.value = filt["value"]
            Session.add(saved)
            Session.commit()
            success = True
            error_msg = ''
            self.invalidate = True
        except IndexError:
            success = False
            error_msg = _("The filter does not exist")
        except IntegrityError:
            success = False
            error_msg = _("The filter already exists")
            Session.rollback()
        if format == 'json':
            response.headers['Content-Type'] = JSON_HEADER
            errors = dict(msg=error_msg)
            return json.dumps(self._get_data(format, success, errors))
        if success:
            flash(_("The filter has been saved"))
        else:
            flash(error_msg)
        redirect(url('toplevel', controller='reports'))

    def load(self, filterid, format=None):
        "Load a saved filter"
        savedfilter = self._get_filter(filterid)
        if not savedfilter:
            abort(404)

        filt = dict(filter=str(savedfilter.option),
                    field=savedfilter.field,
                    value=savedfilter.value)
        self._save_filter(filt)
        if format == 'json':
            response.headers['Content-Type'] = JSON_HEADER
            self.invalidate = True
            return json.dumps(self._get_data(format, True, {}))
        redirect(url('toplevel', controller='reports'))

    def delete_stored(self, filterid, format=None):
        "Delete a saved dilter"
        savedfilter = self._get_filter(filterid)
        if not savedfilter:
            abort(404)

        Session.delete(savedfilter)
        Session.commit()
        if format == 'json':
            response.headers['Content-Type'] = JSON_HEADER
            self.invalidate = True
            return json.dumps(self._get_data(format, True, {}))
        flash(_("The filter has been deleted"))
        redirect(url('toplevel', controller='reports'))

    def show_filters(self):
        "Show filters"
        filters = session.get('filter_by', [])
        c.active_filters = filters
        c.FILTER_BY = FILTER_BY
        c.FILTER_ITEMS = FILTER_ITEMS
        return render('/reports/show_filters.html')

    def add_filters(self):
        "Show form"
        c.form = FilterForm(request.POST, csrf_context=session)
        return render('/reports/add_filters.html')
