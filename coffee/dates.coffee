
BaruwaDateString = (r) ->
    d = new Date r
    pad = (n) ->
        if n < 10
            '0'+n
        else
            n

    d.getFullYear() + '-' \
    + pad(d.getMonth() + 1) \
    + '-' + pad(d.getDate()) + ' ' \
    + pad(d.getHours()) + ':' \
    + pad(d.getMinutes()) + ':' \
    + pad(d.getSeconds())