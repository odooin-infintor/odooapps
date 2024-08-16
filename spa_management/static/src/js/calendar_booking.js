odoo.define('spa_management.calendar_booking', function (require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var rpc = require('web.rpc');

    var QWeb = core.qweb;


    var BookingCalendar = AbstractAction.extend({
        hasControlPanel: true,
        xmlDependencies: ['in_spa/static/src/xml/calendar.xml'],
        events: {
            'click .fc-button-agendaDay': 'get_calendar_data',
            'change #branch_selector': 'get_calendar_data',
            'change #employee_selector': 'get_calendar_data',
            'change #service_selector': 'get_calendar_data',
        },
        start: function () {
            var self = this;
            self.$el.empty();
            self.get_calendar_data();
        },
        get_calendar_data: function (event, noupdate=false) {
            if (noupdate) {
                return;
            }
            var self = this;
            var gotoDate = $('#calendar').length? $('#calendar').fullCalendar('getDate').format(): false;
            var branch = $('#branch_selector').val();
            var employee = $('#employee_selector').val();
            var service = $('#service_selector').val() || '0';
            var service_tmpl_id = $('#service_selector option:selected').data('tmpl_id') || '0';
            console.log(service, service_tmpl_id, 'sssssssssssserc');
            self.$el.empty();
            
            if (!branch)
                branch = 'all';
            if (!employee)
                employee = 'all';
            rpc.query({
                model: 'spa.booking',
                method: 'get_calendar_data',
                args: [branch, employee, service_tmpl_id],
            }).then(function (result) {
                
                if (result) {
                    self.$el.append(QWeb.render('booking_calendar_template', {
                        employees: result['employees'],
                        branches: result['branches'],
                        services: result['services']
                    }));
                    
                    $('#branch_selector').val(branch);
                    $('#employee_selector').val(employee);
                    $('#service_selector').val(service);
                    $('#service_selector').select2().trigger('change', [true]);

                    var scroll_time = new Date(Date.now() - (30 * 1000 * 60));
                    
                    self.$el.find('#calendar').fullCalendar({
                        scrollTime: scroll_time.getHours() + ":" + scroll_time.getMinutes(),
                        slotDuration: '00:30',
                        defaultView: 'agendaDay',
                        defaultDate: result['date'],
                        editable: false,
                        selectable: true,
                        eventLimit: true, // allow "more" link when too many events
                        header: {
                            left: 'prev,next today',
                            center: 'title',
                            right: 'agendaDay,agendaWeek,month,listWeek'
                        },
                        views: {
                          day: {
                             titleFormat: 'dddd, MMMM Do - YYYY'
                          }
                        },
                        resources: result['resources'],
                        events: result['bookings'],
                        selectConstraint: "businessHours",
                        
                        select: function (start, end, jsEvent, view, resource) {
                            
                            if (view.name == 'agendaDay') {
                                self.do_action({
                                    name: "Booking",
                                    type: 'ir.actions.act_window',
                                    res_model: "spa.booking",
                                    views: [
                                        [false, 'form']
                                    ],
                                    target: 'new',
                                    context: {
                                        'default_date': start.format(),
                                        'default_employee_id': resource ? parseInt(resource.id) : 0,
                                        'default_time_from': start.hour() + ":" + start.minute(),
                                        'default_date': start.format(),
                                        'default_product_id': parseInt(service) || false,
                                        'show_footer': 1,
                                        'calendar_booking': true,
                                    },
                                });
                            }
                        },
                        selectOverlap: function (event) {
                        },
                        dayClick: function (date, jsEvent, view, resource) {
                            console.log(date.format(), resource ? resource.id : '(no resource)',"-==========");
                        },
                        eventClick: function (calEvent, jsEvent, view) {
                            
                            if (!calEvent.leave) {
                                
                                self.do_action({
                                    name: 'Reservation Details',
                                    type: 'ir.actions.act_window',
                                    res_model: "spa.booking",
                                    res_id: calEvent.id,
                                    views: [
                                        [false, 'form']
                                    ],
                                    target: 'new',
                                    context: {
                                        'calendar_booking': true,
                                        'show_footer': true,
                                    },
                                });
                            }
                        },
                        schedulerLicenseKey: 'GPL-My-Project-Is-Open-Source',
                    });
                    $("#calendar").on("swipe", function () {
                        $(this).hide();
                    });
                    if (gotoDate) {
                        $('#calendar').fullCalendar('gotoDate', gotoDate);
                    }
                }
            });
        },
    });


    core.action_registry.add('calendar_booking', BookingCalendar);

    return BookingCalendar;
});
