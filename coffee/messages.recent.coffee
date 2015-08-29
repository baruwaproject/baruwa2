###!
 * Baruwa Enterprise Edition
 * http://www.baruwa.com
 *
 * Copyright (c) 2013-2015 Andrew Colin Kissa
 *
 *
###
$ = jQuery
exports = this
exports.already_run = false
exports.setitems_url = setitems_url
style_map = {gray: 'notscanned', whitelisted: 'whitelisted', blacklisted: 'blacklisted', highspam: 'highspam', spam: 'spam', infected: 'infected', white: ''}

disable_links = (e) ->
    if exports.inprogress
        e.preventDefault()
        e.stopPropagation()
        bootbox.dialog '<h3 class="head smaller lighter blue">' + gettext('Refreshing page, please wait') + '</h3>',
        [{'label': 'Dismiss', 'class': 'btn btn-small btn-success'}]
    1

request_json = ->
    row = '<tr class="{{style}}"><td class="date_td hidden-phone">' +
            '<a href="/messages/detail/{{id}}">{{timestamp}}</a></td>' +
            '<td class="from_td hidden-phone"><a href="/messages/detail/{{id}}">{{from_address}}</a></td>' +
            '<td class="to_td hidden-phone"><a href="/messages/detail/{{id}}">{{to_address}}</a></td>' +
            '<td class="subject_td"><a href="/messages/detail/{{id}}">{{{subject}}}</a></td>' +
            '<td class="size_td hidden-phone"><a href="/messages/detail/{{id}}">{{size}}</a></td>' +
            '<td class="score_td hidden-phone"><a href="/messages/detail/{{id}}">{{sascore}}</a></td>' +
            '<td class="status_td hidden-phone"><a href="/messages/detail/{{id}}">{{status}}</a></td></tr>'
    $.ajax location.pathname + '.json',
        type: 'GET'
        cache: false
        dataType: 'json'
        beforeSend: (XHR, settings) ->
            exports.inprogress = true
            XHR.setRequestHeader "X-Last-Timestamp", exports.last_ts
        error: (XHR, textStatus, errorThrown) ->
            if XHR.status == 200
                window.location = location.href
            html = $.mustache exports.errmsgbox, {msg: errorThrown or gettext('network connection failure, reconnecting in 60 seconds')}
            if $('#alertmsg').length
                $('#alertmsg').empty()
                $('#alertmsg').remove()
            $('#heading').after html
        success: (data, textStatus, XHR) ->
            if $('#alertmsg').length
                $('#alertmsg').empty()
                $('#alertmsg').remove()
            if $('.alert').length
                $('.alert').parent().parent().remove()
            if data.items.length
                rows = []
                exports.last_ts = data.items[0].timestamp
                $.each data.items, (i,n) ->
                    n['timestamp'] = BaruwaDateString(n['timestamp'])
                    n['style'] = style_map[n['style']]
                    html = $.mustache row, n
                    rows.push html
                replacement = rows.join ''
                if (data.num_items != data.items.length) and exports.already_run
                    $('tbody tr:first').before replacement
                    index = data.num_items - 1
                    selector = "tbody tr:gt(#{index})"
                    $(selector).remove()
                else
                    $('tbody').empty().append replacement
                $('a').click disable_links
            $('#inq').text data.inbound
            $('#outq').text data.outbound
            $('#bq').text(data.inbound + data.outbound)
            $('span .mtotal').text data.totals[0]
            $('#mtotal').text data.totals[0]
            $('#ttotal').text data.totals[0]
            # if data.totals[4]
            $('#shighspamtotal').text data.totals[4]
            # if data.totals[2]
            $('#svirustotal').text data.totals[2]
            $('#slowspamtotal').text data.totals[5]
            $('#sinfectedtotal').text data.totals[3]
            if data.status
                alt = gettext('OK')
                gstatus = '<i class="icon-ok green"></i> <span class="badge badge-success">' + alt + '</span>'
            else
                alt = gettext('ERROR')
                gstatus = '<i class="icon-remove red"></i> <span class="badge badge-important">' + alt + '</span>'
            $('#gstatus').html gstatus
            1
        complete: (XHR, textStatus) ->
            exports.inprogress = false
            exports.already_run = true
            exports.auto_refresh = setTimeout request_json, 60000
            1
    1

$(document).ready ->
    exports.last_ts = ''
    exports.inprogress = false
    # $('#spinner').ajaxStart(->
    #     exports.inprogress = true
    #     $(this).show()
    # ).ajaxStop(->
    #     $(this).hide()
    # ).ajaxError(->
    #     $(this).hide()
    # )
    $('a').click disable_links
    exports.auto_refresh = setTimeout request_json, 60000
    $('#num_items').change(->
        n = $(this).val()
        location.href = "#{exports.setitems_url}?n=#{n}"
    )
    1


