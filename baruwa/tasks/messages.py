# -*- coding: utf-8 -*-
# Baruwa - Web 2.0 MailScanner front-end.
# Copyright (C) 2010-2015  Andrew Colin Kissa <andrew@topdog.za.net>
# vim: ai ts=4 sts=4 et sw=4
"Messages tasks"
import time

from pylons import config
from celery.task import task
from sqlalchemy.pool import NullPool
from lxml.etree import Error as LXMLError
from sqlalchemy import engine_from_config
from paste.deploy.converters import asbool
from sqlalchemy.orm.exc import NoResultFound
from webhelpers.number import format_byte_size

from baruwa.model.meta import Session
from baruwa.lib.misc import gen_avail_mem
from baruwa.model.messages import Message, Release
from baruwa.lib.mail.message import ProcessQuarantinedMessage as PQM
from baruwa.lib.mail.message import PreviewMessage, search_quarantine


MEMLIMITS = {100: 2000000000, 50: 1000000000, 20: 500000000, 10: 250000000}


if not Session.registry.has():
    try:
        engine = engine_from_config(config, 'sqlalchemy.', poolclass=NullPool)
        Session.configure(bind=engine)
    except KeyError:
        pass


def check_mem(job, logger):
    """check if there is enough mem to execute task"""
    if 'issingle' in job and job['issingle']:
        return
    mem = gen_avail_mem()
    counter = 1
    msgid = job['message_id']
    memlimit = MEMLIMITS[job['num']]
    memlimits = format_byte_size(memlimit)
    while counter < 11:
        if mem < memlimit:
            logger.info("Deferring processing of: %(msgid)s "
                "%(avail)s available %(req)s required",
                dict(msgid=msgid, avail=format_byte_size(mem),
                    req=memlimits))
            if counter == 10:
                raise OSError("Insufficient memory")
        else:
            logger.info("Processing %(msgid)s: "
                "%(avail)s available %(req)s required",
                dict(msgid=msgid, avail=format_byte_size(mem),
                    req=memlimits))
            break
        time.sleep(30)
        mem = gen_avail_mem()
        counter += 1


def release(processor, job, result, logger):
    """Release message"""
    if job['from_address']:
        if job['use_alt']:
            to_addrs = job['altrecipients'].split(',')
        else:
            to_addrs = job['to_address'].split(',')
        result['release'] = processor.release(job['from_address'],
                                                        to_addrs)
        if not result['release']:
            error = ' '.join(processor.errors)
            result['errors'].append(('release', error))
            processor.reset_errors()
        else:
            logger.info("Message: %(msgid)s released to: %(to)s",
                        dict(msgid=job['message_id'],
                        to=', '.join(to_addrs)))
    else:
        result['release'] = False
        error = 'The sender address is empty'
        result['errors'].append(('release', error))
        logger.info("Message: %(msgid)s release failed with "
                    "error: %(error)s", dict(msgid=job['message_id'],
                    error=error))


def learn(processor, job, result, logger):
    """Learn message"""
    result['learn'] = processor.learn(job['salearn_as'])
    if not result['learn']:
        error = ' '.join(processor.errors)
        result['errors'].append(('learn', error))
        processor.reset_errors()
        logger.info("Message: %(msgid)s learning failed with "
                    "error: %(error)s", dict(msgid=job['message_id'],
                    error=error))
    else:
        logger.info("Message: %(msgid)s learnt as %(learn)s",
                    dict(msgid=job['message_id'],
                    learn=job['salearn_as']))


def delete(processor, job, result, logger):
    """Delete message"""
    result['delete'] = processor.delete()
    if not result['delete']:
        error = ' '.join(processor.errors)
        result['errors'].append(('delete', error))
        processor.reset_errors()
        logger.info("Message: %(msgid)s deleting failed with "
                    "error: %(error)s", dict(msgid=job['message_id'],
                    error=error))
    else:
        logger.info("Message: %(msgid)s deleted from quarantine",
        dict(msgid=job['message_id']))
        sql = Message.__table__\
                    .update()\
                    .where(Message.messageid == job['message_id'])\
                    .values(isquarantined=0)
        Session.bind.execute(sql)


def process_exception(exception, result, job, logger):
    """Process an exception"""
    for action in ['release', 'learn', 'todelete']:
        if job[action]:
            if action == 'todelete':
                action = 'delete'
            result[action] = False
            result['errors'].append((action, str(exception)))
            logger.info("Message: %(msgid)s process failed with "
                        "error: %(error)s", dict(msgid=job['message_id'],
                        error=str(exception)))


def process_message(job, logger):
    "Process a quarantined message"
    result = dict(message_id=job['message_id'],
                    mid=job['mid'],
                    date=job['date'],
                    from_address=job['from_address'],
                    to_address=job['to_address'],
                    release=None,
                    learn=None,
                    delete=None,
                    errors=[])
    try:
        msgfile, isdir = search_quarantine(job['date'], job['message_id'],
                                            job['msgfiles'])
        if not msgfile:
            raise OSError('Message not found')
        processor = PQM(msgfile, isdir, debug=asbool(config['debug']))
        if job['release']:
            # Mem zapping protection
            check_mem(job, logger)
            release(processor, job, result, logger)
        if job['learn']:
            # Mem zapping protection
            check_mem(job, logger)
            learn(processor, job, result, logger)
        if job['todelete']:
            delete(processor, job, result, logger)
        return result
    except OSError, exception:
        process_exception(exception, result, job, logger)
        return result


@task(name='release-message')
def release_message(messageid, date, from_addr, to_addr, msgfiles):
    "Release message"
    logger = release_message.get_logger()
    msgfile, isdir = search_quarantine(date, messageid, msgfiles)
    if not msgfile:
        return dict(success=False, error='Message not found')

    processor = PQM(msgfile, isdir, debug=asbool(config['debug']))
    if processor.release(from_addr, to_addr):
        logger.info("Message: %(id)s released to: %(addrs)s",
                    dict(id=messageid, addrs=','.join(to_addr)))
        retdict = dict(success=True, error='')
    else:
        logger.info("Message: %(id)s release failed", dict(id=messageid))
        retdict = dict(success=False, error=' '.join(processor.errors))
        processor.reset_errors()
    return retdict


@task(name='process-quarantined-msg')
def process_quarantined_msg(*args):
    'Process quarantined message'
    job = args[0]
    logger = process_quarantined_msg.get_logger()
    logger.info('Processing quarantined message: %(id)s',
                dict(id=job['message_id']))
    return process_message(job, logger)


# pylint: disable-msg=R0911
# pylint: disable-msg=R0913
# pylint: disable-msg=W0613
@task(name='preview-message')
def preview_msg(messageid, date, msgfiles, attachid=None,
        imgid=None, allowimgs=None):
    "Preview message"
    logger = preview_msg.get_logger()
    try:
        msgfile, _ = search_quarantine(date, messageid, msgfiles)
        previewer = PreviewMessage(msgfile)

        if attachid:
            logger.info("Download attachment: %(attachid)s of "
                        "message: %(id)s",
                        dict(id=messageid, attachid=attachid))
            return previewer.attachment(attachid)
        if imgid:
            logger.info("Image access: %(img)s", dict(img=imgid))
            return previewer.img(imgid)
        logger.info("Preview of message: %(id)s", dict(id=messageid))
        return previewer.preview()
    except IOError, error:
        logger.info("Accessing message: %(id)s, Failed: %(error)s",
                    dict(id=messageid, error=error))
        return {}
    except TypeError, error:
        logger.info("Accessing message: %(id)s, Failed: %(error)s",
                    dict(id=messageid, error=error))
        return {}
    except LXMLError, error:
        logger.info("Accessing message: %(id)s, Failed: %(error)s",
                    dict(id=messageid, error=error))
        return {}
    except AssertionError, error:
        logger.info("Accessing message: %(id)s, Failed: %(error)s",
                    dict(id=messageid, error=error))
        return None


@task(name='update-auto-release-record', ignore_result=True)
def update_autorelease(msg_uuid):
    "Update the autorelease link record"
    logger = update_autorelease.get_logger()
    try:
        record = Session.query(Release)\
                .filter(Release.uuid == msg_uuid)\
                .one()
        record.released = True
        Session.add(record)
        Session.commit()
        logger.info("Auto Release record: %s updated" % msg_uuid)
    except NoResultFound:
        logger.info("Release Record: %s not found" % msg_uuid)
    finally:
        Session.close()
