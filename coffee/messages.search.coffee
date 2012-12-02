$ = jQuery
exports = this
exports.search_url = search_url
exports.setitems_url = setitems_url

pagination = (data, action) ->
    if data.pages > 0
        rows = []
        data['action'] = action
        data['search_url'] = exports.search_url
        if data.next != data.first_page and data.page != data.first
            rows.push '<span><a href="{{search_url}}?q={{q}}&amp;a={{action}}&amp;page={{first_page}}"><img src="{{media_url}}/imgs/first_pager.png" alt="first" title="first" /></a></span><span>...</span>'
        if data.has_previous
          rows.push '<span><a href="{{search_url}}?q={{q}}&amp;a={{action}}&amp;page={{previous}}"><img src="{{media_url}}/imgs/previous_pager.png" alt="prev" title="prev" /></a></span>'
        for linkpage in data.page_numbers
            if linkpage == data.page
                rows.push '<span class="curpage">{{page}}</span>'
            else
                rows.push '<span><a href="{{search_url}}?q={{q}}&amp;a={{action}}&amp;page='+linkpage+'">'+linkpage+'</a></span>'
        if data.has_next
            rows.push '<span><a href="{{search_url}}?q={{q}}&amp;a={{action}}&amp;page={{next}}"><img src="{{media_url}}/imgs/next_pager.png" alt="next" title="next" /></a></span>'
        if data.next != data.pages and data.page != data.pages and data.pages != 0
            rows.push '<span>...</span><span><a href="{{search_url}}?q={{q}}&amp;a={{action}}&amp;page={{last_page}}"><img src="{{media_url}}/imgs/last_pager.png" alt="last" title="last" /></a></span>'
        tmpl = rows.join '\n'
        html = $.mustache tmpl, data
    else
        html = '-'
    html

process_response = (data, textStatus, XHR)->
    a = $('#a').val()
    $('div.pages').html pagination(data.paginator, a)
    if data.items
        row = '<tr class="{{style}}_row"><td class="date_td">' +
                '<a href="/messages/detail/{{id}}">{{timestamp}}</a></td>' +
                '<td class="from_td"><a href="/messages/detail/{{id}}">{{from_address}}</a></td>' +
                '<td class="to_td"><a href="/messages/detail/{{id}}">{{to_address}}</a></td>' +
                '<td class="subject_td"><a href="/messages/detail/{{id}}">{{subject}}</a></td>' +
                '<td class="size_td"><a href="/messages/detail/{{id}}">{{size}}</a></td>' +
                '<td class="score_td"><a href="/messages/detail/{{id}}">{{sascore}}</a></td>' +
                '<td class="status_td"><a href="/messages/detail/{{id}}">{{status}}</a></td></tr>'
        rows = []
        $.each data.items, (i,n) ->
            n['timestamp'] = BaruwaDateString(n['timestamp'])
            html = $.mustache row, n
            rows.push html
        replacement = rows.join ''
    else
        replacement = "<tr><td colspan=\"7\" class=\"spanrow\">"+gettext('No messages found matching search query:')+" #{q} !</td></tr>"
    $('tbody').empty().append replacement
    if data.items.length
        pages_tmpl = gettext('Showing items {{first}} to {{last}} of {{total}}.')
        pages_html = $.mustache pages_tmpl, data.paginator
        search_tmpl = gettext('About {{total_found}} results ({{search_time}} seconds)')
        search_html = $.mustache search_tmpl, data
        $('div.limiter').show()
    else
        pages_html = gettext('No items found')
        search_html = gettext('0 Results found ({{search_time}} seconds)')
        $('div.limiter').hide()
    title_tmpl = gettext('Messages :: Search results :: {{q}}')
    title_html = $.mustache title_tmpl, data
    $('div.toolbar p').html pages_html
    $('#searchinfo').html search_html
    $('#title').html title_html
    $('div.pages a'). bind 'click', (e)->
        e.preventDefault()
        index = this.href.indexOf(exports.search_url)
        base = this.href.slice(index)
        index = base.indexOf('?')
        url = base.slice(0, index)
        params = base.slice(index)
        ajax_request url + '.json' + params
    1

ajax_request = (url)->
    $.ajax url,
        type: 'GET'
        cache: false
        dataType: 'json'
        error: display_ajax_error,
        success: process_response
    1

$(document).ready ->
    $('#msgsearch').submit((e)->
        e.preventDefault()
        q = $('#q').val()
        a = $('#a').val()
        action = $("#msgsearch").attr('action')
        url =  "#{action}.json?q=#{q}&amp;a=#{a}"
        $.ajax url,
            type: 'GET'
            cache: false
            dataType: 'json'
            error: display_ajax_error,
            success: process_response
        1
    )
    $('.filter_show').bind 'click', (e)->
        e.preventDefault()
        show_filters()
        1
    $('div.pages a'). bind 'click', (e)->
        e.preventDefault()
        index = this.href.indexOf(exports.search_url)
        base = this.href.slice(index)
        index = base.indexOf('?')
        url = base.slice(0, index)
        params = base.slice(index)
        ajax_request url + '.json' + params
        1
    $('#spinner').ajaxStart(->
        $(this).show()
    ).ajaxStop(->
        $(this).hide()
    ).ajaxError(->
        $(this).hide()
    )
    $('#sresultstop, #sresultsbottom').change(->
        n = $(this).val()
        q = $('#q').val()
        a = $('#a').val()
        location.href = "#{exports.setitems_url}?n=#{n}&amp;q=#{q}&amp;a=#{a}"
    )
    1