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
"Updates the Spamassassin rule descriptions"
import os
import sys

from sqlalchemy.orm.exc import NoResultFound

from baruwa.model.messages import SARule
from baruwa.model.meta import Session
from baruwa.commands import BaseCommand
from baruwa.lib.regex import RULE_DESCRIPTION_RE, SARULE_SCORE_RE


def _get_rule(ruleid):
    "Return rule"
    try:
        rule = Session.query(SARule).get(ruleid)
    except NoResultFound:
        rule = None
    return rule


class UpdateSaRules(BaseCommand):
    "Update Spamassassin rules"
    summary = 'Update the Spamassassin rule descriptions'
    #usage = 'NAME '
    group_name = 'baruwa'

    def command(self):
        "run command"
        self.init()

        def updatedb(line):
            """Update or save the rule name and
            description to the database"""
            match = RULE_DESCRIPTION_RE.match(line)
            if match:
                matchdict = match.groupdict()
                oldrule = _get_rule(matchdict['ruleid'])
                if oldrule is None:
                    if not matchdict['ruleid'].startswith('__'):
                        rule = SARule(**matchdict)
                        Session.add(rule)
                        Session.commit()
                else:
                    if (str(oldrule.description) !=
                        str(matchdict['description'])):
                        oldrule.description = matchdict['description']
                        Session.add(oldrule)
                        Session.commit()

        def processfile(thefile):
            """Open the rules file and read in the rule
            name and description"""
            with open(thefile, 'r') as rulefile:
                [updatedb(line) for line in rulefile.readlines()]

        def updatescores(thefile):
            """Update the rule scores in the database"""
            with open(thefile, 'r') as rulefile:
                for line in rulefile.readlines():
                    match = SARULE_SCORE_RE.match(line)
                    if match:
                        matchdict = match.groupdict()
                        rule = _get_rule(matchdict['ruleid'])
                        if rule:
                            if '#' in matchdict['scores']:
                                tmp = matchdict['scores'].split('#')[0]
                                scores = tmp.split()
                            else:
                                scores = matchdict['scores'].split()
                            if len(scores) == 4:
                                score = scores[3]
                            else:
                                score = scores[0]
                            rule.score = score
                            Session.add(rule)
                            Session.commit()

        for directory in self.conf['spamassassin.dirs'].split(','):
            directory = directory.strip()
            if not os.path.isdir(directory):
                print >> sys.stderr, "Directory '%s' does not exist" % directory
                continue
            for (dirname, dirs, files) in os.walk(directory):
                for saconf in files:
                    if saconf.endswith('.cf'):
                        saconfpath = os.path.join(dirname, saconf)
                        processfile(saconfpath)
                        updatescores(saconfpath)
