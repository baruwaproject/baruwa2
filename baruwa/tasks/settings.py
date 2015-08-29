# -*- coding: utf-8 -*-
# Baruwa - Web 2.0 MailScanner front-end.
# Copyright (C) 2010-2015  Andrew Colin Kissa <andrew@topdog.za.net>
# vim: ai ts=4 sts=4 et sw=4

"Settings tasks"

import os
import grp
import pwd
import base64
import shutil

from pylons import config
from celery.task import task
from psutil import process_iter
from sqlalchemy.sql import text
from sqlalchemy.pool import NullPool
from eventlet.green import subprocess
from sqlalchemy.exc import DatabaseError
from sqlalchemy import desc, create_engine
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql.expression import false, true
from sqlalchemy import engine_from_config, and_, func
from lxml.html import tostring, fragments_fromstring, iterlinks

from baruwa.model.lists import List
from baruwa.model.meta import Session
from baruwa.lib.templates import render
from baruwa.model.domains import Domain
from baruwa.model.messages import SARule
from baruwa.config.routing import make_map
from baruwa.lib.regex import MSRULE_RE, dbval
from baruwa.model.accounts import User, Relay
from baruwa.lib.outputformats import SignatureCleaner
from baruwa.lib import POLICY_FILE_MAP, POLICY_SETTINGS_MAP
from baruwa.model.settings import DomSignature, UserSignature, Policy
from baruwa.model.settings import UserSigImg, DomSigImg, DomainPolicy
from baruwa.model.settings import ConfigSettings, Rule, PolicySettings


if not Session.registry.has():
    try:
        ENG = engine_from_config(config, 'sqlalchemy.', poolclass=NullPool)
        Session.configure(bind=ENG)
    except KeyError:
        pass

UNCLEANTAGS = ['html', 'title', 'head', 'link', 'body', 'base']


def column_windows(session, column, windowsize):
    """Return a series of WHERE clauses against
    a given column that break it into windows.

    Result is an iterable of tuples, consisting of
    ((start, end), whereclause), where (start, end) are the ids.
    """

    def int_for_range(start_id, end_id):
        "create a range"
        if end_id:
            return and_(column >= start_id, column < end_id)
        else:
            return column >= start_id

    qry = session.query(column,
                func.row_number().
                        over(order_by=column).
                        label('rownum')
                        ).from_self(column)

    if windowsize > 1:
        qry = qry.filter("rownum %% %d=1" % windowsize)

    intervals = [qid for qid, in qry]

    while intervals:
        start = intervals.pop(0)
        if intervals:
            end = intervals[0]
        else:
            end = None
        yield int_for_range(start, end)


def windowed_query(qry, column, windowsize):
    """"Break a Query into windows on a given column."""
    for whereclause in column_windows(qry.session, column, windowsize):
        for row in qry.filter(whereclause).order_by(column):
            yield row


def update_ms_serial(logger):
    """Update MS configuration serial"""
    try:
        msconf = Session.query(ConfigSettings)\
                .filter(ConfigSettings.internal == u'confserialnumber').one()
        msconf.value = int(msconf.value) + 1
    except NoResultFound:
        msconf = ConfigSettings(
                'confserialnumber',
                'ConfSerialNumber',
                0)
        msconf.value = 1
        msconf.server_id = 1
    Session.add(msconf)
    Session.commit()
    # Session.close()
    logger.info('Scanner serial number updated: %s' % str(msconf.value))


# pylint: disable-msg=R0914
def write_html_sig(sigfile, sig, is_domain, logger):
    "write html sig"
    cleaner = SignatureCleaner(style=True,
                                remove_tags=UNCLEANTAGS,
                                safe_attrs_only=False)
    html = cleaner.clean_html(sig.signature_content)
    html = fragments_fromstring(html)[0]
    # pylint: disable-msg=W0612
    for element, attribute, link, pos in iterlinks(html):
        if link.startswith('/fm/'):
            logger.info('Found img link, processing')
            routemap = make_map(config)
            routeargs = routemap.match(link)
            if not routeargs:
                continue
            if is_domain:
                model = DomSigImg
            else:
                model = UserSigImg
            img = Session.query(model)\
                .filter(model.id == routeargs['imgid']).one()
            element.attrib['src'] = 'cid:%s' % img.name
            imgfile = os.path.join(os.path.dirname(sigfile), img.name)
            with open(imgfile, 'wb') as handle:
                handle.write(base64.decodestring(img.image))
            logger.info('%s: stored to filesystem at: %s.' %
                        (img.name, imgfile))
            sig.image.append(img)
    if 'link' in locals():
        Session.add(sig)
        Session.commit()
        # Session.close()
    with open(sigfile, 'w') as handle:
        if not sig.signature_content.startswith('--'):
            handle.write('<br/>--<br/>')
        handle.write(tostring(html))
    logger.info('Finished processing HTML signature: %s' % sigfile)


def create_local_table(conn):
    """Create the sqlite tables"""
    initial_sql = """CREATE TABLE IF NOT EXISTS quickpeek
    (
    id INT PRIMARY KEY,
    rank INT,
    internal TEXT,
    external TEXT,
    hostname TEXT,
    value TEXT
    )
    """
    index1 = "CREATE INDEX internal_idx ON quickpeek(internal)"
    index2 = "CREATE INDEX external_idx ON quickpeek(external)"
    try:
        conn.execute(initial_sql)
        conn.execute(index1)
        conn.execute(index2)
    except DatabaseError:
        pass


def make_connection():
    """Make a connection to the SQLite DB"""
    change_owner = False
    dbdir = config.get('cache_dir', '/var/lib/baruwa/data')
    dbdir = os.path.join(dbdir, 'db')
    dbfile = os.path.join(dbdir, 'baruwa2.db')
    if not os.path.exists(dbfile):
        change_owner = True
    eng = create_engine('sqlite:///%s' % dbfile)
    conn = eng.connect()
    if change_owner:
        uid = pwd.getpwnam("baruwa").pw_uid
        gid = grp.getgrnam("exim").gr_gid
        try:
            os.chown(dbfile, uid, gid)
            create_local_table(conn)
        except OSError:
            pass
    return conn


@task(name="update-serial", ignore_result=True)
def update_serial():
    "update serial number task"
    logger = update_serial.get_logger()
    update_ms_serial(logger)


# pylint: disable-msg=R0912
@task(name='save-domain-signature', ignore_result=True)
def save_dom_sig(sigid):
    "Save domain signature"
    logger = save_dom_sig.get_logger()
    try:
        logger.info('Processing domain signature: %s' % sigid)
        sign = Session.query(DomSignature)\
                .filter(DomSignature.id == sigid).one()
        domain = Session.query(Domain)\
                .filter(Domain.id == sign.domain_id).one()
        basedir = config.get('ms.signatures.base',
                    '/etc/MailScanner/baruwa/signatures')

        def mksigdir(sigfile):
            "create directory"
            logger.info('Creating signature directory for: %s' % domain.name)
            os.mkdir(os.path.dirname(sigfile))
            logger.info('Created: %s' % os.path.dirname(sigfile))

        def mksymlinks(domname):
            "Create symlinked directories"
            domdr = os.path.join(basedir, 'domains', domname.name)
            for alias in domname.aliases:
                linkdr = os.path.join(basedir, 'domains', alias.name)
                if not os.path.exists(linkdr):
                    os.symlink(domdr, linkdr)
                    logger.info('Created symlink: %s' % linkdr)

        if not sign.enabled:
            logger.info('Signature disabled, notifying scanner')
            update_ms_serial(logger)
            return

        if sign.signature_type == 1:
            # text
            sigfile = os.path.join(basedir, 'domains', domain.name, 'sig.txt')
            print sigfile
            print os.path.dirname(sigfile)
            if not os.path.exists(os.path.dirname(sigfile)):
                mksigdir(sigfile)
            with open(sigfile, 'w') as handle:
                if not sign.signature_content.startswith('--'):
                    handle.write("\n--\n")
                handle.write(sign.signature_content)
                logger.info('Signature written to file: %s' % sigfile)
            mksymlinks(domain)
        else:
            # html
            sigfile = os.path.join(basedir, 'domains', domain.name, 'sig.html')
            if not os.path.exists(os.path.dirname(sigfile)):
                mksigdir(sigfile)
            write_html_sig(sigfile, sign, True, logger)
            mksymlinks(domain)
        update_ms_serial(logger)
    except NoResultFound:
        pass
    finally:
        Session.close()


@task(name='save-user-signature', ignore_result=True)
def save_user_sig(sigid):
    "Save a user signature and associated images to filesystem"
    logger = save_user_sig.get_logger()
    try:
        logger.info('Processing user signature: %s' % sigid)
        sign = Session.query(UserSignature)\
                .filter(UserSignature.id == sigid).one()
        user = Session.query(User)\
                .filter(User.id == sign.user_id).one()
        basedir = config.get('ms.signatures.base',
                    '/etc/MailScanner/baruwa/signatures')

        def mksigdir(sigfile):
            "make directory"
            logger.info('Creating signature directory for: %s' % user.username)
            os.mkdir(os.path.dirname(sigfile))
            logger.info('Created: %s' % os.path.dirname(sigfile))

        def mksymlinks(usrname):
            "Create symlinked directories"
            usrdir = os.path.join(basedir, 'users', usrname.username)
            for addr in usrname.addresses:
                linkdr = os.path.join(basedir, 'users', addr.address)
                if not os.path.exists(linkdr):
                    os.symlink(usrdir, linkdr)
                    logger.info('Created symlink: %s' % linkdr)

        if not sign.enabled:
            logger.info('Signature disabled, notifying scanner')
            update_ms_serial(logger)
            return

        if sign.signature_type == 1:
            # text
            sigfile = os.path.join(basedir, 'users', user.username, 'sig.txt')
            if not os.path.exists(os.path.dirname(sigfile)):
                mksigdir(sigfile)
            with open(sigfile, 'w') as handle:
                if not sign.signature_content.startswith('--'):
                    handle.write("\n--\n")
                handle.write(sign.signature_content)
                # os.write(handle, os.linesep)
                logger.info('Signature written to file: %s' % sigfile)
            mksymlinks(user)
        else:
            # html
            sigfile = os.path.join(basedir, 'users', user.username, 'sig.html')
            if not os.path.exists(os.path.dirname(sigfile)):
                mksigdir(sigfile)
            write_html_sig(sigfile, sign, False, logger)
            mksymlinks(user)
        update_ms_serial(logger)
    except NoResultFound:
        pass
    finally:
        Session.close()


@task(name='delete-signature-files', ignore_result=True)
def delete_sig(files):
    "Delete a signature from filesystem"
    logger = delete_sig.get_logger()
    logger.info('Removing signature files')
    basedir = config.get('ms.signatures.base',
                '/etc/MailScanner/baruwa/signatures')
    # delete files first
    for sig in files:
        try:
            if sig.startswith(basedir) and os.path.isfile(sig):
                os.unlink(sig)
                logger.info('Deleting file: %s' % sig)
        except os.error:
            logger.info('Deleting file: %s failed' % sig)
    # delete directories
    for sig in files:
        try:
            if sig.startswith(basedir):
                os.unlink(sig)
                logger.info('Deleting directory: %s' % sig)
        except os.error:
            logger.info('Deleting directory: %s failed' % sig)


@task(name='save-dkim-key', ignore_result=True)
def save_dkim_key(name, priv_key):
    "Save DKIM keys for a domain"
    try:
        logger = save_dkim_key.get_logger()
        logger.info("Store DKIM key for: %s" % name)
        dkimdir = config.get('baruwa.dkim.dir',
                    '/etc/MailScanner/baruwa/dkim')
        keyfile = os.path.join(dkimdir, "%s.pem" % name)
        with open(keyfile, 'w') as handle:
            handle.write(priv_key)
        os.chmod(keyfile, 0640)
        uid = pwd.getpwnam("baruwa").pw_uid
        gid = grp.getgrnam("exim").gr_gid
        os.chown(keyfile, uid, gid)
        logger.info('Stored DKIM key to %s' % keyfile)
    except OSError:
        logger.info("Storing DKIM keys for: %s failed" % name)


@task(name='delete-dkim-key', ignore_result=True)
def delete_dkim_key(name):
    "Delete DKIM key for a domain"
    try:
        logger = save_dkim_key.get_logger()
        logger.info("Remove DKIM key for: %s" % name)
        dkimdir = config.get('baruwa.dkim.dir',
                    '/etc/MailScanner/baruwa/dkim')
        keyfile = os.path.join(dkimdir, "%s.pem" % name)
        os.unlink(keyfile)
        logger.info("Removed DKIM key: %s" % keyfile)
    except OSError:
        logger.info("Removal of key: %s failed" % keyfile)


@task(name='reload-exim', ignore_result=True)
def reload_exim():
    "Reload outbound exim"
    logger = reload_exim.get_logger()
    try:
        for process in process_iter():
            if process.name != 'exim':
                continue
            if '/etc/exim/exim_out.conf' in process.cmdline:
                logger.info("Sending HUP signal to exim pid: %s" %
                            str(process.pid))
                # process.send_signal(SIGHUP)
                cmd = ['sudo', '/bin/kill', '-s', 'HUP', str(process.pid)]
                pipe = subprocess.Popen(cmd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
                error, result = pipe.communicate()
                # pylint: disable-msg=E1123
                pipe.wait(timeout=30)
                logger.info("Successfully signalled exim pid: %s %s %s" %
                            (str(process.pid), result, error))
                break
    except OSError, err:
        logger.info("Exim reload FAILED: %s" % str(err))


def write_ruleset(filename, template_vars, template=None):
    "Generate a MS ruleset file"
    def get_lines(file_name):
        "Generator to save memory"
        with open(file_name) as local_file:
            for line in local_file:
                yield line
    if template:
        # pylint: disable-msg=W0142
        content = render('/mailscanner/%s' % template, **template_vars)
    else:
        # pylint: disable-msg=W0142
        content = render('/mailscanner/%s' % filename, **template_vars)
    base = config.get('ms.config', '/etc/MailScanner/MailScanner.conf')
    cache_dir = config.get('cache_dir', '/var/lib/baruwa/data')
    dest = os.path.join(os.path.dirname(base), 'baruwa', 'rules',
                        filename)
    tmp = os.path.join(cache_dir, 'templates', 'mailscanner', filename)
    with open(tmp, 'w') as handle:
        pre = os.path.join(os.path.dirname(dest), '%s.local' % filename)
        if os.path.exists(pre):
            for line in get_lines(pre):
                handle.write(line)
            handle.flush()
        handle.write(content)
        handle.flush()
    shutil.copy(tmp, dest)


@task(name='create-sign-clean', ignore_result=True)
def create_sign_clean():
    "Generate the sign clean ruleset"
    usersql = """SELECT users.email, '' as address  FROM users,
                user_signatures WHERE users.active = 't'
                AND users.id=user_signatures.user_id
                AND user_signatures.enabled='t' AND
                user_signatures.signature_type = 1
                UNION
                SELECT users.email, addresses.address
                FROM users,addresses, user_signatures
                WHERE users.id=addresses.user_id
                AND users.id=user_signatures.user_id AND
                addresses.enabled='t' AND
                user_signatures.enabled='t' AND
                user_signatures.signature_type = 1
                """
    domainsql = """SELECT name FROM alldomains,
                domain_signatures WHERE alldomains.id =
                domain_signatures.domain_id AND
                alldomains.status='t' AND
                domain_signatures.enabled='t' AND
                domain_signatures.signature_type = 1
                """
    users = Session.execute(usersql)
    domains = Session.execute(domainsql)
    kwargs = dict(users=users, domains=domains)
    write_ruleset('sign.clean.msgs.rules', kwargs)
    Session.close()


def get_sig_data(sigtype):
    "Get signature data"
    usersql = """SELECT users.username, users.email, ''
                AS address  FROM users,
                user_signatures WHERE users.active = 't'
                AND users.id=user_signatures.user_id
                AND user_signatures.enabled='t' AND
                user_signatures.signature_type = :sigtype
                UNION
                SELECT users.username, users.email,
                addresses.address FROM users,addresses,
                user_signatures WHERE users.id=addresses.user_id
                AND users.id=user_signatures.user_id AND
                addresses.enabled='t' AND
                user_signatures.enabled='t' AND
                user_signatures.signature_type = :sigtype
                """
    domainsql = """SELECT name FROM alldomains,
                domain_signatures WHERE alldomains.id =
                domain_signatures.domain_id AND
                alldomains.status='t' AND
                domain_signatures.enabled='t' AND
                domain_signatures.signature_type = :sigtype
                """
    users = Session.execute(usersql, params=dict(sigtype=sigtype))
    domains = Session.execute(domainsql, params=dict(sigtype=sigtype))
    kwargs = dict(users=users, domains=domains)
    return kwargs


@task(name='create-html-sigs', ignore_result=True)
def create_html_sigs():
    "Create HTML signatures ruleset"
    kwargs = get_sig_data(2)
    write_ruleset('html.sigs.rules', kwargs)
    Session.close()


@task(name='create-text-sigs', ignore_result=True)
def create_text_sigs():
    "Create TEXT signatures ruleset"
    kwargs = get_sig_data(1)
    write_ruleset('text.sigs.rules', kwargs)
    Session.close()


def get_sig_img_data():
    "Get signatures data"
    usersql = """SELECT users.username, users.email, ''
                AS address, user_sigimgs.name AS img FROM
                users, user_sigimgs WHERE users.id =
                user_sigimgs.user_id AND users.active='t'
                UNION
                SELECT users.username, users.email,
                addresses.address, user_sigimgs.name AS img
                FROM users, addresses, user_sigimgs
                WHERE users.id = addresses.user_id AND
                users.id = user_sigimgs.user_id AND
                addresses.enabled='t' AND users.active='t'
                """
    domainsql = """SELECT alldomains.name, dom_sigimgs.name
                AS img FROM alldomains, dom_sigimgs WHERE
                alldomains.id = dom_sigimgs.domain_id
                AND alldomains.status='t'
                """
    users = Session.execute(usersql)
    domains = Session.execute(domainsql)
    kwargs = dict(users=users, domains=domains)
    return kwargs


@task(name='create-sig-imgs', ignore_result=True)
def create_sig_imgs():
    "Create signature images ruleset"
    kwargs = get_sig_img_data()
    write_ruleset('sig.imgs.rules', kwargs)
    Session.close()


@task(name='create-sig-img-names', ignore_result=True)
def create_sig_img_names():
    "Create signature image names ruleset"
    kwargs = get_sig_img_data()
    write_ruleset('sig.imgs.names.rules', kwargs)
    Session.close()


@task(name='create-spam-checks', ignore_result=True)
def create_spam_checks():
    "Generate file based spam checks ruleset"
    users_q = Session.query(User).filter(User.spam_checks == false())
    users = windowed_query(users_q, User.id, 100)
    domains = Session.query(Domain).filter(Domain.spam_checks == false()).all()
    kwargs = dict(users=users, domains=domains)
    write_ruleset('spam.checks.rules', kwargs)
    Session.close()


@task(name='create-virus-checks', ignore_result=True)
def create_virus_checks():
    "Generate file based virus checks ruleset"
    domains = Session.query(Domain)\
                    .filter(and_(Domain.virus_checks == true(),
                            Domain.virus_checks_at_smtp == false()))\
                    .all()
    kwargs = dict(domains=domains)
    write_ruleset('virus.checks.rules', kwargs)
    Session.close()


@task(name='create-spam-actions', ignore_result=True)
def create_spam_actions():
    "Generate file based spam actions ruleset"
    hosts = Session.query(Relay.address, Relay.spam_actions)\
                    .filter(Relay.address != u'')\
                    .filter(Relay.spam_actions != 2)\
                    .distinct(Relay.address).all()
    domains = Session.query(Domain).filter(Domain.spam_actions != 2).all()
    kwargs = dict(domains=domains, hosts=hosts)
    write_ruleset('spam.actions.rules', kwargs)
    Session.close()


@task(name='create-highspam-actions', ignore_result=True)
def create_highspam_actions():
    "Generate file based highspam actions ruleset"
    hosts = Session.query(Relay.address, Relay.highspam_actions)\
                    .filter(Relay.address != u'')\
                    .filter(Relay.highspam_actions != 2)\
                    .distinct(Relay.address).all()
    domains = Session.query(Domain).filter(Domain.highspam_actions != 2).all()
    kwargs = dict(domains=domains, hosts=hosts)
    write_ruleset('highspam.actions.rules', kwargs)
    Session.close()


@task(name='create-spam-scores', ignore_result=True)
def create_spam_scores():
    "Generate file based spam scores ruleset"
    users_q = Session.query(User).filter(User.low_score > 0)
    users = windowed_query(users_q, User.id, 100)
    domains = Session.query(Domain).filter(Domain.low_score > 0).all()
    hosts = Session.query(Relay.address, Relay.low_score)\
                    .filter(Relay.low_score > 0)\
                    .filter(Relay.address != u'')\
                    .distinct(Relay.address).all()
    kwargs = dict(domains=domains, users=users, hosts=hosts)
    write_ruleset('spam.score.rules', kwargs)
    Session.close()


@task(name='create-highspam-scores', ignore_result=True)
def create_highspam_scores():
    "Generate file based highspam scores ruleset"
    users_q = Session.query(User).filter(User.high_score > 0)
    users = windowed_query(users_q, User.id, 100)
    domains = Session.query(Domain).filter(Domain.high_score > 0).all()
    hosts = Session.query(Relay.address, Relay.high_score)\
                    .filter(Relay.high_score > 0)\
                    .filter(Relay.address != u'')\
                    .distinct(Relay.address).all()
    kwargs = dict(domains=domains, users=users, hosts=hosts)
    write_ruleset('highspam.score.rules', kwargs)
    Session.close()


def get_list_data(list_type):
    "Return lists"
    # email to any
    email2any = Session.query(List).filter(List.list_type == list_type)\
                .filter(List.from_addr_type == 1)\
                .filter(List.to_address == u'any')
    email2any = windowed_query(email2any, List.id, 500)
    # non email to any
    nonemail2any = Session.query(List).filter(List.list_type == list_type)\
                .filter(List.from_addr_type != 1)\
                .filter(List.to_address == u'any')
    nonemail2any = windowed_query(nonemail2any, List.id, 500)
    # email to non any
    email2nonany = Session.query(List).filter(List.list_type == list_type)\
                .filter(List.from_addr_type == 1)\
                .filter(List.to_address != u'any')
    email2nonany = windowed_query(email2nonany, List.id, 500)
    # nonemail to non any
    nonemail2nonany = Session.query(List).filter(List.list_type == list_type)\
                .filter(List.from_addr_type != 1)\
                .filter(List.to_address != u'any')
    nonemail2nonany = windowed_query(nonemail2nonany, List.id, 500)
    kwargs = dict(email2any=email2any, nonemail2any=nonemail2any,
                email2nonany=email2nonany, nonemail2nonany=nonemail2nonany)
    return kwargs


@task(name='create-lists', ignore_result=True)
def create_lists(list_type):
    "Generate Approved and banned lists"
    if list_type == 1:
        # create approve
        kwargs = get_list_data(1)
        write_ruleset('approved.senders.rules', kwargs)
    if list_type == 2:
        # create banned
        kwargs = get_list_data(2)
        write_ruleset('banned.senders.rules', kwargs)
    Session.close()


@task(name='create-message-size-rules', ignore_result=True)
def create_message_size():
    "Generate file based message size ruleset"
    domains = Session.query(Domain).filter(Domain.message_size != u'0').all()
    kwargs = dict(domains=domains)
    write_ruleset('message.size.rules', kwargs)
    Session.close()


@task(name='create-report-language-rules', ignore_result=True)
def create_language_based():
    "Generate file base language ruleset"
    domains = Session.query(Domain).filter(Domain.language != u'en').all()
    kwargs = dict(domains=domains)
    write_ruleset('languages.rules', kwargs)
    write_ruleset('rejectionreport.rules', kwargs)
    write_ruleset('deletedcontentmessage.rules', kwargs)
    write_ruleset('deletedfilenamemessage.rules', kwargs)
    write_ruleset('deletedvirusmessage.rules', kwargs)
    write_ruleset('deletedsizemessage.rules', kwargs)
    write_ruleset('storedcontentmessage.rules', kwargs)
    write_ruleset('storedfilenamemessage.rules', kwargs)
    write_ruleset('storedvirusmessage.rules', kwargs)
    write_ruleset('storedsizemessage.rules', kwargs)
    write_ruleset('disinfectedreport.rules', kwargs)
    write_ruleset('inlinewarninghtml.rules', kwargs)
    write_ruleset('inlinewarningtxt.rules', kwargs)
    write_ruleset('sendercontentreport.rules', kwargs)
    write_ruleset('sendererrorreport.rules', kwargs)
    write_ruleset('senderfilenamereport.rules', kwargs)
    write_ruleset('sendervirusreport.rules', kwargs)
    write_ruleset('sendersizereport.rules', kwargs)
    write_ruleset('senderspamreport.rules', kwargs)
    write_ruleset('senderspamrblreport.rules', kwargs)
    write_ruleset('senderspamsareport.rules', kwargs)
    write_ruleset('inlinespamwarning.rules', kwargs)
    write_ruleset('recipientspamreport.rules', kwargs)
    Session.close()


@task(name='get-ruleset-data')
def get_ruleset(rulesetfile):
    """Return the contents of a ms ruleset"""
    data = []
    logger = get_ruleset.get_logger()

    def process_line(line):
        """Process a file line"""
        if line == '\n' or line.startswith('#'):
            return
        match = MSRULE_RE.match(line)
        if match:
            data.append(match.groupdict())
        else:
            logger.error('File: %s Line not matched: %s' %
                        (rulesetfile, line))
    logger.info('Processing ruleset file: %s' % rulesetfile)
    for line in open(rulesetfile):
        process_line(line)
    logger.info('Found %d entries in ruleset file: %s' %
                (len(data), rulesetfile))
    if data:
        data.reverse()
    return data


@task(name='create-content-protection-rules', ignore_result=True)
def create_content_rules(policy_id, policy_name, remove=None):
    """Create content rules"""
    filename = "%s.conf" % policy_name
    if remove:
        base = config.get('ms.config', '/etc/MailScanner/MailScanner.conf')
        dest = os.path.join(os.path.dirname(base), 'baruwa', 'rules',
                            filename)
        if os.path.exists(dest):
            os.unlink(dest)
    else:
        rules = Session.query(Rule)\
                        .filter(Rule.policy_id == policy_id)\
                        .filter(Rule.enabled == true())\
                        .order_by(desc('ordering'))\
                        .all()
        if rules:
            kwargs = dict(rules=rules)
            write_ruleset(filename, kwargs, 'content.protection.rules')


@task(name='create-content-protection-ruleset', ignore_result=True)
def create_content_ruleset():
    """Create content ruleset"""
    def set_attrs(obj, dom=None):
        """Set attrs"""
        for key in POLICY_SETTINGS_MAP:
            attr = POLICY_SETTINGS_MAP[key]
            value = getattr(obj, attr)
            if value != 0:
                policy = Session.query(Policy.name)\
                                .filter(Policy.id == value)\
                                .one()
                setattr(obj, '%s-name' % attr, "%s.conf" % policy.name)
        if dom:
            setattr(obj, 'domain_name', dom.name)
            setattr(obj, 'domain_aliases', dom.aliases)
            return obj
    global_policy = Session.query(PolicySettings).get(1)
    set_attrs(global_policy)
    dpsq = Session.query(DomainPolicy, Domain)\
                    .filter(DomainPolicy.domain_id == Domain.id)\
                    .filter(Domain.status == true())
    domain_policies = [set_attrs(dps[0], dps[1]) for dps in dpsq]
    for policy_type in [1, 2, 3, 4]:
        kwargs = dict(gps=global_policy,
                        dps=domain_policies,
                        policy_type=POLICY_SETTINGS_MAP[policy_type],
                        default="%s.conf" % POLICY_FILE_MAP[policy_type])
        write_ruleset(POLICY_FILE_MAP[policy_type],
                        kwargs, 'content.protection.ruleset')


@task(name='create-local-scores', ignore_result=True)
def create_local_scores():
    """Create local scores"""
    scores_q = Session.query(SARule)\
            .filter(SARule.local_score != 0)\
            .filter(SARule.local_score != SARule.score)
    scores = windowed_query(scores_q, SARule.id, 50)
    kwargs = dict(scores=scores)
    write_ruleset('local.scores', kwargs, 'localscores.rules')
    Session.close()


@task(name='create-local-settings', ignore_result=True)
def create_ms_settings():
    """Create MS local SETTINGS_MAP"""
    sql = text("""SELECT * FROM quickpeek""")
    proxy = Session.execute(sql)
    params = [dict(rank=row.rank,
            internal=row.internal,
            external=row.external,
            hostname=row.hostname,
            value=dbval(row.value))
            for row in proxy]
    conn = make_connection()
    insert_sql = text("""INSERT INTO quickpeek
    (rank, internal, external, hostname, value)
    VALUES(:rank, :internal, :external, :hostname, :value)
    """)
    conn.execute(text("DELETE FROM quickpeek"))
    conn.execute(insert_sql, params)
