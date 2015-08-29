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
        if data.next_page != data.first_page and data.page != data.first_page
            if data.orgid
                rows.push '<span><a href="/domains/byorg/{{orgid}}/{{first_page}}"><i class="icon-double-angle-left"></i></a></span><span>...</span>'
            else
                rows.push '<span><a href="/domains/{{first_page}}"><i class="icon-double-angle-left"></i></a></span><span>...</span>'
        if data.previous_page
            if data.orgid
                rows.push '<span><a href="/domains/byorg/{{orgid}}/{{previous_page}}"><i class="icon-angle-left"></i></a></span>'
            else
                rows.push '<span><a href="/domains/{{previous_page}}"><i class="icon-angle-left"></i></a></span>'
        for linkpage in data.page_nums
            if linkpage == data.page
                rows.push '<span class="curpage">{{page}}</span>'
            else
                if data.orgid
                    rows.push '<span><a href="/domains/byorg/{{orgid}}/'+linkpage+'">'+linkpage+'</a></span>'
                else
                    rows.push '<span><a href="/domains/'+linkpage+'">'+linkpage+'</a></span>'
        if data.next_page
            if data.orgid
                rows.push '<span><a href="/domains/byorg/{{orgid}}/{{next_page}}"><i class="icon-angle-right"></i></a></span>'
            else
                rows.push '<span><a href="/domains/{{next_page}}"><i class="icon-angle-right"></i></a></span>'
        if data.next_page != data.page_count and data.page != data.page_count and data.page_count != 0
            if data.orgid
                rows.push '<span>...</span><span><a href="/domains/byorg/{{orgid}}/{{last_page}}"><i class="icon-double-angle-right"></i></a></span>'
            else
                rows.push '<span>...</span><span><a href="/domains/{{last_page}}"><i class="icon-double-angle-right"></i></a></span>'
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
    top = '<tr><td><input type="checkbox" name="domainid" value="{{id}}" class="selector" /></td>' +
        '<td><a href="/domains/detail/{{id}}">{{name}}</a></td>' +
        '<td  class="hidden-phone">'
    bottom = '</td><td  class="hidden-phone"><a href="/accounts/domain/{{id}}"><i class="icon-user blue"></i></a></td>' +
        '<td class="hidden-phone"><i class="icon-{{status}} {{statuscolor}}"></i></td>' +
        '<td><a href="/settings/domain/{{id}}"><i class="icon-cog blue"></i></a></td>' +
        '<td><a href="/domains/edit/{{id}}"><i class="icon-edit blue"></i></a></td>' +
        '<td><a href="/domains/delete/{{id}}"><i class="icon-remove red"></i></a></td></tr>'
    if data.items
        rows = []
        $.each data.items, (i,n) ->
            if n['statusimg'] == 'imgs/tick.png'
                status = 'ok'
                statuscolor = 'green'
            if n['statusimg'] == 'imgs/minus.png'
                status = 'minus'
                statuscolor = 'red'
            n['status'] = status
            n['statuscolor'] = statuscolor
            html = $.mustache top, n
            rows.push html
            for owner in n.organizations
                tmpl = '<a href="/organizations/{{id}}">{{name}}</a>'
                html = $.mustache tmpl, owner
                rows.push html
                rows.push '&nbsp;'
            n['media_url'] = exports.media_url
            html = $.mustache bottom, n
            rows.push html
        replacement = rows.join ''
    else
        replacement = '<tr><td colspan="7" class="spanrow">'+gettext('No domains found')+'</td></tr>'
    $('div.pages').html pagination(data)
    $('tbody').empty().append replacement
    if data.items.length
        pages_tmpl = gettext('Showing items {{first_item}} to {{last_item}} of {{item_count}}.')
        pages_html = $.mustache pages_tmpl, data
        title_tmpl = gettext('Domains :: Showing page {{page}} of {{page_count}} pages.')
        title_html = $.mustache title_tmpl, data
        $('div.limiter').show()
    else
        pages_html = gettext('No items found')
        title_html = gettext('Domains')
        $('div.limiter').hide()
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
        success:buildpage,
        error:display_ajax_error

$(document).ready ->
    exports.inprogress = false
    $('#checkall').click(->
        $('.selector').attr 'checked', this.checked
        1
    )
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
    $('#seldomaintop, #seldomainbottom').change(->
        n = $(this).val()
        location.href = "#{exports.setitems_url}?n=#{n}"
    )


