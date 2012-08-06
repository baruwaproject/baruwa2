$ = jQuery
exports = this
exports.aftmpl = '<div class="grid_8 drow alpha"><div class="grid_1 omega"><a href="/reports/filters/delete/{{index}}">' +
                 '<img src="{{media_url}}imgs/action_remove.png" alt="x" title="Remove" class="positio" /></a></div>' +
                 '<div class="grid_1 omega"><a href="/reports/filters/save/{{index}}">' +
                 '<img src="{{media_url}}imgs/save.png" alt="Save" title="Save" class="positio" /></a></div>' +
                 '<div class="grid_6">{{filter_field}} {{filter_by}} {{filter_value}}</div></div>'
exports.sftmpl = '<div class="grid_8 drow alpha"><div class="grid_1 omega"><a href="/reports/storedfilters/delete/{{id}}">' +
                 '<img src="{{media_url}}imgs/action_delete.png" alt="x" title="Delete" class="positio" /></a></div>' +
                 '<div class="grid_1 omega">{{{link_chunk}}}</div>' +
                 '<div class="grid_6">{{name}}</div></div>'
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
        $("#afilters").empty().append rows.join('')
    else
        $("#afilters").empty().append '<div class="grid_8 drow alpha"><div class="grid_6">'+exports.aftext+'</div></div>'
    $("#afilters div a").bind 'click', ajaxify_active_filter_links
    1

build_saved = (saved_filters)->
    rows = []
    $.each saved_filters, (itr, f)->
        f['media_url'] = exports.media_url
        if f.loaded
            img = '<img src="{{media_url}}imgs/action_add.png" alt="Load" class="positio" />'
        else
            img = '<a href="/reports/storedfilters/load/{{id}}"><img src="{{media_url}}imgs/action_add.png" alt="Load" title="Load" class="positio" /></a>'
        f['link_chunk'] = $.mustache img, f
        html = $.mustache exports.sftmpl, f
        rows.push html
    if rows.length
        $("#sfilters").empty().append rows.join('')
    else
        $("#sfilters").empty().append '<div class="grid_8 drow alpha"><div class="grid_7">'+exports.sftext+'</div></div>'
    $("#sfilters div a").bind 'click', ajaxify_active_filter_links
    1

build_page = (response)->
    if response.success
        update_counters response.data
        build_active response.active_filters
        build_saved response.saved_filters
    else
        if $('#alertmsg').length
            $('#alertmsg').empty()
            $('#alertmsg').remove()
        html = $.mustache exports.errmsgbox, {msg:response.errors.msg}
        $('#heading').after html
        $('.closeflash').click((e)->
            e.preventDefault()
            $('#alertmsg').empty()
            $('#alertmsg').remove()
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
        if $('#alertmsg').length
            $('#alertmsg').empty()
            $('#alertmsg').remove()
        if response.active_filters
            i = response.active_filters.length
            i--
            if i > 0
                n = response.active_filters[i]
                n['media_url'] = exports.media_url
                n['index'] = i
                row = $.mustache exports.aftmpl, n
                $("#afilters").append row
                $('form').clearForm()
            else
                n = response.active_filters[0]
                if n
                    n['media_url'] = exports.media_url
                    n['index'] = i
                    row = $.mustache exports.aftmpl, n
                    $("#afilters").empty().append row
                else
                    $("#afilters").append '<div class="grid_8 drow alpha"><div class="grid_6">'+exports.aftext+'</div></div>'
            $("#afilters div a").bind 'click', ajaxify_active_filter_links
        if response.saved_filters
            build_saved response.saved_filters
        update_counters response.data
    else
        display_ajax_response_error(response.errors.msg)
    $("#filter_form_submit").removeAttr('disabled').attr {value:gettext('Add Filter')}
    $("#filter-ajax").remove()
    1

addFilter = (e)->
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
    $.post location.pathname + '.json', request_data, build_elements, 'json'
    1


$(document).ready ->
    $('#afform .closeflash').hide()
    init_form()
    $('#filter-form').submit addFilter
    $('#spinner').ajaxStart(->
        $(this).show()
    ).ajaxStop(->
        $(this).hide()
    ).ajaxError(
        ajax_global_error_redirect
    )
    $("#afilters div a").bind 'click', ajaxify_active_filter_links
    $("#sfilters div a").bind 'click', ajaxify_active_filter_links
    1