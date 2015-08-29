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

disable_links = (e) ->
    if exports.inprogress
        e.preventDefault()
    1

pagination = (data) ->
    if data.items.length
        rows = []
        #data['action'] = action
        if data.next_page != data.first_page and data.page != data.first_page
            rows.push '<span><a href="/settings/{{first_page}}"><i class="icon-double-angle-left"></i></a></span><span>...</span>'
        if data.previous_page
            rows.push '<span><a href="/settings/{{previous_page}}"><i class="icon-angle-left"></i></a></span>'
        for linkpage in data.page_nums
            if linkpage == data.page
                rows.push '<span class="curpage">{{page}}</span>'
            else
                rows.push '<span><a href="/settings/'+linkpage+'">'+linkpage+'</a></span>'
        if data.next_page
            rows.push '<span><a href="/settings/{{next_page}}"><i class="icon-angle-right"></i></a></span>'
        if data.next_page != data.page_count and data.page != data.page_count and data.page_count != 0
            rows.push '<span>...</span><span><a href="/settings/{{last_page}}"><i class="icon-double-angle-right"></i></a></span>'
        tmpl = rows.join '\n'
        html = $.mustache tmpl, data
    else
        html = '-'
    html

ajaxify = (e, url) ->
    e.preventDefault()
    $.address.value url.replace(/\.json/, '')
    $.address.history $.address.baseURL() + url
    ajaxrequest url
    1


buildpage = (data) ->
    row = '<tr><td>&nbsp;</td><td class="scanners_name">{{hostname}}</td>' +
        '<td><img src="{{media_url}}{{statusimg}}" alt="" /></td>' +
        '<td><a href="/settings/node/{{id}}/section/1"><i class="icon-cog blue"></i></a></td>' +
        '<td><a href="/settings/node/edit/{{id}}"><i class="icon-edit blue"></i></a></td>' +
        '<td><a href="/settings/node/delete/{{id}}"><i class="icon-remove red"></i></a></td></tr>'

    if data.items
        rows = []
        $.each data.items, (i,n) ->
            n['media_url'] = exports.media_url
            html = $.mustache row, n
            rows.push html
        replacement = rows.join ''
    else
        replacement = '<tr><td colspan="5" class="spanrow">'+gettext('No scanning hosts found')+'</td></tr>'
    $('div.pages').html pagination(data)
    $('tbody').empty().append replacement
    if data.items.length
        pages_tmpl = gettext('Showing items {{first_item}} to {{last_item}} of {{item_count}}.')
        pages_html = $.mustache pages_tmpl, data
        title_tmpl = gettext('Settings :: Nodes :: Showing page {{page}} of {{page_count}} pages.')
        title_html = $.mustache title_tmpl, data
    else
        pages_html = gettext('No items found')
        title_html = gettext('Settings :: Nodes')
    $('div.toolbar p').html pages_html
    $('#title').html title_html
    $.address.title '.:. ' + exports.baruwa_custom_name + ' :: ' + title_html
    $('div.pages a').click((e)->
        url = $(this).attr('href') + '.json'
        ajaxify(e, url)
    )

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
    $('#statusnumitemstop, #statusnumitemsbottom').change(->
        n = $(this).val()
        location.href = "#{exports.setitems_url}?n=#{n}"
    )


