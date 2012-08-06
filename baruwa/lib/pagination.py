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
from math import ceil

def paginator(context, adjacent_pages=2):
    """
    Paginate through sphinx result.

    """
    if context['total'] == 0:
        pages = 0
    else:
        pages = int(ceil(context['total'] /
                float(context['results_per_page'])))
    startpage = max(context['page'] - adjacent_pages, 1)
    if startpage <= 3:
        startpage = 1
    endpage = context['page'] + adjacent_pages + 1
    if endpage >= pages - 1:
        endpage = pages + 1
    page_numbers = [n for n in range(startpage, endpage) \
    if n > 0 and n <= pages]
    if context['page'] == 1:
        first = 1
        last = (context['page'] *
                min(context['results_per_page'], context['items']))
    else:
        first = ((context['page'] - 1) * context['results_per_page']) + 1
        last = (((context['page'] - 1) *
                context['results_per_page']) +
                min(context['results_per_page'], context['items']))

    return {
        'results_per_page': context['results_per_page'],
        'page': context['page'],
        'pages': pages,
        'items': context['items'],
        'total': context['total'],
        'page_numbers': page_numbers,
        'first': first,
        'last': last,
        'next': context['page'] + 1,
        'previous': context['page'] - 1,
        'has_next': context['page'] < pages,
        'has_previous': context['page'] - 1,
        'show_first': page_numbers and 1 not in page_numbers,
        'show_last': page_numbers and pages not in page_numbers,
        'q': context['q'],
        'last_page': pages,
        'first_page': 1,
    }