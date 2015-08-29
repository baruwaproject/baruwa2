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
exports.aftmpl = '<div class="row-fluid afr"><div class="span1 half"><a href="/reports/filters/delete/{{index}}">' +
                    '<i class="icon-remove red"></i></a></div><div class="span1 half">' +
                    '<a href="/reports/filters/save/{{index}}"><i class="icon-save green"></i></a>' +
                    '</div><div class="span10 half">{{filter_field}} {{filter_by}} {{filter_value}}</div></div>'
exports.sftmpl = '<div class="row-fluid sfr"><div class="span1 half"><a href="/reports/storedfilters/delete/{{id}}">' +
                    '<i class="icon-remove red"></i></a></div><div class="span1 half">{{{link_chunk}}}</div>' +
                    '<div class="span10 half">{{name}}</div></div>'
exports.aftext = gettext('No active filters at the moment')
exports.sftext = gettext('No saved filters at the moment')

update_counters = (data)->
    $("#msgcount").html data.count
    $("#newestmsg").html data.newest
    $("#oldestmsg").html data.oldest
    1

build_active = (active_filters)->
    rows = []
    $.each active_filters, (itr, f)->
        f['index'] = itr
        f['media_url'] = exports.media_url
        html = $.mustache exports.aftmpl, f
        rows.push html
    if rows.length
        $("#afilters").nextAll().remove()
        $("#afilters").after rows.join('')
    else
        $("#afilters").nextAll().remove()
        $("#afilters").after '<div class="row-fluid afr"><div class="span12">'+exports.aftext+'</div></div>'
    $("div.afr a").bind 'click', ajaxify_active_filter_links
    1

build_saved = (saved_filters)->
    rows = []
    $.each saved_filters, (itr, f)->
        f['media_url'] = exports.media_url
        if f.loaded
            img = '<i class="icon-plus red"></i>'
        else
            img = '<a href="/reports/storedfilters/load/{{id}}"><i class="icon-upload-alt blue"></i></a>'
        f['link_chunk'] = $.mustache img, f
        html = $.mustache exports.sftmpl, f
        rows.push html
    if rows.length
        $("#sfilters").nextAll().remove()
        $("#sfilters").after rows.join('')
    else
        $("#sfilters").nextAll().remove()
        $("#sfilters").after '<div class="row-fluid"><div class="span12">'+exports.sftext+'</div></div>'
    $("div.sfr a").bind 'click', ajaxify_active_filter_links
    1

build_page = (response)->
    if response.success
        update_counters response.data
        build_active response.active_filters
        build_saved response.saved_filters
    else
        if $('.alert').length
            $('.alert').parent().parent().remove()
        html = $.mustache exports.errmsgbox, {msg:response.errors.msg}
        $('#heading').after html
        $('.close').click((e)->
            e.preventDefault()
            $('.alert').parent().parent().remove()
        )
    $("#filter_form_submit").removeAttr('disabled').attr {value:gettext('Add Filter')}
    1

ajaxify_active_filter_links = (e)->
    e.preventDefault()
    $("#filter_form_submit").attr {disabled:'disabled', value:gettext('Loading')}
    $.ajax $(this).attr('href') + '.json',
        type: 'GET',
        cache: false,
        dataType: 'json',
        success: build_page
    1

build_elements = (response)->
    if response.success
        if $('.alert').length
            $('.alert').parent().parent().remove()
        if response.active_filters
            i = response.active_filters.length
            # alert i
            i--
            # alert i
            if i > 0
                n = response.active_filters[i]
                n['media_url'] = exports.media_url
                n['index'] = i
                row = $.mustache exports.aftmpl, n
                # $("#afilters").nextAll().remove()
                # $('.afr').remove()
                $("#afilters").after row
                $('form').clearForm()
            else
                n = response.active_filters[0]
                if n
                    n['media_url'] = exports.media_url
                    n['index'] = i
                    row = $.mustache exports.aftmpl, n
                    # $("#afilters").nextAll().remove()
                    $('.afr').remove()
                    $("#afilters").after row
                else
                    $("#afilters").nextAll().after '<div class="row-fluid afr"><div class="span12">'+exports.aftext+'</div></div>'
            $("div.afr a").bind 'click', ajaxify_active_filter_links
        if response.saved_filters
            build_saved response.saved_filters
        update_counters response.data
    else
        display_ajax_response_error(response.errors.msg)
    $("#filter_form_submit").removeAttr('disabled').attr {value:gettext('Add Filter')}
    $("#filter-ajax").remove()
    $("#filtered_value").unmask("999-99-99")
    $("#filtered_value").unmask("99:99")
    1

addFilter = (e)->
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
    $.post location.pathname + '.json', request_data, build_elements, 'json'
    1


$(document).ready ->
    $('#afform .close').hide()
    init_form()
    $('#filter-form').submit addFilter
    $('#spinner').ajaxStart(->
        $(this).show()
    ).ajaxStop(->
        $(this).hide()
    ).ajaxError(
        ajax_global_error_redirect
    )
    $("div.afr a").bind 'click', ajaxify_active_filter_links
    $("div.sfr a").bind 'click', ajaxify_active_filter_links
    1

