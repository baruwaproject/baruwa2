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
exports.setitems_url = setitems_url

buildpage = (data) ->
    buildrows data.items, 'archive'
    $('div.pages').html pagination(data, 'archive')
    if data.items.length
        pages_tmpl = gettext('Showing items {{first_item}} to {{last_item}} of {{item_count}}.')
        pages_html = $.mustache pages_tmpl, data
        title_tmpl = gettext('Messages :: Archive :: Showing page {{page}} of {{page_count}} pages.')
        title_html = $.mustache title_tmpl, data
    else
        pages_html = gettext('No items found')
        title_html = gettext('Messages :: Archive')
    $('div.toolbar p').html pages_html
    $('#title').html title_html
    $.address.title '.:. ' + exports.baruwa_custom_name + ' :: ' + title_html
    $('div.pages a').click((e)->
        url = $(this).attr('href') + '.json'
        ajaxify(e, url)
    )
    columns = ['timestamp', 'from_address', 'to_address', 'subject', 'size', 'sascore']
    linfo = [gettext('Date/Time'), gettext('From'), gettext('To'), gettext('Subject'), gettext('Size'), gettext('Score')]
    style = ['.date_heading', '.from_heading', '.to_heading', '.subject_heading', '.size_heading', '.score_heading']
    tmpl = '<a href="/messages/archive/{{order_by}}/{{direction}}/1">{{column}}</a>'
    for column, i in columns
        html = $.mustache tmpl, {'order_by': column, 'direction': data.direction, 'column': linfo[i]}
        if column == data.order_by
            if data.direction == 'dsc'
                newdirection = 'asc'
                c = '&nbsp;&uarr;'
            else
                newdirection = 'dsc'
                c = '&nbsp;&darr;'
            arrow = $.mustache tmpl, {'order_by': data.order_by, 'direction': newdirection, 'column': c}
            html = html + arrow
        replacelink html, style[i]
        1
    $('thead a').click((e)->
        url = $(this).attr('href') + '.json'
        ajaxify(e, url)
    )
    1

ajaxrequest = (url) ->
    if not $('#shield').length
        $('#wrap').after exports.loading
    else
        $('#shield').show()
    $.ajax url,
        type:'GET',
        cache:false,
        dataType:'json',
        success:buildpage
    1

$(document).ready ->
    exports.inprogress = false
    $('div.pages a').click((e)->
        url = $(this).attr('href') + '.json'
        ajaxify(e, url)
    )
    $('thead a').click((e)->
        url = $(this).attr('href') + '.json'
        ajaxify(e, url)
    )
    $('html').ajaxStart(->
        exports.inprogress = true
    ).ajaxError(
        display_global_ajax_error
    ).ajaxComplete(->
        exports.inprogress = false
        $('#shield').hide()
        if $(window).scrollTop()
            $('html,body').animate
                scrollTop: $("#wrap").offset().top, 1500
    ).ajaxSuccess(->
        if $('#alertmsg').length
            $('#alertmsg').empty()
            $('#alertmsg').remove()
    )
    $('a').click disable_links
    $.address.externalChange((e)->
        if e.path == '/'
            $.address.history $.address.baseURL()
            return
        url = $.address.value() + '.json'
        ajaxify(e, url)
    )
    $('#sarchivetop, #sarchivebottom').change(->
        n = $(this).val()
        location.href = "#{exports.setitems_url}?n=#{n}"
    )
    1


