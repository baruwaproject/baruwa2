###!
 * Baruwa Enterprise Edition
 * http://www.baruwa.com
 *
 * Copyright (c) 2013-2015 Andrew Colin Kissa
 *
 *
###
$(document).ready ->
    $('#checkall').click(->
        $('.selector').attr 'checked', this.checked
        1
    )
