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

import os
import paste
import logging

from celery.app import app_or_default
from pylons import config as pylonsconfig
from paste.script.command import Command, BadCommand
from celery.bin import camqadm, celerybeat, celeryd, celeryev

__all__ = ['CeleryDaemonCommand', 'CeleryBeatCommand',
           'CAMQPAdminCommand', 'CeleryEventCommand']

log = logging.getLogger(__name__)


class BasePasterCommand(Command):
    """
    Abstract Base Class for paster commands.

    The celery commands are somewhat aggressive about loading
    celery.conf, and since our module sets the `CELERY_LOADER`
    environment variable to our loader, we have to bootstrap a bit and
    make sure we've had a chance to load the pylons config off of the
    command line, otherwise everything fails.
    """
    group_name = 'baruwa'
    min_args = 1
    min_args_error = "Please provide a paster config file as an argument."
    takes_config_file = 1
    requires_config_file = True

    def notify_msg(self, msg, log=False):
        """Make a notification to user, additionally if logger is passed
        it logs this action using given logger

        :param msg: message that will be printed to user
        :param log: logging instance, to use to additionally log this message
        """
        if log and isinstance(log, logging):
            log(msg)

    def run(self, args):
        """
        Overrides Command.run

        Checks for a config file argument and loads it.
        """
        if len(args) < self.min_args:
            raise BadCommand(
               self.min_args_error % {'min_args': self.min_args,
                                      'actual_args': len(args)})

        # Decrement because we're going to lob off the first argument.
        # @@ This is hacky
        self.min_args -= 1
        self.bootstrap_config(args[0])
        self.update_parser()
        return super(BasePasterCommand, self).run(args[1:])

    def update_parser(self):
        """
        Abstract method.  Allows for the class's parser to be updated
        before the superclass's `run` method is called.  Necessary to
        allow options/arguments to be passed through to the underlying
        celery command.
        """
        raise NotImplementedError("Abstract Method.")

    def bootstrap_config(self, conf):
        """
        Loads the pylons configuration.
        """

        path_to_ini_file = os.path.realpath(conf)
        conf = paste.deploy.appconfig('config:' + path_to_ini_file)
        pylonsconfig.init_app(conf.global_conf, conf.local_conf)


class CeleryCommand(BasePasterCommand):
    """Abstract class implements run methods needed for celery

    Starts the celery worker that uses a paste.deploy configuration
    file.
    """

    def update_parser(self):
        """
        Abstract method.  Allows for the class's parser to be updated
        before the superclass's `run` method is called.  Necessary to
        allow options/arguments to be passed through to the underlying
        celery command.
        """

        cmd = self.celery_command(app_or_default())
        for x in cmd.get_options():
            self.parser.add_option(x)

    def command(self):
        cmd = self.celery_command(app_or_default())
        return cmd.run(**vars(self.options))

class CeleryDaemonCommand(CeleryCommand):
    """Start the celery worker

    Starts the celery worker that uses a paste.deploy configuration
    file.
    """
    usage = 'CONFIG_FILE [celeryd options...]'
    summary = __doc__.splitlines()[0]
    description = "".join(__doc__.splitlines()[2:])

    parser = Command.standard_parser(quiet=True)
    celery_command = celeryd.WorkerCommand


class CeleryBeatCommand(CeleryCommand):
    """Start the celery beat server

    Starts the celery beat server using a paste.deploy configuration
    file.
    """
    usage = 'CONFIG_FILE [celerybeat options...]'
    summary = __doc__.splitlines()[0]
    description = "".join(__doc__.splitlines()[2:])

    parser = Command.standard_parser(quiet=True)
    celery_command = celerybeat.BeatCommand


class CAMQPAdminCommand(CeleryCommand):
    """CAMQP Admin

    CAMQP celery admin tool.
    """
    usage = 'CONFIG_FILE [camqadm options...]'
    summary = __doc__.splitlines()[0]
    description = "".join(__doc__.splitlines()[2:])

    parser = Command.standard_parser(quiet=True)
    celery_command = camqadm.AMQPAdminCommand

class CeleryEventCommand(CeleryCommand):
    """Celery event command.

    Capture celery events.
    """
    usage = 'CONFIG_FILE [celeryev options...]'
    summary = __doc__.splitlines()[0]
    description = "".join(__doc__.splitlines()[2:])

    parser = Command.standard_parser(quiet=True)
    celery_command = celeryev.EvCommand
