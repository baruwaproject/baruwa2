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
exports.run = should_run

request_json = ->
    row = '<tr><td>{{{img}}}</td><td class="hidden-phone">{{message_id}}</td><td>{{from_address}}</td>' +
          '<td class="hidden-phone">{{to_address}}</td><td class="hidden-phone">{{error}}</td></tr>'
    $.ajax location.pathname + '.json',
        type: 'GET'
        cache: false
        dataType: 'json'
        error: (XHR, textStatus, errorThrown) ->
            html = $.mustache exports.errmsgbox, {msg: errorThrown or gettext('An unknown error occured')}
            if $('#alertmsg').length
                $('#alertmsg').empty()
                $('#alertmsg').remove()
            $('#stateupdates').empty().html('&nbsp;');
            $('#progbar').empty();
            $('#heading').after html
            exports.run = false
        success: (data, textStatus, XHR) ->
            if $('#alertmsg').length
                $('#alertmsg').empty()
                $('#alertmsg').remove()
            if $('.notice').length
                $('.notice').remove()
            if data.finished
                exports.run = false
                rows = []
                $.each data.results, (i,n) ->
                    if n.errors.length
                        n['img'] = '<i class="icon-remove red"></i>'
                        erows = []
                        for error in n.errors
                            erows.push "#{error[0]} : #{error[1]}"
                        n['error'] = erows.join '<br/>'
                    else
                        n['img'] = '<i class="icon-ok green"></i>'
                    html = $.mustache row, n
                    rows.push html
                replacement = rows.join ''
                $('tbody').empty().append replacement
            else
                $('#status').text(data.status);
                $('#percent').text(data.completed);
                $("#progressbar").reportprogress(data.completed);
            1
        complete: (XHR, textStatus) ->
            if exports.run
                exports.auto_refresh = setTimeout request_json, 5000
            else
                $('#shield').hide()
            1

$(document).ready ->
    if exports.run
        $('#stateupdates').empty().html("&nbsp;");
        if not $('#shield').length
            $('#wrap').after exports.loading
        else
            $('#shield').show()
        $('#shield').empty().append $('<div id="loading-status"><div id="progressbar"></div><br/>Processing tasks...</div>')
        $("#progressbar").reportprogress(0)
        exports.auto_refresh = setTimeout request_json, 5000
    1

