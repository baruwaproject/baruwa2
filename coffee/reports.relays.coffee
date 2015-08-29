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

generate_pie = (mydata)->
    data = []
    $.each mydata, (i, f)->
        f['label'] = f['tooltip']
        f['data'] = f['y']
        data.push f
        1
    placeholder = $('#chart')
    $.plot(placeholder, data, exports.pieoptions)
    $tooltip = $("<div class='tooltip top in' style='display:none;'><div class='tooltip-inner'></div></div>").appendTo('body')
    placeholder.data('tooltip', $tooltip)
    previousPoint = null
    placeholder.on 'plothover', (event, pos, item)->
        if item
            if previousPoint != item.seriesIndex
                previousPoint = item.seriesIndex
                tip = item.series['label']
                $(this).data('tooltip').show().children(0).text(tip)
            $(this).data('tooltip').css({top:pos.pageY + 10, left:pos.pageX + 10})
        else
            $(this).data('tooltip').hide()
            previousPoint = null
        1
    1

process_response = (data)->
    if data.success
        links = build_links(data.active_filters)
        $('#fhl').empty()
        if links != ""
            $('#fhl').append(links)
            $('.mkbox').parent().removeClass('hide')
        else
            $('.mkbox').parent().removeClass('show')
            $('.mkbox').parent().addClass('hide')
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
                tmpl = '<tr><td>{{counter}}.</td><td><span class="label label-{{counter}}">&nbsp;&nbsp;</span>' +
                       '&nbsp;{{address}}</td><td class="hidden-phone">{{hostname}}</td><td>{{{flag}}}</td>' +
                       '<td class="hidden-phone">{{count}}</td><td class="hidden-phone">{{size}}</td></tr>'
                $.each data.items, (i, f)->
                    item = {}
                    item['counter'] = i + 1
                    item['address'] = f[0]
                    item['hostname'] = f[1]
                    item['flag'] = f[2]
                    item['count'] = f[3]
                    item['size'] = filesizeformat f[4]
                    html = $.mustache tmpl, item
                    rows.push html
                    1
                if rows.length
                    replacement = rows.join('')
                else
                    text = gettext('No items found')
                    replacement = '<tr><td colspan="6">'+text+'</td></tr>'
                $('#pietbody').empty().append(replacement)
                generate_pie data.pie_data
                1
            error: ajax_error_redirect,
            complete: (XHR, textStatus) ->
                $("#filter_form_submit").removeAttr('disabled').attr {value:gettext('Add Filter')}
                $("#filter-ajax").remove()
                1
    else
        $("#filter_form_submit").removeAttr('disabled').attr {value:gettext('Add Filter')}
        $("#filter-ajax").remove()
        display_ajax_response_error(data.errors.msg)
    1


$(document).ready ->
    exports.pieoptions = {
        series: {
            pie: {
                show: true,
                tilt:0.6,
                highlight: {
                    opacity: 0.25
                },
                stroke: {
                    color: '#fff',
                    width: 2
                },
                startAngle: 2
            }
        },
        grid: {
            hoverable: true,
            clickable: true
        },
        tooltip: true,
        tooltipOpts: {
            content: "%s",
            shifts: {
                x: -30,
                y: -50
            }
        },
    }
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
            dataType: 'json'
            error: display_ajax_error
        1
    generate_pie rdata
    1

