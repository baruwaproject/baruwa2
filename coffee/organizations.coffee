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
            rows.push '<span><a href="/organizations/list/{{first_page}}"><img src="{{media_url}}/imgs/first_pager.png" alt="first" title="first" /></a></span><span>...</span>'
        if data.previous_page
            rows.push '<span><a href="/organizations/list/{{previous_page}}"><img src="{{media_url}}/imgs/previous_pager.png" alt="prev" title="prev" /></a></span>'
        for linkpage in data.page_nums
            if linkpage == data.page
                rows.push '<span class="curpage">{{page}}</span>'
            else
                rows.push '<span><a href="/organizations/list/'+linkpage+'">'+linkpage+'</a></span>'
        if data.next_page
            rows.push '<span><a href="/organizations/list/{{next_page}}"><img src="{{media_url}}/imgs/next_pager.png" alt="next" title="next" /></a></span>'
        if data.next_page != data.page_count and data.page != data.page_count and data.page_count != 0
            rows.push '<span>...</span><span><a href="/organizations/list/{{last_page}}"><img src="{{media_url}}/imgs/last_pager.png" alt="last" title="last" /></a></span>'
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
    row = '<tr class="orgrows"><td class="org_name"><a href="/organizations/{{id}}">{{name}}</a></td>' +
        '<td class="org_domains cl"><a href="/domains/byorg/{{id}}"><img src="{{media_url}}imgs/domains.png" alt="List domains" /></a></td>' +
        '<td class="org_accounts cl"><a href="/accounts/byorg/{{id}}"><img src="{{media_url}}imgs/user.png" alt="List accounts" /></a></td>' +
        '<td class="org_adddomains cl"><a href="/domains/byorg/{{id}}/add"><img src="{{media_url}}imgs/add.png" alt="Add domains" /></a></td>' +
        '<td class="org_importdomains cl"><a href="/organizations/import/domains/{{id}}"><img src="{{media_url}}imgs/import.png" alt="import domains" /></a></td>' +
        '<td class="org_edit cl"><a href="/organizations/edit/{{id}}"><img src="{{media_url}}imgs/edit.png" alt="Edit"></a></td>' +
        '<td class="org_delete cl"><a href="/organizations/delete/{{id}}"><img src="{{media_url}}imgs/action_delete.png" alt="Delete"></a></td></tr>'

    if data.items
        rows = []
        $.each data.items, (i,n) ->
            n['media_url'] = exports.media_url
            html = $.mustache row, n
            rows.push html
        replacement = rows.join ''
    else
        replacement = '<tr><td colspan="6" class="spanrow">'+gettext('No organizations found')+'</td></tr>'
    $('div.pages').html pagination(data)
    $('tbody').empty().append replacement
    if data.items.length
        pages_tmpl = gettext('Showing items {{first_item}} to {{last_item}} of {{item_count}}.')
        pages_html = $.mustache pages_tmpl, data
        title_tmpl = gettext('Organizations :: Showing page {{page}} of {{page_count}} pages.')
        title_html = $.mustache title_tmpl, data
    else
        pages_html = gettext('No items found')
        title_html = gettext('Organizations')
    $('div.toolbar p').html pages_html
    $('#title').html title_html
    $.address.title '.:. Baruwa :: ' + title_html
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
                scrollTop: $("#header-bar").offset().top, 1500
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
    $('#sorgstop, #sorgsbottom').change(->
        n = $(this).val()
        location.href = "#{exports.setitems_url}?n=#{n}"
    )
    1