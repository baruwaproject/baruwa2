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
    data = []
    $.each rdata, (i, f)->
        f['label'] = f['tooltip']
        f['data'] = f['y']
        data.push f
        1
    placeholder = $('#chart')
    $.plot(placeholder, data, {
        series: {
            pie: {
                show: true,
                tilt:0.6,
                highlight: {
                    opacity: 0.25
                },
                stroke: {
                    color: '#fff',
                    width: 2
                },
                startAngle: 2
            }
        },
        grid: {
            hoverable: true,
            clickable: true
        },
        tooltip: true,
        tooltipOpts: {
            content: "%s",
            shifts: {
                x: -30,
                y: -50
            }
        },
    })
    $tooltip = $("<div class='tooltip top in' style='display:none;'><div class='tooltip-inner'></div></div>").appendTo('body')
    placeholder.data('tooltip', $tooltip)
    previousPoint = null
    placeholder.on 'plothover', (event, pos, item)->
        if item
            if previousPoint != item.seriesIndex
                previousPoint = item.seriesIndex
                tip = item.series['label']
                $(this).data('tooltip').show().children(0).text(tip)
            $(this).data('tooltip').css({top:pos.pageY + 10, left:pos.pageX + 10})
        else
            $(this).data('tooltip').hide()
            previousPoint = null
        1
    1

