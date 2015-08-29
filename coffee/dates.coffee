###!
 * Baruwa Enterprise Edition
 * http://www.baruwa.com
 *
 * Copyright (c) 2013-2015 Andrew Colin Kissa
 *
 *
###
BaruwaDateString = (r) ->
    json_format = "YYYY-MM-DD HH:mm:ss Z"
    display_format = "YYYY-MM-DD HH:mm:ss"
    moment(r, json_format).tz(user_timezone).format(display_format)

