$ = jQuery
exports = this
exports.media_url = media_url
exports.errmsgbox = '<div id="alertmsg" class="alpos">' +
                    '<div class="error">' +
                    '<a class="closeflash" href="#" title="Close">x</a>' +
                    gettext('AJAX Error:')+' {{msg}}</div></div>'
exports.errbox = '<div id="alertmsg" class="alpos"><div class="error">' +
                 '<a class="closeflash" href="#" title="Close">x</a>' +
                  gettext('Error Occured:')+' {{msg}}</div></div>'
progress_tmpl = '<div id="shield"><div id="loading"><img src="{{media_url}}imgs/large-progress.gif" alt="loading"/><br/>'+gettext('Loading')+'</div></div>'
exports.loading = $.mustache progress_tmpl, {'media_url': exports.media_url}

filesizeformat = (bytes)->
    s = ['bytes', 'KB', 'MB', 'GB', 'TB', 'PB']
    e = Math.floor(Math.log(bytes) / Math.log(1024))
    (bytes / Math.pow(1024, Math.floor(e))).toFixed(1) + " " + s[e]

display_ajax_error = (XHR, textStatus, errorThrown)->
    html = $.mustache exports.errmsgbox, {msg: errorThrown or gettext('Unknown error occured !')}
    if $('#alertmsg').length
        $('#alertmsg').empty()
        $('#alertmsg').remove()
    $('#heading').after html
    # $('#alertmsg .closeflash').click (e)->
    #     e.preventDefault()
    #     $('#alertmsg').empty()
    #     $('#alertmsg').remove()
    #     1
    1

ajax_error_redirect = (XHR, textStatus, errorThrown)->
    if XHR.status == 200
        window.location = location.href
    html = $.mustache exports.errmsgbox, {msg: errorThrown or gettext('Unknown error occured !')}
    if $('#alertmsg').length
        $('#alertmsg').empty()
        $('#alertmsg').remove()
    $('#heading').after html
    # $('#alertmsg .closeflash').click((e)->
    #     e.preventDefault()
    #     $('#alertmsg').empty()
    #     $('#alertmsg').remove()
    # )
    1

ajax_global_error_redirect = (event, request, settings, errorThrown)->
    if request.status == 200
        location.href = settings.url
    else
        html = $.mustache exports.errmsgbox, {msg: errorThrown or gettext('Unknown error occured !')}
        if $('#alertmsg').length
            $('#alertmsg').empty()
            $('#alertmsg').remove()
        $('#heading').after html
    $(this).hide()
    1

display_global_ajax_error = (e, jqxhr, settings, errorThrown)->
    html = $.mustache errmsgbox, {msg: errorThrown or gettext('Unknown error occured !')}
    if $('#alertmsg').length
        $('#alertmsg').empty()
        $('#alertmsg').remove()
    $('#heading').after html
    1

display_ajax_response_error = (errormsg)->
    html = $.mustache exports.errmsgbox, {msg:errormsg}
    if $('#alertmsg').length
        $('#alertmsg').empty()
        $('#alertmsg').remove()
    $('#heading').after html
    1

$(document).ready ->
    $('#globallang').change(->
        n = $(this).val()
        if window.location.search
            location.href = "/accounts/setlang#{window.location.search}&amp;language=#{n}"
        else
            location.href = "/accounts/setlang?language=#{n}"
        1
    )
    $('.closeflash').bind 'click', (e)->
        e.preventDefault()
        $(this).parent().parent().remove()
        1
    1

