# -*- coding: utf-8 -*-
# Baruwa - Web 2.0 MailScanner front-end.
# Copyright (C) 2010-2012  Andrew Colin Kissa <andrew@topdog.za.net>
# vim: ai ts=4 sts=4 et sw=4

"status tasks"

import os
import datetime

import psutil

from StringIO import StringIO

from pylons import config
from celery.task import task
from sqlalchemy.pool import NullPool
from eventlet.green import subprocess
from sqlalchemy import desc
from sqlalchemy import engine_from_config
from sqlalchemy.exc import DatabaseError
from sphinxapi import SphinxClient, SPH_MATCH_EXTENDED2
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Table
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Image, Spacer, TableStyle

from baruwa.model.meta import Session
from baruwa.lib.graphs import PIE_TABLE
from baruwa.lib.query import clean_sphinx_q
from baruwa.lib.mail.queue.exim import EximQueue
from baruwa.lib.mail.message import PreviewMessage
from baruwa.lib.mail.queue.convert import Exim2Mbox
from baruwa.lib.mail.queue.search import search_queue
from baruwa.model.status import AuditLog, CATEGORY_MAP
from baruwa.commands.queuestats import update_queue_stats
from baruwa.lib.regex import EXIM_MSGID_RE, BAYES_INFO_RE
from baruwa.lib.outputformats import build_csv, BaruwaPDFTemplate
from baruwa.lib.misc import get_processes, get_config_option, wrap_string, _


STYLES = getSampleStyleSheet()


if not Session.registry.has():
    engine = engine_from_config(config, 'sqlalchemy.', poolclass=NullPool)
    Session.configure(bind=engine)


@task(name="get-system-status")
def systemstatus():
    "process via mq"
    logger = systemstatus.get_logger()
    logger.info("Checking system status")

    stats = dict(mem=None,
                cpu=None,
                load=None,
                net=[],
                mta=None,
                scanners=None,
                time=None,
                uptime=None,
                av=None,
                partitions=[])
    def _obj2dict(obj):
        "convert object attribs to dict"
        val = {}
        for key in obj._fields:
            val[key] = getattr(obj, key)
        return val

    pipe = subprocess.Popen(["uptime"], stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)
    upt = pipe.communicate()[0].split()
    pipe.wait(timeout=2)
    pipe = subprocess.Popen(["date"], stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)
    stats['time'] = pipe.communicate()[0]
    pipe.wait(timeout=2)
    stats['uptime'] = "%s %s" % (upt[2], upt[3].rstrip(','))
    stats['mem'] = _obj2dict(psutil.phymem_usage())
    stats['cpu'] = psutil.cpu_percent()
    stats['load'] = os.getloadavg()
    net = psutil.network_io_counters(True)
    infs = {}
    for inf in net:
        infs[inf] = _obj2dict(net[inf])
    stats['net'] = infs
    partitions = []
    for part in psutil.disk_partitions(all=False):
        usage = psutil.disk_usage(part.mountpoint)
        dpart = _obj2dict(part)
        dpart.update(_obj2dict(usage))
        partitions.append(dpart)
    stats['partitions'] = partitions
    stats['mta'] = get_processes('exim')
    stats['scanners'] = get_processes('MailScanner')
    stats['av'] = get_processes('clamd')
    return stats


@task(name="spamassassin-lint")
def salint():
    "Spamassassin lint"
    logger = salint.get_logger()
    logger.info("Running Spamassassin lint checks")
    lint = []
    saprefs = config.get('ms.saprefs',
            '/etc/MailScanner/spam.assassin.prefs.conf')

    pipe1 = subprocess.Popen(['spamassassin',
                            '-x',
                            '-D',
                            '-p',
                            saprefs,
                            '--lint'],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    while True:
        line = pipe1.stderr.readline()
        if not line:
            break
        lint.append(line)
    pipe1.wait(timeout=2)
    return lint


@task(name="get-bayes-info")
def bayesinfo():
    "Get bayes info"
    logger = bayesinfo.get_logger()
    logger.info("Generating Bayesian stats")
    info = {}
    saprefs = config.get(
                    'ms.saprefs',
                    '/etc/MailScanner/spam.assassin.prefs.conf'
                )

    pipe1 = subprocess.Popen(['sa-learn',
                            '-p',
                            saprefs,
                            '--dump',
                            'magic'],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    while True:
        line = pipe1.stdout.readline()
        if not line:
            break
        match = BAYES_INFO_RE.match(line)
        if match:
            if match.group(5) == 'bayes db version':
                info['version'] = match.group(3)
            elif match.group(5) == 'nspam':
                info['spam'] = match.group(3)
            elif match.group(5) == 'nham':
                info['ham'] = match.group(3)
            elif match.group(5) == 'ntokens':
                info['tokens'] = match.group(3)
            elif match.group(5) == 'oldest atime':
                info['otoken'] = datetime.datetime\
                                .fromtimestamp(float(match.group(3)))
            elif match.group(5) == 'newest atime':
                info['ntoken'] = datetime.datetime\
                                .fromtimestamp(float(match.group(3)))
            elif match.group(5) == 'last journal sync atime':
                info['ljournal'] = datetime.datetime\
                                .fromtimestamp(float(match.group(3)))
            elif match.group(5) == 'last expiry atime':
                info['expiry'] = datetime.datetime\
                                .fromtimestamp(float(match.group(3)))
            elif match.group(5) == 'last expire reduction count':
                info['rcount'] = match.group(3)
    pipe1.wait(timeout=2)
    return info


@task(name="preview-queued-msg")
def preview_queued_msg(msgid, direction, attachid=None, imgid=None):
    "Preview a queued message"
    try:
        logger = preview_queued_msg.get_logger()
        header = search_queue(msgid, int(direction))
        convertor = Exim2Mbox(header)
        mbox = convertor()
        msgfile = StringIO(mbox)
        previewer = PreviewMessage(msgfile)
        if attachid:
            logger.info("Download attachment: %(attachid)s of "
                        "message: %(id)s",
                        dict(id=msgid, attachid=attachid))
            return previewer.attachment(attachid)
        if imgid:
            logger.info("Image access: %(img)s", dict(img=imgid))
            return previewer.img(imgid)
        logger.info("Preview of message: %(id)s", dict(id=msgid))
        return previewer.preview()
    except TypeError, type_error:
        logger.info("Error occured: %s" % str(type_error))
        return {}
    except (AssertionError, IOError), error:
        logger.info("Accessing message: %(id)s, Failed: %(error)s",
        dict(id=msgid, error=error))
        return None
    finally:
        if 'msgfile' in locals():
            msgfile.close()


@task(name='process-queued-msgs', ignore_result=True)
def process_queued_msgs(msgids, action, direction, *args):
    "Process queued messages"
    try:
        logger = process_queued_msgs.get_logger()
        eximcmd = get_config_option('Sendmail2') if direction == 2 else 'exim'
        if not 'exim' in eximcmd:
            logger.info("Invalid exim command: %s" % eximcmd)
            return
        if direction == 1 and action not in ['bounce', 'delete']:
            logger.info("Invalid action: %s" % action)
            return
        exim_user = config.get('baruwa.mail.user', 'exim')
        queue = EximQueue('sudo -u %s %s' % (exim_user, eximcmd))
        func = getattr(queue, action)
        msgids = [msgid for msgid in msgids if EXIM_MSGID_RE.match(msgid)]
        func(msgids, *args)
        for result in queue.results:
            logger.info("STDOUT: %s" % result)
        if queue.errors:
            for errmsg in queue.errors:
                logger.info("STDERR: %s" % errmsg)
        pipe = subprocess.Popen(['/bin/hostname'],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
        hostname = pipe.communicate()[0]
        pipe.wait(timeout=10)
        hostname = hostname.strip()
        update_queue_stats(hostname)
    except TypeError, error:
        logger.info("Invalid input: %s" % error)
    except AttributeError:
        logger.info("Invalid action: %s" % action)
        

@task(name='update-audit-log', ignore_result=True)
def update_audit_log(username,
                    category,
                    info,
                    hostname,
                    remoteip,
                    timestamp=None):
    "Update the audit log"
    logger = update_audit_log.get_logger()
    try:
        entry = AuditLog(username,
                        category,
                        info,
                        hostname,
                        remoteip)
        if timestamp:
            entry.timestamp = timestamp
        Session.add(entry)
        Session.commit()
        logger.info("Audit Log update for: %s from: %s" %
                    (username, remoteip))
    except DatabaseError, err:
        logger.error("Audit Log FAILURE: %s %s %s %s %s %s Error: %s" %
                    (username,
                    category,
                    info,
                    hostname,
                    remoteip,
                    timestamp,
                    err))


def build_pdf(rows):
    "Build PDF"
    pdffile = StringIO()
    doc = BaruwaPDFTemplate(pdffile, topMargin=50, bottomMargin=18)
    import baruwa
    here = os.path.dirname(
                os.path.dirname(os.path.abspath(baruwa.__file__))
            )
    logo = os.path.join(here, 'baruwa', 'public', 'imgs', 'logo.png')
    img = Image(logo)
    logobj = [(img, _('Audit Log exported report'))]
    logo_table = Table(logobj, [2.0 * inch, 5.4 * inch])
    logo_table.setStyle(PIE_TABLE)
    parts = [logo_table]
    parts.append(Spacer(1, 20))
    parts.append(Paragraph(_('Audit Logs'), STYLES['Heading1']))
    heading = ((Paragraph(_('Date/Time'), STYLES["Heading6"]),
            Paragraph(_('Username'), STYLES["Heading6"]),
            Paragraph(_('Info'), STYLES["Heading6"]),
            Paragraph(_('Hostname'), STYLES["Heading6"]),
            Paragraph(_('Remote IP'), STYLES["Heading6"]),
            Paragraph(_('Action'), STYLES["Heading6"]),
            ))
    rows.insert(0, heading)
    table = Table(rows, [1.10 * inch, 1.23 * inch,
                        1.96 * inch, 1.69 * inch,
                        0.95 * inch, 0.45 * inch,])
    table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('FONT', (0, 0), (-1, -1), 'Helvetica'),
            ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.15, colors.black),
    ]))
    parts.append(table)
    doc.title = _('Baruwa Audit log export')
    doc.build(parts)
    return pdffile.getvalue()


@task(name='export-audit-log')
def export_auditlog(format, query):
    "Export the audit log"
    logger = export_auditlog.get_logger()
    filename = 'auditlog-%s.%s' % (export_auditlog.request.id, format)
    content_type = 'text/csv' if format == 'csv' else 'application/pdf'
    results = dict(id=export_auditlog.request.id,
                    f=None,
                    content_type=content_type,
                    filename=filename,
                    errormsg='')
    try:
        dbquery = Session.query(AuditLog)
        if query:
            conn = SphinxClient()
            conn.SetMatchMode(SPH_MATCH_EXTENDED2)
            conn.SetLimits(0, 500, 500)
            query = clean_sphinx_q(query)
            qresults = conn.Query(query, 'auditlog, auditlog_rt')
            if qresults and qresults['matches']:
                ids = [hit['id'] for hit in qresults['matches']]
                dbquery = dbquery.filter(AuditLog.id.in_(ids))

        dbquery = dbquery.order_by(desc('timestamp')).all()
        if format == 'pdf':
            PS = ParagraphStyle('auditlogp',
                                    fontName='Helvetica',
                                    fontSize=8,
                                    borderPadding =(2, 2, 2, 2))
            rows = [(Paragraph(item.timestamp.strftime('%Y-%m-%d %H:%M'), PS),
                    Paragraph(wrap_string(item.username, 27), PS),
                    Paragraph(wrap_string(item.info, 33), PS),
                    Paragraph(wrap_string(item.hostname, 27), PS),
                    Paragraph(wrap_string(item.remoteip, 15), PS),
                    Paragraph(CATEGORY_MAP[item.category], PS))
                    for item in dbquery]
            pdf = build_pdf(rows)
            results['f'] = pdf
        elif format == 'csv':
            rows = [item.tojson() for item in dbquery]
            keys = ('timestamp',
                    'username',
                    'info',
                    'hostname',
                    'remoteip',
                    'category')
            results['f'] = build_csv(rows, keys)
        logger.info("Audit Log export complete: %s" % results['filename'])
        return results
    except (DatabaseError), err:
        results['errormsg'] = str(err)
        logger.info("Audit Log export FAILURE: %s" % str(err))
        return results
        
