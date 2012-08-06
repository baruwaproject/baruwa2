$ = jQuery
exports = this
exports.run = should_run

request_json = ->
    row = '<tr><td>{{message_id}}</td><td>{{from_address}}</td><td>{{to_address}}</td>' +
          '<td><img src="{{img}}" alt="{{alt}} />"</td><td>{{error}}</td></tr>'
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
                        eimg = 'failed.png'
                        alt = gettext('FAILED')
                        erows = []
                        for error in n.errors
                            erows.push "#{error[0]} : #{error[1]}"
                        n['error'] = erows.join '<br/>'
                    else
                        eimg = 'passed.png'
                        alt = gettext('PASSED')
                    n['img'] = "#{exports.media_url}imgs/#{eimg}"
                    n['alt'] = "#{alt}"
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
        exports.auto_refresh = setTimeout request_json, 5000
    1