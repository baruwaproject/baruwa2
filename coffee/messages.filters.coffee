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
exports.show_url = filter_url
exports.add_url = filter_add_url


process_filter_response = (data)->
    if data.success
        links = build_links(data.active_filters)
        url = window.location.pathname + '.json'
        $('#fhl').empty()
        if links != ""
            $('#fhl').append(links)
            $('#mailfilter').removeClass('hide')
        else
            $('#mailfilter').removeClass('show')
            $('#mailfilter').addClass('hide')
            $('#mailfilter').remove()
        $('#fhl a').bind 'click', (e)->
            e.preventDefault()
            enable_filters(this.href)
            1
        ajaxrequest(url)
        1
    else
        html = $.mustache exports.errbox, {msg:data.errors.msg}
        if $('#alertmsg').length
            $('#alertmsg').empty()
            $('#alertmsg').remove()
        $('#heading').after html
        1
    1


enable_filters = (url)->
    $.ajax url + '.json',
        type: 'GET',
        cache: false,
        dataType: 'json',
        beforeSend: (XHR)->
            exports.inprogress = true
            $('#spinner').show()
            1
        success: process_filter_response,
        error: ajax_error_redirect,
        complete:(XHR, textStatus) ->
            exports.inprogress = false
            $('#spinner').hide()
            1
    1


ajaxify_form = ->
    $('#afform .close').bind 'click', (e)->
        e.preventDefault()
        $('.form_area').hide()
    $('#filter-form').submit (e)->
        e.preventDefault()
        $("#filter_form_submit").attr {disabled:'disabled', value:gettext('Loading')}
        text = gettext 'Processing request.............'
        $('#filter-form').before '<div class="row-fluid" id="filter-ajax">'+text+'</div>'
        request_data = {
            filtered_field: $("#filtered_field").val(),
            filtered_by: $("#filtered_by").val(),
            filtered_value: $("#filtered_value").val(),
            csrf_token: $("#csrf_token").val()
        }
        url = $('#filter-form').attr('action')
        $.ajax url + '.json',
            type: 'POST',
            cache: false,
            data: request_data,
            success: process_filter_response,
            dataType: 'json',
            beforeSend: (XHR)->
                exports.inprogress = true
                1
            error: display_ajax_error,
            complete: (XHR, textStatus) ->
                $("#filter_form_submit").removeAttr('disabled').attr {value:gettext('Add Filter')}
                $("#filter-ajax").remove()
                exports.inprogress = false
                1
    1

show_filters = ->
    $.ajax exports.show_url,
        type:'GET',
        dataType:'html',
        cache:false,
        beforeSend: (XHR)->
            exports.inprogress = true
            $('#spinner').show()
            1
        success:(data, textStatus, XHR) ->
            # if not $('#filterrow').length
            # if $('#filterrow').length
            $('#reportfilter').prevAll("div.space-6:first").remove()
            $('#reportfilter').remove()
            $('#mailfilter').prevAll("div.space-6:first").remove()
            $('#mailfilter').remove()
            if not $('.form_area').length
                $('#sublinks').after(data)
            else
                $('.form_area').after(data)
            $('.mkbox').removeClass('hide')
            $('#mailfilter').removeClass('hide')
            if not $('#fhl a').length
                $('#fhl').html('<span id="tmpinfo">'+gettext('None applied at the moment')+'</span>')
            $('#fhl a').bind 'click', (e)->
                e.preventDefault()
                enable_filters(this.href)
            $('#apfb').bind 'click', (e)->
                e.preventDefault()
                $('#applied_filters').prevAll("div.space-6:first").remove()
                $('#applied_filters').remove()
                $('#mailfilter').prevAll("div.space-6:first").remove()
                $('#mailfilter').remove()
            1
        complete:(XHR, textStatus) ->
            exports.inprogress = false
            $('#spinner').hide()
            1
        error:display_ajax_error
    1

add_filters = ->
    if exports.inprogress
        return
    if not $('.form_area').length
        $.ajax exports.add_url,
            type:'GET',
            dataType:'html',
            cache:true,
            beforeSend: (XHR)->
                exports.inprogress = true
                $('#spinner').show()
                1
            success:(data, textStatus, XHR) ->
                if not $('.form_area').length
                    $('#sublinks').after(data)
                init_form()
                ajaxify_form()
                1
            complete:(XHR, textStatus) ->
                exports.inprogress = false
                $('#spinner').hide()
            error:display_ajax_error
    $('.form_area').show()
    1

