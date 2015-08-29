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

"""Clean up CSS"""
import re
import logging
import cssutils

from tinycss import make_parser

from baruwa.lib.regex import XSS_RE

UNCLEANTAGS = ['html', 'title', 'head', 'body', 'base']

UNCLEAN_RE = re.compile(r'|'.join("^" + tag for tag in UNCLEANTAGS))
PARSER = make_parser('page3')
CSS_FMT = """%s {
%s
}
"""


def rule_fixup(rule, target):
    "Utility function to clean up CSS rules"
    rule.selectorText = UNCLEAN_RE.sub(target, rule.selectorText)
    target_re = re.compile(r'^(:?\s+)?' + target)
    tmprules = []
    changed = False
    for tmprule in rule.selectorText.split(','):
        if not target_re.match(tmprule):
            newrule = u'%s %s' % (target, tmprule)
            tmprules.append(newrule)
            changed = True
        else:
            tmprules.append(tmprule)
    if changed:
        rule.selectorText = u','.join(tmprules)

    for prop in rule.style.keys():
        if XSS_RE.findall(rule.style[prop]):
            rule.style.removeProperty(prop)


def sanitize_css(css, target='#email-html-part'):
    "Sanitize CSS"
    parser = cssutils.parse.CSSParser(parseComments=False,
                                    loglevel=logging.FATAL)
    parsed = parser.parseString(css)
    indexes = []
    for rule in parsed.cssRules:
        if (rule.type in [rule.STYLE_RULE, rule.MEDIA_RULE] and
            rule.wellformed):
            if rule.type == rule.STYLE_RULE:
                rule_fixup(rule, target)
            if rule.type == rule.MEDIA_RULE:
                subindexes = []
                for subrule in rule.cssRules:
                    if (subrule.type == subrule.STYLE_RULE and
                        subrule.wellformed):
                        rule_fixup(subrule, target)
                    else:
                        subindexes.append(subrule)
                for sind in subindexes:
                    rule.deleteRule(rule.cssRules.index(sind))
        else:
            indexes.append(rule)
    for ind in indexes:
        parsed.deleteRule(parsed.cssRules.index(ind))
    return parsed.cssText


def sanitize_style(css):
    "Sanitize style attributes"
    parsed, _ = PARSER.parse_style_attr(css)
    styles = ("%s: %s;" % (style.name, style.value.as_css())
            for style in parsed if not XSS_RE.findall(style.value.as_css()))
    return ' '.join(styles)
