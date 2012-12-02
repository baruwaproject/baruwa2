$ = jQuery
exports = this
exports.already_run = false
exports.setitems_url = setitems_url

disable_links = (e) ->
    if exports.inprogress
        e.preventDefault()
    1

request_json = ->
    row = '<tr class="{{style}}_row"><td class="date_td">' +
            '<a href="/messages/detail/{{id}}">{{timestamp}}</a></td>' +
            '<td class="from_td"><a href="/messages/detail/{{id}}">{{from_address}}</a></td>' +
            '<td class="to_td"><a href="/messages/detail/{{id}}">{{to_address}}</a></td>' +
            '<td class="subject_td"><a href="/messages/detail/{{id}}">{{{subject}}}</a></td>' +
            '<td class="size_td"><a href="/messages/detail/{{id}}">{{size}}</a></td>' +
            '<td class="score_td"><a href="/messages/detail/{{id}}">{{sascore}}</a></td>' +
            '<td class="status_td"><a href="/messages/detail/{{id}}">{{status}}</a></td></tr>'
    $.ajax location.pathname + '.json',
        type: 'GET'
        cache: false
        dataType: 'json'
        beforeSend: (XHR, settings) ->
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
            if $('.notice').length
                $('.notice').remove()
            if data.items.length
                rows = []
                exports.last_ts = data.items[0].timestamp
                $.each data.items, (i,n) ->
                    n['timestamp'] = BaruwaDateString(n['timestamp'])
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
            $('#inq a').text data.inbound 
            $('#outq a').text data.outbound
            $('#smailtotal').text data.totals[0]
            if data.totals[4]
                $('#sspamtotal').text data.totals[4]
            if data.totals[2]
                $('#svirustotal').text data.totals[2]
            if data.status
                simg = 'active.png'
                alt = gettext('OK')
            else
                simg = 'inactive.png'
                alt = gettext('FAULTY')
            tmp = "{{media_url}}imgs/{{simg}}"
            statusimg = $.mustache(tmp, {media_url: exports.media_url, simg: simg})
            $('#statusimg').attr('src', statusimg).attr('alt', alt);
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
    $('#spinner').ajaxStart(->
        exports.inprogress = true
        $(this).show()
    ).ajaxStop(->
        $(this).hide()
    ).ajaxError(->
        $(this).hide()
    )
    $('a').click disable_links
    exports.auto_refresh = setTimeout request_json, 60000
    $('#num_items').change(->
        n = $(this).val()
        location.href = "#{exports.setitems_url}?n=#{n}"
    )
    1
    