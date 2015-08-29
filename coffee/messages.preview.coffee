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

exports.msgbox = '<div class="row-fluid"><div class="span1 hidden-phone"></div><div class="span10">' +
		         '<div class="alert alert-info"><button class="close" data-dismiss="alert" type="button">' +
		         '<i class="icon-remove"></i></button><strong><i class="icon-ok"></i></strong>' +
		         gettext(' This message contains external images, which have been blocked.') +
		         '<a href="'+preview_with_imgs_url+'"> '+gettext('Display images')+'</a></div></div>' +
		         '<div class="span1 hidden-phone"></div></div>'

format_change = (e)->
    e.preventDefault()
    $('.alert').parent().parent().remove()
    if $('#altformat').hasClass('textformat')
        #html showing
        $(this).text gettext('HTML Alternative')
        $(this).removeClass('textformat').addClass('htmlformat')
        $('#email-text-part').removeClass('hide').addClass('show')
        $('#email-html-part').removeClass('show').addClass('hide')
        1
    else
        #text showing
        $(this).text gettext('Text Alternative')
        $(this).removeClass('htmlformat').addClass('textformat')
        if $('img[src$="/imgs/blocked.gif"]').length
            $('#heading').after exports.msgbox
        $('#email-text-part').removeClass('show').addClass('hide')
        $('#email-html-part').removeClass('hide').addClass('show')
        1
    1

$(document).ready ->
    $('.lh').trunk8()
    $('#altformat').click format_change
    1

