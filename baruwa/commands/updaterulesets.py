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
"Update MailScanner rulesets"

from baruwa.commands import BaseCommand, change_user
from baruwa.tasks.settings import (create_sign_clean, create_html_sigs,
    create_text_sigs, create_sig_imgs, create_sig_img_names,
    create_spam_checks, create_virus_checks, create_spam_actions,
    create_highspam_actions, create_spam_scores, create_highspam_scores,
    create_lists, create_message_size, create_language_based,
    create_content_ruleset)


class UpdateRulesetsCommand(BaseCommand):
    "Update MailScanner rulesets command"

    summary = 'Generates file based MailScanner rulesets'
    group_name = 'baruwa'

    def command(self):
        "command"
        self.init()
        change_user("baruwa", "baruwa")

        create_sign_clean()
        create_html_sigs()
        create_text_sigs()
        create_sig_imgs()
        create_sig_img_names()
        create_spam_checks()
        create_virus_checks()
        create_spam_actions()
        create_highspam_actions()
        create_spam_scores()
        create_highspam_scores()
        create_lists(1)
        create_lists(2)
        create_message_size()
        create_language_based()
        create_content_ruleset()
