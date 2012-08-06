disable_links = (e) ->
    if exports.inprogress
        e.preventDefault()
        1

pagination = (data, action) ->
    if data.items.length
        rows = []
        data['action'] = action
        if data.next_page != data.first_page and data.page != data.first_page
            rows.push '<span><a href="/messages/{{action}}/{{order_by}}/{{direction}}/{{first_page}}"><img src="{{media_url}}/imgs/first_pager.png" alt="first" title="first" /></a></span><span>...</span>'
        if data.previous_page
          rows.push '<span><a href="/messages/{{action}}/{{order_by}}/{{direction}}/{{previous_page}}"><img src="{{media_url}}/imgs/previous_pager.png" alt="prev" title="prev" /></a></span>'
        for linkpage in data.page_nums
            if linkpage == data.page
                rows.push '<span class="curpage">{{page}}</span>'
            else
                rows.push '<span><a href="/messages/{{action}}/{{order_by}}/{{direction}}/'+linkpage+'">'+linkpage+'</a></span>'
        if data.next_page
            rows.push '<span><a href="/messages/{{action}}/{{order_by}}/{{direction}}/{{next_page}}"><img src="{{media_url}}/imgs/next_pager.png" alt="next" title="next" /></a></span>'
        if data.next_page != data.page_count and data.page != data.page_count and data.page_count != 0
            rows.push '<span>...</span><span><a href="/messages/{{action}}/{{order_by}}/{{direction}}/{{last_page}}"><img src="{{media_url}}/imgs/last_pager.png" alt="last" title="last" /></a></span>'
        tmpl = rows.join '\n'
        html = $.mustache tmpl, data
    else
        html = '-'
    html

ajaxify = (e, url) ->
    e.preventDefault()
    $.address.value url.replace(/\.json/, '')
    $.address.history $.address.baseURL() + url
    ajaxrequest url
    1

replacelink = (html, style)->
    $(style).html html
    1

buildrows = (items, action) ->
    row = '<tr class="{{style}}_row"><td class="date_td">' +
            '<a href="/messages/{{action}}/{{id}}">{{timestamp}}</a></td>' +
            '<td class="from_td"><a href="/messages/{{action}}/{{id}}">{{from_address}}</a></td>' +
            '<td class="to_td"><a href="/messages/{{action}}/{{id}}">{{to_address}}</a></td>' +
            '<td class="subject_td"><a href="/messages/{{action}}/{{id}}">{{{subject}}}</a></td>' +
            '<td class="size_td"><a href="/messages/{{action}}/{{id}}">{{size}}</a></td>' +
            '<td class="score_td"><a href="/messages/{{action}}/{{id}}">{{sascore}}</a></td>' +
            '<td class="status_td"><a href="/messages/{{action}}/{{id}}">{{status}}</a></td></tr>'
    if items.length
        rows = []
        $.each items, (i,n) ->
            n['action'] = action
            html = $.mustache row, n
            rows.push html
        replacement = rows.join ''
    else
        replacement = '<tr><td colspan="7" class="spanrow">'+gettext('No messages found')+'</td></tr>'
    $('tbody').empty().append replacement
    1