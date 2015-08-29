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
# pylint: disable=F0401
"""Baruwa authentication middleware overrides"""

import os
import sys
import logging

import zope.interface

from repoze.who.config import WhoConfig
from paste.deploy.converters import asbool
from repoze.what.plugins.config import WhatConfig, _LEVELS
from repoze.what.middleware import AuthorizationMetadata
from repoze.who.classifiers import default_challenge_decider
from repoze.who.classifiers import default_request_classifier
from repoze.who.middleware import match_classification
from repoze.who.interfaces import IAuthenticator, IChallengeDecider
from repoze.who.middleware import PluggableAuthenticationMiddleware
from repoze.who.plugins.testutil import AuthenticationForgerMiddleware


def baruwa_challenge_decider(environ, status, headers):
    """Baruwa Challenge Decider"""
    return status.startswith('401 ') and not \
            environ.get('REQUEST_URI', '').startswith('/api')
zope.interface.directlyProvides(baruwa_challenge_decider, IChallengeDecider)


class BaruwaPAM(PluggableAuthenticationMiddleware):
    """Override repoze.who.middleware:PluggableAuthenticationMiddleware
    """
    def __init__(self,
                app,
                identifiers,
                authenticators,
                challengers,
                mdproviders,
                classifier,
                challenge_decider,
                log_stream=None,
                log_level=logging.INFO,
                remote_user_key='REMOTE_USER'):
        PluggableAuthenticationMiddleware.__init__(self,
                app,
                identifiers,
                authenticators,
                challengers,
                mdproviders,
                classifier,
                challenge_decider,
                log_stream,
                log_level,
                remote_user_key)

    def authenticate(self, environ, classification, identities):
        """Override authenticate to return as soon as
        first authenticator passes
        """
        candidates = self.registry.get(IAuthenticator, [])
        self.log('authenticator plugins registered %s' %
                                    candidates, 'info')
        plugins = match_classification(IAuthenticator, candidates,
                                       classification)
        self.log('authenticator plugins matched for '
            'classification "%s": %s' % (classification, plugins), 'info')

        # 'preauthenticated' identities are considered best-ranking
        identities, results, id_rank_start = self._filter_preauthenticated(
            identities)

        # Stop wasting CPU circles return early we are already authenticated
        if results:
            self.log('userid: %s preauthenticated' % results[0][4])
            return results

        auth_rank = 0

        for plugin in plugins:
            if results:
                # Authenticated breakout
                self.log(
                    'userid: %s authenticated using %s '
                    'discontinuing futher plugin checks' %
                    (results[0][4], results[0][1]))
                break
            identifier_rank = id_rank_start
            for identifier, identity in identities:
                userid = plugin.authenticate(environ, identity)
                if userid is not None:
                    self.log('userid returned from %s: "%s"' %
                        (plugin, userid))

                    # stamp the identity with the userid
                    identity['repoze.who.userid'] = userid
                    user_dn = ''
                    try:
                        plugin_name = plugin.name
                        user_dn = identity['userdata']
                    except AttributeError:
                        plugin_name = str(plugin)
                    except KeyError:
                        pass
                    identity['tokens'] = [plugin_name, user_dn]
                    rank = (auth_rank, identifier_rank)
                    results.append(
                        (rank, plugin, identifier, identity, userid))
                else:
                    self.log('no userid returned from %s: (%s)' %
                        (plugin, userid))
                identifier_rank += 1
            auth_rank += 1

        self.log('identities authenticated: %s' % (results,))
        return results

    def log(self, msg, priority='debug'):
        "log message"
        if self.logger:
            logger = getattr(self.logger, priority)
            logger(msg)


def make_middleware(skip_authentication=False, *args, **kwargs):
    """Overide repoze.who.plugins.testutil:make_middleware
    """
    if asbool(skip_authentication):
        return AuthenticationForgerMiddleware(*args, **kwargs)
    else:
        return BaruwaPAM(*args, **kwargs)


def setup_auth(app, group_adapters=None, permission_adapters=None, **who_args):
    """Override repoze.what.middleware:setup_auth
    """
    authorization = AuthorizationMetadata(group_adapters,
                                          permission_adapters)

    if 'mdproviders' not in who_args:
        who_args['mdproviders'] = []

    who_args['mdproviders'].append(('authorization_md', authorization))

    if 'classifier' not in who_args:
        who_args['classifier'] = default_request_classifier

    if 'challenge_decider' not in who_args:
        who_args['challenge_decider'] = default_challenge_decider

    auth_log = os.environ.get('AUTH_LOG', '') == '1'
    if auth_log:
        who_args['log_stream'] = sys.stdout

    skip_authn = who_args.pop('skip_authentication', False)
    middleware = make_middleware(skip_authn, app, **who_args)
    return middleware


def make_middleware_with_config(app, global_conf, log_file=None):
    """Override repoze.what.plugins.config:make_middleware_with_config
    Allows us to call a Baruwa modified authentication stark and use
    single configuration file
    """
    who_parser = WhoConfig(global_conf['here'])
    who_parser.parse(open(global_conf['__file__']))
    what_parser = WhatConfig(global_conf['here'])
    what_parser.parse(open(global_conf['__file__']))
    log_level = 'DEBUG' if asbool(global_conf['debug']) else 'INFO'

    log_stream = None

    if log_file is not None:
        if log_file.lower() == 'stdout':
            log_stream = sys.stdout
        else:
            try:
                log_stream = open(log_file, 'wb')
            except IOError:
                log_stream = None

    if log_level is None:
        log_level = logging.INFO
    else:
        log_level = _LEVELS[log_level.lower()]

    return setup_auth(app,
                      group_adapters=what_parser.group_adapters,
                      permission_adapters=what_parser.permission_adapters,
                      identifiers=who_parser.identifiers,
                      authenticators=who_parser.authenticators,
                      challengers=who_parser.challengers,
                      mdproviders=who_parser.mdproviders,
                      classifier=who_parser.request_classifier,
                      challenge_decider=who_parser.challenge_decider,
                      log_stream=log_stream,
                      log_level=log_level,
                      remote_user_key=who_parser.remote_user_key)
