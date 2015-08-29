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
"Some varibles here to prevent import loops"

POLICY_URL_MAP = {'1': 'archive-file-policy', '2': 'archive-mime-policy',
                    '3': 'file-policy', '4': 'mime-policy'}
POLICY_FILE_MAP = {1: 'archives.filename.rules',
                    2: 'archives.filetype.rules',
                    3: 'filename.rules',
                    4: 'filetype.rules'}
POLICY_SETTINGS_MAP = {1: 'archive_filename', 2: 'archive_filetype',
                        3: 'filename', 4: 'filetype'}
