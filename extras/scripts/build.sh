#!/bin/bash
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

copyholder="Andrew Colin Kissa"
bugsemail="andrew@topdog.za.net"

echo "Compiling coffeescript"
coffee -b -c -o extras/js coffee
echo "Minifying javascript"
for infile in $(find extras/js -type f); do
    output_file=$(echo $infile|sed -e 's:extras/js:baruwa/public/js/baruwa:')
    java -jar ~/Documents/devel/java/yuicompressor-2.4.7.jar --charset utf-8 --type js -o $output_file  $infile
    #echo -e "\t$output_file"
done
echo "Compiling compass"
compass compile compass
if [ "$1" == "full" ]; then
echo "Updating i18n"
pybabel extract -F babel.cfg -o baruwa/i18n/baruwajs.pot --msgid-bugs-address="${bugsemail}" --copyright-holder="${copyholder}" baruwa/public/
#pybabel init -D baruwajs -i baruwa/i18n/baruwajs.pot -d baruwa/i18n -l en
pybabel update -D baruwajs -i baruwa/i18n/baruwajs.pot -d baruwa/i18n
pybabel compile -D baruwajs -f -d baruwa/i18n
python setup.py extract_messages
python setup.py update_catalog
python setup.py compile_catalog
echo "Building baruwa"
python setup.py sdist --formats bztar
fi