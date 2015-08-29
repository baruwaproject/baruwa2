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
exports.baseurl = base_url

disable_links = (e) ->
    if exports.inprogress
        e.preventDefault()
        1

ajaxrequest = (url) ->
    if not $('#shield').length
        $('#wrap').after exports.loading
    else
        $('#shield').show()
    $.ajax url,
        type:'GET',
        cache:false,
        dataType:'json'
        success:buildpage,
        beforeSend: (XHR)->
            exports.inprogress = true
            1
        error:display_ajax_error,
        complete:(XHR, textStatus) ->
            exports.inprogress = false
            $('#shield').hide()
            if $(window).scrollTop()
                $('html,body').animate
                    scrollTop: $("#wrap").offset().top, 1500
            1

ajaxify = (e, url)->
    e.preventDefault()
    $.address.value url.replace(/\.json/, '')
    $.address.history $.address.baseURL() + url
    ajaxrequest url
    1

buildrows = (items)->
    row = '<tr>
    	<td class="hidden-phone">{{timestamp}}</td>
    	<td>{{username}}</td>
    	<td>{{info}}</td>
    	<td class="hidden-phone">{{hostname}}</td>
    	<td class="hidden-phone">{{remoteip}}</td>
    	<td class="hidden-phone">{{category}}</td>
        </tr>'
    if items.length
        rows = []
        $.each items, (i,n) ->
            html = $.mustache row, n
            rows.push html
        replacement = rows.join ''
    else
        replacement = '<tr><td colspan="6">'+gettext('No audit logs found')+'</td></td>'
    $('tbody').empty().append replacement
    1

pagination = (data)->
    if data.items.length
        rows = []
        data['baseurl'] = exports.base_url
        if data.q
            data['params'] = ".json?q=#{data.q}"
        else
            data['params'] = ".json"
        if data.next_page != data.first_page and data.page != data.first_page
            rows.push '<span><a href="{{baseurl}}/{{first_page}}{{{params}}}"><i class="icon-double-angle-left"></i></a></span><span>...</span>'
        if data.previous_page
          rows.push '<span><a href="{{baseurl}}/{{previous_page}}{{{params}}}"><i class="icon-angle-left"></i></a></span>'
        for linkpage in data.page_nums
            if linkpage == data.page
                rows.push '<span class="curpage">{{page}}</span>'
            else
                rows.push '<span><a href="{{baseurl}}/'+linkpage+'{{{params}}}">'+linkpage+'</a></span>'
        if data.next_page
            rows.push '<span><a href="{{baseurl}}/{{next_page}}{{{params}}}"><i class="icon-angle-right"></i></a></span>'
        if data.next_page != data.page_count and data.page != data.page_count and data.page_count != 0
            rows.push '<span>...</span><span><a href="{{baseurl}}/{{last_page}}{{{params}}}"><i class="icon-double-angle-right"></i></a></span>'
        tmpl = rows.join '\n'
        html = $.mustache tmpl, data
    else
        html = '-'
    html

buildpage = (data)->
    buildrows data.items
    $('div.pages').html pagination(data)
    if data.items.length
        pages_tmpl = gettext('Showing items {{first_item}} to {{last_item}} of {{item_count}}.')
        pages_html = $.mustache pages_tmpl, data
        title_tmpl = gettext('Status :: Audit log :: Showing page {{page}} of {{page_count}} pages.')
        title_html = $.mustache title_tmpl, data
        $('div.limiter').show()
    else
        pages_html = gettext('No items found')
        title_html = gettext('Status :: Audit log')
        $('div.limiter').hide()
    $('div.toolbar p').html pages_html
    $('#title').html title_html
    $.address.title '.:. ' + exports.baruwa_custom_name + ' :: ' + title_html
    $('div.pages a').click((e)->
        url = $(this).attr('href')
        # if '.json' not in url
        #     if '?' in url
        #         params = url.slice(url.indexOf('?'))
        #         url = url.slice(0, url.indexOf('?'))
        #         url = url + '.json' + params
        ajaxify(e, url)
    )
    # $('thead a').click((e)->
    #     url = $(this).attr('href') + '.json'
    #     ajaxify(e, url)
    # )
    if $('#alertmsg').length
        $('#alertmsg').empty()
        $('#alertmsg').remove()

$(document).ready ->
    exports.inprogress = false
    $('div.pages a').click((e)->
        e.preventDefault()
        url = $(this).attr('href')
        if '.json' not in url
            if '?' in url
                p = url.slice(url.indexOf('?'))
                url = url.slice(0, url.indexOf('?'))
                url = url + '.json' + p
            else
                url = url + '.json'
        ajaxify(e, url)
    )
    $('a').click disable_links
    $.address.externalChange((e)->
        if e.path == '/'
            $.address.history $.address.baseURL()
            return
        url = $.address.value()
        if '.json' not in url
            if '?' in url
                p = url.slice(url.indexOf('?'))
                url = url.slice(0, url.indexOf('?'))
                url = url + '.json' + p
            else
                url = url + '.json'
        ajaxify(e, url)
    )
    $('#auditlogtop, #auditlogbottom').change(->
        n = $(this).val()
        location.href = "#{exports.setitems_url}?n=#{n}&amp;ac=auditlog"
    )
    1



