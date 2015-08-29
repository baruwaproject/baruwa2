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
exports.media_url = media_url
exports.errmsgbox = '<div class="row-fluid" id="alertmsg"><div class="span1 hidden-phone"></div>' +
                    '<div class="span10"><div class="alert alert-error">' +
                    '<button class="close" data-dismiss="alert" type="button">' +
                    '<i class="icon-remove"></i></button><strong><i class="icon-remove"></i></strong> ' +
                    gettext('AJAX Error:')+' {{msg}}</div></div><div class="span1 hidden-phone"></div></div>'
exports.errbox =   '<div class="row-fluid" id="alertmsg"><div class="span1 hidden-phone"></div>' +
                    '<div class="span10"><div class="alert alert-error">' +
                    '<button class="close" data-dismiss="alert" type="button">' +
                    '<i class="icon-remove"></i></button><strong><i class="icon-remove"></i></strong> ' +
                    gettext('Error Occured:')+' {{msg}}</div></div><div class="span1 hidden-phone"></div></div>'
progress_tmpl = '<div id="shield"><div id="loading"><img src="{{media_url}}imgs/large-progress.gif" alt="loading"/><br/>'+gettext('Loading')+'</div></div>'
exports.loading = $.mustache progress_tmpl, {'media_url': exports.media_url}

filesizeformat = (bytes)->
    s = ['bytes', 'KB', 'MB', 'GB', 'TB', 'PB']
    e = Math.floor(Math.log(bytes) / Math.log(1024))
    (bytes / Math.pow(1024, Math.floor(e))).toFixed(1) + " " + s[e]

display_ajax_error = (XHR, textStatus, errorThrown)->
    html = $.mustache exports.errmsgbox, {msg: errorThrown or gettext('Unknown error occured !')}
    if $('.alert').length
        $('.alert').parent().parent().remove()
    $('#heading').after html
    $('.close').bind 'click', (e)->
        e.preventDefault()
        $(this).parent().parent().parent().remove()
        1
    $('.form_area .close').unbind('click')
    $('.form_area .close').bind 'click', (e)->
        e.preventDefault()
        $('.form_area').hide()
        $('#addfilter').show()
        1
    $('#addfilter a').bind 'click', (e)->
        e.preventDefault()
        $('.form_area').show()
        $('#addfilter').hide()
        1
    1

ajax_error_redirect = (XHR, textStatus, errorThrown)->
    if XHR.status == 200
        window.location = location.href
    html = $.mustache exports.errmsgbox, {msg: errorThrown or gettext('Unknown error occured !')}
    if $('.alert').length
        $('.alert').parent().parent().remove()
    $('#heading').after html
    $('.close').bind 'click', (e)->
        e.preventDefault()
        $(this).parent().parent().parent().remove()
        1
    1

ajax_global_error_redirect = (event, request, settings, errorThrown)->
    if request.status == 200
        location.href = settings.url
    else
        html = $.mustache exports.errmsgbox, {msg: errorThrown or gettext('Unknown error occured !')}
        if $('.alert').length
            $('.alert').parent().parent().remove()
        $('#heading').after html
        $('.close').bind 'click', (e)->
            e.preventDefault()
            $(this).parent().parent().parent().remove()
            1
    $(this).hide()
    1

display_global_ajax_error = (e, jqxhr, settings, errorThrown)->
    html = $.mustache errmsgbox, {msg: errorThrown or gettext('Unknown error occured !')}
    if $('.alert').length
        $('.alert').parent().parent().remove()
    $('#heading').after html
    $('.close').bind 'click', (e)->
        e.preventDefault()
        $(this).parent().parent().parent().remove()
        1
    1

display_ajax_response_error = (errormsg)->
    html = $.mustache exports.errmsgbox, {msg:errormsg}
    if $('.alert').length
        $('.alert').parent().parent().remove()
    $('#heading').after html
    $('.close').bind 'click', (e)->
        e.preventDefault()
        $(this).parent().parent().parent().remove()
        1
    $('.form_area .close').unbind('click')
    $('.form_area .close').bind 'click', (e)->
        e.preventDefault()
        $('.form_area').hide()
        $('#addfilter').show()
        1
    $('#addfilter a').bind 'click', (e)->
        e.preventDefault()
        $('.form_area').show()
        $('#addfilter').hide()
        1
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
    $('.close').bind 'click', (e)->
        e.preventDefault()
        $(this).parent().parent().parent().remove()
        1
    1



