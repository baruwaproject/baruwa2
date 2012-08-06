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
                tmpl = '<tr><td class="totals_date">{{date}}</td><td class="totals_mail">{{mail_total}}</td>' +
                	   '<td class="totals_virii">{{virus_total}}</td><td class="totals_viriip">{{virus_percent}}%</td>' +
                	   '<td class="totals_spam">{{spam_total}}</td><td class="totals_spamp">{{spam_percent}}%</td>' +
                	   '<td class="totals_volume">{{size_total}}</td></tr>'
                if $('#alertmsg').length
                    $('#alertmsg').empty()
                    $('#alertmsg').remove()
                if $('.notice').length
                    $('.notice').remove()
                $.each data.items, (i, f)->
                    html = $.mustache tmpl, f
                    rows.push html
                    1
                if rows
                    replacement = rows.join('')
                else
                    text = gettext('No records found')
                    replacement = '<tr><td class="spanrow" colspan="7">'+text+'</td></tr>'
                $('#chartbody').empty().append(replacement)
                $('#chart img').attr {src: url + '.png?' + d.getTime()}
                1
            error: ajax_error_redirect,
            complete: (XHR, textStatus) ->
                $("#filter_form_submit").removeAttr('disabled').attr {value:gettext('Add Filter')}
                $("#filter-ajax").remove()
                1
    else
        display_ajax_response_error(response.errors.msg)
    1


$(document).ready ->
    init_form()
    $('#form-area').hide()
    $('#addfilter a').bind 'click', (e)->
        e.preventDefault()
        $('#form-area').show()
        $('#addfilter').hide()
        1
    $('#afform .closeflash').bind 'click', (e)->
        e.preventDefault()
        $('#form-area').hide()
        $('#addfilter').show()
        1
    $('#fhl a').bind 'click', (e)->
        e.preventDefault()
        remove_filter e, this.href
    $('#filter-form').submit (e)->
        e.preventDefault()
        $("#filter_form_submit").attr {disabled:'disabled', value:gettext('Loading')}
        text = gettext 'Processing request.............'
        $('#afform').after '<div class="grid_16 drow" id="filter-ajax"><div class="grid_7">'+text+'</div></div>'
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
    $('#spinner').ajaxStart(->
        $(this).show()
        timg = exports.media_url + 'imgs/large-progress.gif'
        $('#chart img').attr {src: timg}
    ).ajaxStop(->
        $(this).hide()
    ).ajaxError(
        ajax_global_error_redirect
    )