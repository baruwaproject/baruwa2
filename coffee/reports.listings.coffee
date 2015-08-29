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

# process_rdata = (mydata)->

date_to_timestamp = (date)->
    mydate = date.split "-"
    newdate = mydate[1] + "/" + mydate[2] + "/" + mydate[0]
    new Date(newdate).getTime()


showTooltip = (x, y, contents)->
    $('<div id="listing-tooltip">' + contents + '</div>').css({top: y - 20, left: x - 90}).appendTo("body").show()


generate_graph = (mydata)->
    mail = []
    spam = []
    virus = []
    days = []
    if mydata.labels
        $.each mydata.labels, (i, f)->
            mail.push [date_to_timestamp(f.text), mydata.mail[i]]
            spam.push [date_to_timestamp(f.text), mydata.spam[i]]
            virus.push [date_to_timestamp(f.text), mydata.virus[i]]
            days.push f.text
            1
    else
        $.each mydata.items, (i, f)->
            mail.push [date_to_timestamp(f.date), f.mail_total]
            spam.push [date_to_timestamp(f.date), f.spam_total]
            virus.push [date_to_timestamp(f.date), f.virus_total]
            days.push f.date
            1
    if mail.length or spam.length or virus.length or days.length
        placeholder = $('#chart')
        data = [
                {label: "Mail",
                data: mail,
                bars: {show: true, fill: true, lineWidth: 1, order: 1, fillColor:  "#008000", barWidth: 24 * 60 * 60 * 500},
                color: "#008000"
                },
                {label: "Spam", data: spam,
                bars: {show: true, fill: true, lineWidth: 1, order: 2, fillColor:  "#FFC0CB", barWidth: 24 * 60 * 60 * 500},
                color: "#FFC0CB"
                },
                {label: "Virus", data: virus,
                bars: {show: true, fill: true, lineWidth: 1, order: 3, fillColor:  "#FF0000", barWidth: 24 * 60 * 60 * 500},
                color: "#FF0000"
                }
            ]
        $.plot(placeholder, data, {
                xaxis: {
                    mode: "time",
                    timeformat: "%Y-%m-%d",
                    tickSize: [10, "day"],
                },
                grid: {
                    hoverable: true,
                    clickable: false,
                    borderWidth: 1
                },
                series: {
                    shadowSize: 1
                }
            })
        placeholder.bind 'plothover', (event, pos, item)->
            if item
                if previousPoint != item.datapoint
                    previousPoint = item.datapoint
                    $('#listing-tooltip').remove()
                    y = item.datapoint[1]
                    showTooltip(item.pageX, item.pageY, "<b>" + item.series.label + ": " + y + "</b>")
            else
                $('#listing-tooltip').remove()
                previousPoint = null
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
                tmpl = '<tr><td>{{date}}</td><td>{{mail_total}}</td>' +
                	   '<td>{{virus_total}}</td><td class="hidden-phone">{{virus_percent}}%</td>' +
                	   '<td>{{spam_total}}</td><td class="hidden-phone">{{spam_percent}}%</td>' +
                	   '<td>{{size_total}}</td></tr>'
                $.each data.items, (i, f)->
                    html = $.mustache tmpl, f
                    rows.push html
                    1
                if rows.length
                    replacement = rows.join('')
                else
                    text = gettext('No records found')
                    replacement = '<tr><td class="spanrow" colspan="7">'+text+'</td></tr>'
                $('#chartbody').empty().append(replacement)
                generate_graph data
                1
            error: ajax_error_redirect,
            complete: (XHR, textStatus) ->
                $("#filter_form_submit").removeAttr('disabled').attr {value:gettext('Add Filter')}
                $("#filter-ajax").remove()
                1
    else
        display_ajax_response_error(data.errors.msg)
        $("#filter-ajax").remove()
        $("#filter_form_submit").removeAttr('disabled').attr {value:gettext('Add Filter')}
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
            dataType: 'json'
            error: display_ajax_error
        1
    generate_graph rdata
    1

