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

$(document).ready ->
    $('#mailqnumitemstop, #mailqnumitemsbottom').change(->
        n = $(this).val()
        location.href = "#{exports.setitems_url}?n=#{n}"
    )
    $('#allchecker').click(->
        $('.selector').attr 'checked', this.checked
        1
    )

