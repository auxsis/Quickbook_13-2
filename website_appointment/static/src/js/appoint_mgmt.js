/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : https://store.webkul.com/license.html/ */

odoo.define('website_appointment.appoint_mgmt', function (require) {

    "use strict";
    var ajax = require('web.ajax');
    var core = require('web.core');
    var time = require('web.time');
    var _t = core._t;

    $(function () {
        var lang_date_format = $('.appoint_date_div').closest('form').find('input[name="lang_date_format"]').val()
        if (lang_date_format != undefined){
        $('.appoint_date_div').datetimepicker({
            format: time.strftime_to_moment_format(lang_date_format),
            pickTime: false,
            locale : moment.locale(),
            allowInputToggle: true,
            onSelect: function(date) {
                  $(this).hide();
              },
            minDate: new Date().setHours(0,0,0,0),
            defaultDate: new Date(),
            // maxDate: moment().add(200, "d"),
            icons: {
                date: 'fa fa-calendar',
                next: 'fa fa-chevron-right',
                previous: 'fa fa-chevron-left',
            },
        });
        }
    });

    $(document).ready(function(){

        $('tr.my_appointments_row').click(function() {
            var href = $(this).find("a").attr("href");
            if(href) {
                window.location = href;
          }
        });

        $('#appoint_date').on('input', function() {
        	var input=$(this);
        	var appoint_date=input.val();
        	if(appoint_date){$('#appoint_datetime_picker').removeClass("invalid").addClass("valid");
            }
        	else{$('#appoint_datetime_picker').removeClass("valid").addClass("invalid");}
        });

        $('#appoint_groups').on('input', function() {
        	var input=$(this);
        	var appoint_group=input.val();
        	if(appoint_group){
                input.removeClass("invalid").addClass("valid");}
        	else{input.removeClass("valid").addClass("invalid");}
        });

        $('#button_find_appointee').on('click', function(event){
            event.preventDefault()
            var group_id =  parseInt($("select.appoint_groups option:selected" ).val())
            var appoint_date = $('#appoint_date').val()
            if (isNaN(group_id) && (appoint_date == '')){
                $('#appoint_groups').addClass("invalid");
                $('#appoint_datetime_picker').addClass("invalid");
            }
            else if (isNaN(group_id))
            {
                $('#appoint_groups').addClass("invalid");
            }
            else if (appoint_date == '') {
                $('#appoint_datetime_picker').addClass("invalid");
            }
            else{
                $('#appoint_groups').removeClass("invalid").removeClass("valid");
                $('#appoint_datetime_picker').removeClass("invalid").removeClass("valid");
                $('.appoint_loader').show();
                ajax.jsonRpc("/find/appointee/timeslot", 'call', {
                    'group_id'  :   group_id,
                    'appoint_date': appoint_date,
                }).then(function(appointee_listing_div){
                    console.log("===========",group_id,appoint_date)
                    $('.appoint_loader').hide();
                    if(appointee_listing_div == undefined){
                        $('#appoint_datetime_picker').addClass("invalid");
                        bootbox.alert({
                            title: "Warning",
                            backdrop: true,
                            message: _t("Appointment Date should be today or later."),
                        })
                    }
                    else{
                        $('div#appointee_listing').html(appointee_listing_div)
                    }
                });
            }
        });

        function dateCompare(time1,time2) {
          var t1 = new Date();
          var parts = time1.split(":");
          t1.setHours(parts[0],parts[1],parts[2],0);
          var t2 = new Date();
          parts = time2.split(":");
          t2.setHours(parts[0],parts[1],parts[2],0);

          // returns 1 if greater, -1 if less and 0 if the same
          if (t1.getTime()>t2.getTime()) return 1;
          if (t1.getTime()<t2.getTime()) return -1;
          return 0;
        }

        $('#appointee_listing').on('click', '.button_book_now' , function(event){
            event.preventDefault()
            var already_booked = $(this).parent().data('already-booked')
            var $form = $(this).closest('form');

            // validate timeslot according to today date and time
            var appoint_date = $('#appoint_date').val()

            var lang_date_format = $('.appoint_date_div').closest('form').find('input[name="lang_date_format"]').val()
            if (lang_date_format != undefined){
                lang_date_format = time.strftime_to_moment_format(lang_date_format)
                appoint_date = moment(appoint_date, lang_date_format)
            }

            appoint_date = new Date(appoint_date)
            var today = new Date()
            // var res = -1
            // if (appoint_date.getDate() == today.getDate() && appoint_date.getMonth() == today.getMonth() && appoint_date.getYear() == today.getYear() ){
            //     var h = today.getHours();
            //     var m = today.getMinutes();
            //
            //     var t1 = h + ':' + m + ':' + '00'
            //     var start_time = $(this).parents('.appoint_timeslot_panel').find(".start_time").html()
            //     var parts = start_time.split(":");
            //     if (parts[0].length < 2){
            //         parts[0] = '0' + parts[0]
            //     }
            //     if (parts[1].length < 2){
            //         parts[1] = '0' + parts[1]
            //     }
            //     var t2 = parts[0] + ':' + parts[1] + ':' + '00'
            //     res = dateCompare(t1,t2);
            // }
            //
            // if (res == 1 || res == 0){
            //     bootbox.alert({
            //       title: "Warning",
            //       backdrop: true,
            //       message: _t("This slot is not available for today. Please select any other slot."),
            //     })
            // }

            if (appoint_date.setHours(0,0,0,0) < today.setHours(0,0,0,0)){
                bootbox.alert({
                  title: "Warning",
                  backdrop: true,
                  message: _t("Appointment Date should be today or later."),
                })
            }
            else{
                var time_slot_id = parseInt($(this).parents('.appoint_timeslot_panel').first().attr('id'))
                var person_id =  parseInt($( "select.appoint_person option:selected" ).val())
                var appoint_person_id = parseInt($(this).parents('.appoint_person_panel').first().attr('id'))
                $('.appoint_loader').show();
                // code added for booking restriction
                ajax.jsonRpc("/validate/appointment", 'call', {
                    // 'appoint_date' : moment.utc(appoint_date).local().format("YYYY-MM-DD"),
                    'appoint_date' : $('#appoint_date').val(),
                    'time_slot_id': time_slot_id,
                    'appoint_person_id': appoint_person_id,
                }).then(function(result){
                    $('.appoint_loader').hide();
                    if(result.status == false){
                        bootbox.alert({
                          title: "Warning",
                          backdrop: true,
                          message: _t(result.message),
                        })
                    }
                    else if(already_booked && already_booked=='True'){
                        bootbox.alert({
                          title: "Warning",
                          backdrop: true,
                          message: _t("You have already booked an appointment for this slot."),
                        })
                    }
                    else{
                        $('#appointee_listing').append('<input type="hidden" name="appoint_timeslot_id" value="'+ time_slot_id + '" />');
                        if (isNaN(person_id)){
                            $('#appointee_listing').append('<input type="hidden" name="appoint_person" value="'+ appoint_person_id + '" />');
                        }
                        if(event.isDefaultPrevented()){
                            $form.submit();
                        }
                    }
                });
            }
        });

        $('#button_cancel_booking').click(function(event){
            event.preventDefault()
            var reason = ''
            var appoint_id = $(this).data('appoint_id')
            bootbox.prompt({
                title: "Please enter the reason for your cancellation ?",
                inputType: 'textarea',
                callback: function(result){
                    reason = result
                    if(appoint_id != undefined){
                        $('.appoint_loader').show();
                        ajax.jsonRpc("/cancel/booking", 'call', {
                            'appoint_id' : appoint_id,
                            'reason' : reason,
                        }).then(function(result){
                            $('.appoint_loader').hide();
                            if(result == false){
                                bootbox.alert({
                                  title: "Warning",
                                  backdrop: true,
                                  message: _t("Some error occurred..please try again later !!"),
                                })
                            }
                            else{
                                location.reload();
                            }
                        });
                    }
                },
                buttons: {
                    cancel: {
                        label: "Close",
                        className: 'btn-default',
                    },
                    confirm: {
                        label: "Cancel Now",
                        className: 'btn-danger',
                    },
                },
            });
        });
    });
});
