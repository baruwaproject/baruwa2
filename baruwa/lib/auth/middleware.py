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
"""Baruwa authentication middleware overrides"""

import os
import sys
import logging

from repoze.who.config import WhoConfig
from paste.deploy.converters import asbool
from repoze.who.interfaces import IAuthenticator
from repoze.what.plugins.config import WhatConfig, _LEVELS
from repoze.what.middleware import AuthorizationMetadata
from repoze.who.classifiers import default_challenge_decider
from repoze.who.classifiers import default_request_classifier
from repoze.who.middleware import match_classification
from repoze.who.middleware import PluggableAuthenticationMiddleware
# from repoze.who.middleware import Identity, _ENDED, _STARTED, wrap_generator
# from repoze.who.middleware import match_classification, StartResponseWrapper
from repoze.who.plugins.testutil import AuthenticationForgerMiddleware


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
                log_stream = None,
                log_level = logging.INFO,
                remote_user_key = 'REMOTE_USER',
                ):
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

    # def __call__(self, environ, start_response):
    #     if self.remote_user_key in environ:
    #         return self.app(environ, start_response)
    # 
    #     path_info = environ.get('PATH_INFO', None)
    # 
    #     environ['repoze.who.plugins'] = self.name_registry
    #     environ['repoze.who.logger'] = self.logger
    #     environ['repoze.who.application'] = self.app
    # 
    #     self.log(_STARTED % path_info, 'info')
    #     classification = self.classifier(environ)
    #     self.log('request classification: %s' % classification, 'info')
    #     userid = None
    #     identity = None
    #     identifier = None
    # 
    #     ids = self.identify(environ, classification)
    # 
    #     if ids:
    #         auth_ids = self.authenticate(environ, classification, ids)
    # 
    #         if auth_ids:
    #             auth_ids.sort()
    #             best = auth_ids[0]
    #             rank, authenticator, identifier, identity, userid = best
    #             identity = Identity(identity)
    # 
    #             self.add_metadata(environ, classification, identity)
    # 
    #             environ['repoze.who.identity'] = identity
    #             environ[self.remote_user_key] = userid
    #             self.log(identity)
    #     else:
    #         self.log('no identities found, not authenticating', 'info')
    # 
    #     app = environ.pop('repoze.who.application')
    #     if  app is not self.app:
    #         self.log('static downstream application replaced with %s' % app,
    #                 'info')
    # 
    #     wrapper = StartResponseWrapper(start_response)
    #     app_iter = app(environ, wrapper.wrap_start_response)
    # 
    #     if not wrapper.called:
    #         app_iter = wrap_generator(app_iter)
    # 
    #     if self.challenge_decider(environ, wrapper.status, wrapper.headers):
    #         self.log('challenge required', 'info')
    # 
    #         challenge_app = self.challenge(
    #             environ,
    #             classification,
    #             wrapper.status,
    #             wrapper.headers,
    #             identifier,
    #             identity
    #             )
    #         if challenge_app is not None:
    #             self.log('executing challenge app', 'info')
    #             if app_iter:
    #                 list(app_iter)
    #             app_iter = challenge_app(environ, start_response)
    #         else:
    #             self.log('configuration error: no challengers', 'info')
    #             raise RuntimeError('no challengers found')
    #     else:
    #         self.log('no challenge required', 'info')
    #         remember_headers = []
    #         if identifier:
    #             remember_headers = identifier.remember(environ, identity)
    #             if remember_headers:
    #                 self.log('remembering via headers from %s: %s'
    #                         % (identifier, remember_headers), 'info')
    #         wrapper.finish_response(remember_headers)
    # 
    #     self.log(_ENDED % path_info, 'info')
    #     return app_iter

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
                        (rank, plugin, identifier, identity, userid)
                        )
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
                      log_stream = log_stream,
                      log_level = log_level,
                      remote_user_key = who_parser.remote_user_key,
                     )

