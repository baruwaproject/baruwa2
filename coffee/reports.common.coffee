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

build_links = (filters)->
    tmpl = '<a href="/reports/filters/delete/{{index}}"><i class="icon-remove red"></i>' +
            '&nbsp;{{filter_field}} {{filter_by}} {{filter_value}}&nbsp;'
    rows = []
    $.each filters, (i, f)->
        f['index'] = i
        f['media_url'] = exports.media_url
        html = $.mustache tmpl, f
        rows.push html
    links = rows.join('')
    links


remove_filter = (e, url)->
    e.preventDefault()
    $('#filter_form_submit').attr {disabled:'disabled', value:gettext('Loading')}
    $('#spinner').show()
    $.ajax url + '.json',
        type: 'GET',
        cache: false,
        dataType: 'json',
        success: process_response,
        error: ajax_error_redirect
    1

init_form = ->
    bool_fields = ["scaned","spam","highspam","saspam","rblspam","whitelisted",
                    "blacklisted","virusinfected","nameinfected","otherinfected",
                    "isquarantined"]
    num_fields = ["size","sascore"]
    text_fields = ["messageid","from_address","from_domain","to_address","to_domain",
                    "subject","clientip","spamreport","headers", "hostname"]
    time_fields = ["date","time"]
    num_values = [{'value':1,'opt':gettext('is equal to')},{'value':2,'opt':gettext('is not equal to')},
                    {'value':3,'opt':gettext('is greater than')},{'value':4,'opt':gettext('is less than')}]
    text_values = [{'value':1,'opt':gettext('is equal to')},{'value':2,'opt':gettext('is not equal to')},
                    {'value':9,'opt':gettext('is null')},{'value':10,'opt':gettext('is not null')},
                    {'value':5,'opt':gettext('contains')},{'value':6,'opt':gettext('does not contain')},
                    {'value':7,'opt':gettext('matches regex')},{'value':8,'opt':gettext('does not match regex')}]
    time_values = [{'value':1,'opt':gettext('is equal to')},{'value':2,'opt':gettext('is not equal to')},
                    {'value':3,'opt':gettext('is greater than')},{'value':4,'opt':gettext('is less than')}]
    bool_values = [{'value':11,'opt':gettext('is true')},{'value':12,'opt':gettext('is false')}]
    select_text = gettext('Please select')
    select_option = "<option value=\"0\" selected=\"0\">#{select_text}</option>"
    $("#filtered_field").prepend select_option
    $("#filtered_value").attr {disabled: 'disabled'}
    fltdval = $("#filtered_value")
    fltdby = $("#filtered_by")
    $("#filtered_field").bind 'change', ()->
        value_to_check = $(this).val()
        if $.inArray(value_to_check, bool_fields) != -1
            fltdval.unmask("99:99")
            fltdval.datepicker('remove')
            # fltdval.unmask("9999-99-99")
            fltdby.empty()
            $.each bool_values, (i, n) ->
                fltdby.append $('<option/>', {value:n.value, html:n.opt})
            fltdval.attr {disabled:'disabled', value:''}
        if $.inArray(value_to_check, num_fields) != -1
            fltdval.unmask("99:99")
            fltdval.datepicker('remove')
            # fltdval.unmask("9999-99-99")
            fltdby.empty()
            $.each num_values, (i, n) ->
                fltdby.append $('<option/>', {value:n.value, html:n.opt})
            fltdval.removeAttr 'disabled'
            fltdval.attr {value:''}
        if $.inArray(value_to_check, text_fields) != -1
            fltdval.unmask("99:99")
            fltdval.datepicker('remove')
            # fltdval.unmask("9999-99-99")
            fltdby.empty()
            $.each text_values, (i, n) ->
                fltdby.append $('<option/>', {value:n.value, html:n.opt})
            fltdval.removeAttr 'disabled'
            fltdval.attr {value:''}
        if $.inArray(value_to_check, time_fields) != -1
            fltdby.empty()
            $.each time_values, (i, n) ->
                fltdby.append $('<option/>', {value:n.value, html:n.opt})
            fltdval.removeAttr 'disabled'
            if value_to_check == 'time'
                fltdval.datepicker('remove')
                fltdval.mask "99:99"
            else
                # fltdval.mask "9999-99-99"
                fltdval.datepicker({'format': 'yyyy-mm-dd', 'autoclose': true, 'language': baruwalang})
    1

