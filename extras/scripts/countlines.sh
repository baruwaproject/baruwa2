#!/bin/sh
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

pushd `dirname $0` > /dev/null
	pushd ../.. > /dev/null
		find baruwa bin coffee compass dev setup* *.ini extras -type f \
		| egrep -v "extras/(js|config|exports)" \
		| egrep -v "\.mo$" \
		| grep -v ".pyc$" \
		| grep -v ".sass-cache" \
		| egrep -v "baruwa/public/(js|css|imgs)"\
		| xargs wc
	popd > /dev/null
popd > /dev/null