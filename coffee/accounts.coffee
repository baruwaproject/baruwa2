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
            if data.orgid
                rows.push '<span><a href="/accounts/byorg/{{orgid}}/{{first_page}}"><img src="{{media_url}}/imgs/first_pager.png" alt="first" title="first" /></a></span><span>...</span>'
            else
                rows.push '<span><a href="/accounts/{{first_page}}"><img src="{{media_url}}/imgs/first_pager.png" alt="first" title="first" /></a></span><span>...</span>'
        if data.previous_page
            if data.orgid
                rows.push '<span><a href="/accounts/byorg/{{orgid}}/{{previous_page}}"><img src="{{media_url}}/imgs/previous_pager.png" alt="prev" title="prev" /></a></span>'
            else
                rows.push '<span><a href="/accounts/{{previous_page}}"><img src="{{media_url}}/imgs/previous_pager.png" alt="prev" title="prev" /></a></span>'
        for linkpage in data.page_nums
            if linkpage == data.page
                rows.push '<span class="curpage">{{page}}</span>'
            else
                if data.orgid
                    rows.push '<span><a href="/accounts/byorg/{{orgid}}/'+linkpage+'">'+linkpage+'</a></span>'
                else
                    rows.push '<span><a href="/accounts/'+linkpage+'">'+linkpage+'</a></span>'
        if data.next_page
            if data.orgid
                rows.push '<span><a href="/accounts/byorg/{{orgid}}/{{next_page}}"><img src="{{media_url}}/imgs/next_pager.png" alt="next" title="next" /></a></span>'
            else
                rows.push '<span><a href="/accounts/{{next_page}}"><img src="{{media_url}}/imgs/next_pager.png" alt="next" title="next" /></a></span>'
        if data.next_page != data.page_count and data.page != data.page_count and data.page_count != 0
            if data.orgid
                rows.push '<span>...</span><span><a href="/accounts/byorg/{{orgid}}/{{last_page}}"><img src="{{media_url}}/imgs/last_pager.png" alt="last" title="last" /></a></span>'
            else
                rows.push '<span>...</span><span><a href="/accounts/{{last_page}}"><img src="{{media_url}}/imgs/last_pager.png" alt="last" title="last" /></a></span>'
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
    row = '<tr id="account-id-{{id}}"><td class="domains_check"><input type="checkbox" name="accountid" value="{{id}}" class="selector" /></td>' +
        '<td class="users_hash"><a href="/accounts/detail/{{id}}"><img src="{{media_url}}{{userimg}}" alt="view" /></a></td>' +
        '<td class="users_username"><a href="/accounts/detail/{{id}}">{{username}}</a></td>' +
        '<td class="users_fullname"><a href="/accounts/detail/{{id}}">{{fullname}}</a></td>' +
        '<td class="users_email"><a href="/accounts/detail/{{id}}">{{email}}</a></td>' +
        '<td class="users_status"><img src="{{media_url}}{{statusimg}}" alt="" /></td><td class="users_settings"><img src="{{media_url}}imgs/cog.png" alt="Settings"></td>' +
        '<td class="users_edit"><a href="/accounts/edit/{{id}}"><img src="{{media_url}}imgs/edit.png" alt="Edit"></a></td>' +
        '<td class="users_delete"><a href="/accounts/delete/{{id}}"><img src="{{media_url}}imgs/action_delete.png" alt="Delete"></a></td></tr>'
    if data.items
        rows = []
        $.each data.items, (i,n) ->
            n['media_url'] = exports.media_url
            html = $.mustache row, n
            rows.push html
        replacement = rows.join ''
    else
        replacement = '<tr><td colspan="7" class="spanrow">No accounts found</td></tr>'
    $('div.pages').html pagination(data)
    $('tbody').empty().append replacement
    if data.items.length
        pages_tmpl = gettext('Showing items {{first_item}} to {{last_item}} of {{item_count}}.')
        pages_html = $.mustache pages_tmpl, data
        title_tmpl = gettext('Accounts :: Showing page {{page}} of {{page_count}} pages.')
        title_html = $.mustache title_tmpl, data
        $('div.limiter').show()
    else
        pages_html = gettext('No items found')
        title_html = gettext('Accounts')
        $('div.limiter').hide()
    $('div.toolbar p').html pages_html
    $('#title').html title_html
    $.address.title '.:. Baruwa :: ' + title_html
    $('div.pages a').click((e)->
        url = $(this).attr('href') + '.json'
        ajaxify(e, url)
        1
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
    $('#saccountstop, #saccountsbottom').change(->
        n = $(this).val()
        location.href = "#{exports.setitems_url}?n=#{n}"
    )
    1