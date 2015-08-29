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

$(document).ready ->
    $('#cancelrset').bind 'click', (e)->
        e.preventDefault()
        $('#forgottenpw').addClass 'hide'
        $('#login-box').removeClass 'hide'
        document.title = exports.baruwa_custom_name + ' :: ' + gettext('Login')
        1
    $('#iforgot').bind 'click', (e)->
        e.preventDefault()
        $('#forgottenpw').removeClass 'hide'
        $('#login-box').addClass 'hide'
        document.title = exports.baruwa_custom_name + ' :: ' + gettext('Reset my password')
        1


