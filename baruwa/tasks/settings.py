# -*- coding: utf-8 -*-
# Baruwa - Web 2.0 MailScanner front-end.
# Copyright (C) 2010-2012  Andrew Colin Kissa <andrew@topdog.za.net>
# vim: ai ts=4 sts=4 et sw=4

"Settings tasks"

import os
import grp
import pwd
import base64

from pylons import config
from celery.task import task
from psutil import process_iter
from sqlalchemy.pool import NullPool
from eventlet.green import subprocess
from sqlalchemy import engine_from_config
from sqlalchemy.orm.exc import NoResultFound
from lxml.html import tostring, fragments_fromstring, iterlinks

from baruwa.model.meta import Session
from baruwa.model.domains import Domain
from baruwa.config.routing import make_map
from baruwa.model.accounts import User
from baruwa.model.settings import DomSignature, UserSignature
from baruwa.model.settings import UserSigImg, DomSigImg
from baruwa.model.settings import ConfigSettings
from baruwa.lib.outputformats import SignatureCleaner


if not Session.registry.has():
    engine = engine_from_config(config, 'sqlalchemy.', poolclass=NullPool)
    Session.configure(bind=engine)

UNCLEANTAGS = ['html', 'title', 'head', 'link', 'body', 'base']


def update_ms_serial(logger):
    """Update MS configuration serial"""
    try:
        msconf = Session.query(ConfigSettings)\
                .filter(ConfigSettings.internal == 'confserialnumber').one()
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


def write_html_sig(sigfile, sig, is_domain, logger):
    "write html sig"
    cleaner = SignatureCleaner(style=True,
                                remove_tags=UNCLEANTAGS,
                                safe_attrs_only=False)
    html = cleaner.clean_html(sig.signature_content)
    html = fragments_fromstring(html)[0]
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


@task(name="update-serial", ignore_result=True)
def update_serial():
    "update serial number task"
    logger = update_serial.get_logger()
    update_ms_serial(logger)


@task(name='save-domain-signature', ignore_result=True)
def save_dom_sig(sigid):
    "Save domain signature"
    logger = save_dom_sig.get_logger()
    try:
        logger.info('Processing domain signature: %s' % sigid)
        sign = Session.query(DomSignature)\
                .filter(DomSignature.id == sigid).one()
        domain = Session.query(Domain.name)\
                .filter(Domain.id == sign.domain_id).one()
        basedir = config.get('ms.signatures.base',
                    '/etc/MailScanner/baruwa/signatures')

        def mksigdir(sigfile):
            "create directory"
            logger.info('Creating signature directory for: %s' % domain.name)
            os.mkdir(os.path.dirname(sigfile))
            logger.info('Created: %s' % os.path.dirname(sigfile))

        if not sign.enabled:
            logger.info('Signature disabled, notifying scanner')
            update_ms_serial(logger)
            return

        if sign.signature_type == 1:
            #text
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
        else:
            #html
            sigfile = os.path.join(basedir, 'domains', domain.name, 'sig.html')
            if not os.path.exists(os.path.dirname(sigfile)):
                mksigdir(sigfile)
            write_html_sig(sigfile, sign, True, logger)
        update_ms_serial(logger)
    except NoResultFound:
        pass
    # finally:
    #     Session.close()


@task(name='save-user-signature', ignore_result=True)
def save_user_sig(sigid):
    "Save a user signature and associated images to filesystem"
    logger = save_user_sig.get_logger()
    try:
        logger.info('Processing user signature: %s' % sigid)
        sign = Session.query(UserSignature)\
                .filter(UserSignature.id == sigid).one()
        user = Session.query(User.username)\
                .filter(User.id == sign.user_id).one()
        basedir = config.get('ms.signatures.base',
                    '/etc/MailScanner/baruwa/signatures')

        def mksigdir(sigfile):
            "make directory"
            logger.info('Creating signature directory for: %s' % user.username)
            os.mkdir(os.path.dirname(sigfile))
            logger.info('Created: %s' % os.path.dirname(sigfile))

        if not sign.enabled:
            logger.info('Signature disabled, notifying scanner')
            update_ms_serial(logger)
            return

        if sign.signature_type == 1:
            #text
            sigfile = os.path.join(basedir, 'users', user.username, 'sig.txt')
            if not os.path.exists(os.path.dirname(sigfile)):
                mksigdir(sigfile)
            with open(sigfile, 'w') as handle:
                if not sign.signature_content.startswith('--'):
                    handle.write("\n--\n")
                handle.write(sign.signature_content)
                #os.write(handle, os.linesep)
                logger.info('Signature written to file: %s' % sigfile)
        else:
            #html
            sigfile = os.path.join(basedir, 'users', user.username, 'sig.html')
            if not os.path.exists(os.path.dirname(sigfile)):
                mksigdir(sigfile)
            write_html_sig(sigfile, sign, False, logger)
        update_ms_serial(logger)
    except NoResultFound:
        pass
    # finally:
    #     Session.close()


@task(name='delete-signature-files', ignore_result=True)
def delete_sig(files):
    "Delete a signature from filesystem"
    logger = delete_sig.get_logger()
    logger.info('Removing signature files')
    basedir = config.get('ms.signatures.base',
                '/etc/MailScanner/baruwa/signatures')
    for sig in files:
        try:
            if sig.startswith(basedir):
                os.unlink(sig)
                logger.info('Deleting: %s' % sig)
        except os.error:
            logger.info('Deleting failed: %s' % sig)


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
                pipe.wait(timeout=30)
                logger.info("Successfully signalled exim pid: %s %s %s" %
                            (str(process.pid), result, error))
                break
    except OSError, err:
        logger.info("Exim reload FAILED: %s" % str(err))

