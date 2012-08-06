$ = jQuery
exports = this

$(document).ready ->
    $('#cancelrset').bind 'click', (e)->
        e.preventDefault()
        $('#forgottenpw').addClass 'hide'
        $('#login-box').removeClass 'hide'
        document.title = 'Baruwa :: ' + gettext('Login')
        1
    $('#iforgot').bind 'click', (e)->
        e.preventDefault()
        $('#forgottenpw').removeClass 'hide'
        $('#login-box').addClass 'hide'
        document.title = 'Baruwa :: ' + gettext('Reset my password')
        1