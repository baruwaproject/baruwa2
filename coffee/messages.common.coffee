###!
 * Baruwa Enterprise Edition
 * http://www.baruwa.com
 *
 * Copyright (c) 2013-2015 Andrew Colin Kissa
 *
 *
###
style_map = {gray: 'notscanned', whitelisted: 'whitelisted', blacklisted: 'blacklisted', highspam: 'highspam', spam: 'spam', infected: 'infected', white: ''}

show_dialog = ()->
    bootbox.dialog '<h3 class="head smaller lighter blue">Processing your request, please be patient</h3>',
    [{'label': 'Dismiss', 'class': 'btn btn-small btn-success'}]
    1

disable_links = (e) ->
    if exports.inprogress
        e.preventDefault()
        e.stopPropagation()
        # bootbox.dialog '<h3 class="head smaller lighter blue">Processing your request, please be patient</h3>',
        # [{'label': 'Dismiss', 'class': 'btn btn-small btn-success'}]
    1

pagination = (data, action) ->
    if data.items.length
        rows = []
        data['action'] = action
        if data.next_page != data.first_page and data.page != data.first_page
            rows.push '<span><a href="/messages/{{action}}/{{order_by}}/{{direction}}/{{first_page}}"><i class="icon-double-angle-left"></i></a></span><span>...</span>'
        if data.previous_page
          rows.push '<span><a href="/messages/{{action}}/{{order_by}}/{{direction}}/{{previous_page}}"><i class="icon-angle-left"></i></a></span>'
        for linkpage in data.page_nums
            if linkpage == data.page
                rows.push '<span class="curpage">{{page}}</span>'
            else
                rows.push '<span><a href="/messages/{{action}}/{{order_by}}/{{direction}}/'+linkpage+'">'+linkpage+'</a></span>'
        if data.next_page
            rows.push '<span><a href="/messages/{{action}}/{{order_by}}/{{direction}}/{{next_page}}"><i class="icon-angle-right"></i></a></span>'
        if data.next_page != data.page_count and data.page != data.page_count and data.page_count != 0
            rows.push '<span>...</span><span><a href="/messages/{{action}}/{{order_by}}/{{direction}}/{{last_page}}"><i class="icon-double-angle-right"></i></a></span>'
        tmpl = rows.join '\n'
        html = $.mustache tmpl, data
    else
        html = '-'
    html

ajaxify = (e, url) ->
    if exports.inprogress
        show_dialog
        return false
    e.preventDefault()
    $.address.value url.replace(/\.json/, '')
    $.address.history $.address.baseURL() + url
    ajaxrequest url
    1

replacelink = (html, style)->
    $(style).html html
    1

buildrows = (items, action) ->
    row = '<tr class="{{style}}"><td class="date_td  hidden-phone">' +
            '<a href="/messages/{{action}}/{{id}}">{{timestamp}}</a></td>' +
            '<td class="from_td hidden-phone"><a href="/messages/{{action}}/{{id}}">{{from_address}}</a></td>' +
            '<td class="to_td hidden-phone"><a href="/messages/{{action}}/{{id}}">{{to_address}}</a></td>' +
            '<td class="subject_td"><a href="/messages/{{action}}/{{id}}">{{{subject}}}</a></td>' +
            '<td class="size_td hidden-phone"><a href="/messages/{{action}}/{{id}}">{{size}}</a></td>' +
            '<td class="score_td hidden-phone"><a href="/messages/{{action}}/{{id}}">{{sascore}}</a></td>' +
            '<td class="status_td hidden-phone"><a href="/messages/{{action}}/{{id}}">{{status}}</a></td></tr>'
    if items.length
        rows = []
        $.each items, (i,n) ->
            n['action'] = action
            n['timestamp'] = BaruwaDateString(n['timestamp'])
            n['style'] = style_map[n['style']]
            html = $.mustache row, n
            rows.push html
        replacement = rows.join ''
    else
        replacement = '<tr><td colspan="7" class="spanrow">'+gettext('No messages found')+'</td></tr>'
    $('tbody').empty().append replacement
    1

