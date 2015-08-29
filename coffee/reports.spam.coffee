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

process_response = (data)->
    if data.success
        links = build_links(data.active_filters)
        $('#fhl').empty()
        if links != ""
            $('#fhl').append(links)
            $('.mkbox').removeClass('hide')
        else
            $('.mkbox').removeClass('show')
            $('.mkbox').addClass('hide')
        $('#fhl a').bind 'click', (e)->
            remove_filter(e, this.href)
            1
        url = window.location.pathname
        $.ajax url + '.json',
            type: 'GET',
            cache: false,
            dataType: 'json',
            success: (data, textStatus, XHR) ->
                d = `new Date()`
                rows = []
                tmpl = '<tr><td>{{score}}</td><td>{{count}}</td></tr>'
                if $('#alertmsg').length
                    $('#alertmsg').empty()
                    $('#alertmsg').remove()
                if $('.notice').length
                    $('.notice').remove()
                $.each data.items, (i, f)->
                    item = {}
                    item['score'] = f[0]
                    item['count'] = f[1]
                    html = $.mustache tmpl, item
                    rows.push html
                    1
                if rows.length
                    replacement = rows.join('')
                else
                    text = gettext('No items found')
                    replacement = '<td colspan="2">'+text+'</td>'
                $('#graphrows').empty().append(replacement)
                $('#chart img').attr {src: url + '.png?' + d.getTime()}
                1
            error: ajax_error_redirect
            complete: (XHR, textStatus) ->
                $("#filter_form_submit").removeAttr('disabled').attr {value:gettext('Add Filter')}
                $("#filter-ajax").remove()
                1
    else
        display_ajax_response_error(data.errors.msg)
        $("#filter_form_submit").removeAttr('disabled').attr {value:gettext('Add Filter')}
        $("#filter-ajax").remove()
    1


$(document).ready ->
    init_form()
    $('.form_area').hide()
    $('#addfilter a').bind 'click', (e)->
        e.preventDefault()
        $('.form_area').show()
        $('#addfilter').hide()
        1
    $('.form_area .close').unbind()
    $('.form_area .close').bind 'click', (e)->
        e.preventDefault()
        $('.form_area').hide()
        $('#addfilter').show()
        1
    $('#fhl a').bind 'click', (e)->
        e.preventDefault()
        remove_filter e, this.href
    $('#filter-form').submit (e)->
        e.preventDefault()
        $("#filter_form_submit").attr {disabled:'disabled', value:gettext('Loading')}
        text = gettext 'Processing request.............'
        $('#afform .row-fluid').before '<div class="row-fluid" id="filter-ajax"><div class="span12">'+text+'</div></div>'
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
            success: process_response,
            dataType: 'json',
            error: display_ajax_error
        1
    data = []
    $.each rdata.labels, (i, f)->
        data.push [f.text, rdata.scores[i]]
        1
    placeholder = $('#chart')
    $.plot(placeholder, [
        {
            data: data,
            bars: {
                show: true,
                # barWidth: 12*24*60*60*300,
                fill: true,
                lineWidth: 1,
                order: 1,
                fillColor:  "#0000FF"
            },
            color: "#OOOOOO",
            grid: {
                hoverable: true,
                clickable: true
            },
            tooltip: true,
        }
    ])
    1

