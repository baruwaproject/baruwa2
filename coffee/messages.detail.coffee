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
exports.list_add_url = list_add_url
exports.relayedvia_url = relayedvia_url


disable_links = (e) ->
    if exports.inprogress
        e.preventDefault()
    1

relayed_via = (e)->
    e.preventDefault()
    if $('#relayedhosts').length
        if $("#relayedhosts").css("display") == 'block'
            text = gettext('Show hosts')
            html = "<i class=\"icon-arrow-down\"></i>&nbsp;#{text}"
            $('#rvtoggle a').html html
            $("#relayedhosts").css({display:'none'})
        else
            text = gettext('Hide hosts')
            html = "<i class=\"icon-arrow-up\"></i>&nbsp;#{text}"
            $('#rvtoggle a').html html
            $("#relayedhosts").css({display:'block'})
    else
        $.ajax exports.relayedvia_url,
            type:'GET',
            cache:true,
            dataType:'html',
            beforeSend: (XHR)->
                img = "<img id=\"ajp\" src=\"#{exports.media_url}imgs/ajax-pager.gif\" alt=\"loading\">"
                $('#rvtoggle').before(img)
            success: (data, textStatus, XHR) ->
                $('#ajp').remove()
                if not $('#rvtoggle').siblings().length
                    $('#rvtoggle').before(data)
                    text = gettext('Hide hosts')
                    html = "<i class=\"icon-arrow-up\"></i>&nbsp;#{text}"
                    $('#rvtoggle a').html html
                    1
            error: display_ajax_error,
            complete:(XHR, textStatus) ->
                if $('#ajp').length
                    $('#ajp').remove()
                1

inserthtml = (data)->
    if $('#alertmsg').length
        $('#alertmsg').empty()
        $('#alertmsg').remove()
    $('#loading').remove()
    $('#shield').html data
    $('#from_address').attr {readonly: 'readonly'}
    $('#iptoggle').click (e)->
        if $(this).is(':checked')
            $('#domaintoggle').attr {checked: false}
            $('#from_address').val($('#clientip').text())
        else
            $('#from_address').val($('#from_addr').text())
        1
    $('#domaintoggle').click (e)->
        if $(this).is(':checked')
            tmpaddr = $('#from_addr').text()
            if tmpaddr.indexOf('@') != -1
                $('#iptoggle').attr {checked: false}
                $('#from_address').val(tmpaddr.split('@')[1])
        else
            $('#from_address').val($('#from_addr').text())
        1
    $('#from_address').val($('#from_addr').text())
    if $('#to_domain').length
        # todo check if this fails
        splitarry = $('#to_addr').text().split('@')
        to_addr = splitarry[0]
        to_domain = splitarry[1]
        $('#to_domain').val(to_domain)
        $("#to_domain option[value!='"+to_domain+"']").remove()
    else
        to_addr = $('#to_addr').text()
    $('#to_address').val(to_addr).attr {readonly: 'readonly'}
    if $('#ajaxform select').length == 2
        $("#to_address option[value!='"+to_addr+"']").remove()
    $('#ajaxformheading .close').click((e)->
        e.preventDefault()
        $('#shield').remove()
    )
    $('a').click disable_links
    $('#list-form').submit (e)->
        $('#ajaxsubmit').attr {disabled: 'disabled'}
        saved_text = $('#ajaxformheading .span11').text()
        e.preventDefault()
        form_data = {
            from_address: $('#from_address').val(),
            to_address: $('#to_address').val(),
            list_type: $('#list_type').val(),
            csrf_token: $("#csrf_token").val()
        }
        if $('#to_domain').length
            form_data['to_domain'] = $('#to_domain').val()
        $.ajax exports.list_add_url,
            type:'POST',
            data:form_data,
            dataType:'html',
            beforeSend: (XHR)->
                exports.inprogress = true
                $('#ajaxformheading .span11').text(gettext('Processing......'))
                1
            success:inserthtml,
            error: display_ajax_error,
            complete:(XHR, textStatus) ->
                exports.inprogress = false
                $('#ajaxsubmit').removeAttr 'disabled'
                $('#ajaxformheading .span11').text(saved_text)
                1

handle_post = (e)->
    e.preventDefault()
    if not $('#shield').length
        $('#wrap').after exports.loading
    else
        $('#shield').show()
    request_data = {
         learnas: $('#learnas').val(),
         altrecipients: $('#altrecipients').val(),
         csrf_token: $("#csrf_token").val()
    }
    if $("#release").is(":checked")
        request_data['release'] = 1
    if $("#delete").is(":checked")
        request_data['delete'] = 1
    if $("#learn").is(":checked")
        request_data['learn'] = 1
    if $("#usealt").is(":checked")
        request_data['usealt'] = 1
    $.ajax location.pathname + '.json',
        type:'POST',
        cache:false,
        dataType:'json',
        data:request_data,
        beforeSend: (XHR)->
            exports.inprogress = true
        success:(data, textStatus, jqXHR)->
            tmpl = '<div class="row-fluid" id="qmresult"><div class="span1 hidden-phone"></div><div class="span10">' +
                    '<div class="alert alert-notice"><button class="close" data-dismiss="alert" type="button">' +
                    '<i class="icon-remove"></i></button><strong><i class="icon-ok"></i></strong> ' +
                    '{{{result}}}</div></div><div class="span1 hidden-phone"></div></div>'
            html = $.mustache tmpl, data
            if $('#alertmsg').length
                $('#alertmsg').empty()
                $('#alertmsg').remove()
            if $('#qmresult').length
                $('#qmresult').remove()
            $('#heading').after html
            $('.close').click (e)->
                e.preventDefault()
                $('#qmresult').remove()
            $('#qform :checkbox').attr {checked: false}
            $('#altrecipients').val('')
            if request_data['delete'] == 1
                $('#msgops li:gt(0)').remove()
            1
        error: display_ajax_error,
        complete:(XHR, textStatus) ->
            $('#shield').hide()
            exports.inprogress = false
            if $(window).scrollTop()
                $('html,body').animate
                    scrollTop: $("#wrap").offset().top, 1500
            1
    1

$(document).ready ->
    $('a').click disable_links
    $('#listsender').bind 'click', (e)->
        e.preventDefault()
        if not $('#shield').length
            $('#wrap').after exports.loading
        else
            $('#shield').show()
        $.ajax exports.list_add_url,
            type:'GET',
            cache:false,
            dataType:'html',
            beforeSend: (XHR)->
                exports.inprogress = true
            success: inserthtml,
            error: display_ajax_error,
            complete:(XHR, textStatus) ->
                exports.inprogress = false
    $('#alertmsg .close').click((e)->
        e.preventDefault()
        $('#alertmsg').empty()
        $('#alertmsg').remove()
    )
    $('#qform').submit handle_post
    $('#rvtoggle a').bind 'click', relayed_via
    $('#mhtoggle a').bind 'click', (e)->
        e.preventDefault()
        if $("#mail-headers").css("display") == 'block'
            $("#mail-headers").css({display:'none'})
            $(this).blur().html('<i class="icon-arrow-down"></i>&nbsp;'+gettext('Show headers'));
            if $(window).scrollTop()
                $('html,body').animate
                    scrollTop: $("#wrap").offset().top, 1400
        else
            $("#mail-headers").css({display:'block'})
            $(this).blur().html('<i class="icon-arrow-up"></i>&nbsp;'+gettext('Hide headers'));
    1


