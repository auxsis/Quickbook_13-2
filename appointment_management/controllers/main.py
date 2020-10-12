# -*- coding: utf-8 -*-

import pytz
from pytz import timezone
from datetime import datetime
import time
from odoo import http, modules, tools
from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.http import request
from odoo.addons.website.controllers.main import QueryURL
import logging
_logger = logging.getLogger(__name__)

weekdays = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
class AppointmentCreate(http.Controller):
    @http.route(['/page/appointment/'], auth='user', website=True, csrf=True)
    def get_appointee(self, **kw):
        partner_obj = http.request.env['res.partner']
        appointees = partner_obj.sudo().search([('is_available_for_apointment','=',True)])
        values = {
            'appointee_ids' : appointees,
        }
        return request.render('appointment_management.website_appointment1',values)

    def _convert_to_utc(self, localdatetime=None, appointee_id=None):
        check_in_date = datetime.strptime(localdatetime, "%Y-%m-%d  %H:%M:%S")
        
        timezone_tz = 'utc'
        user_id = request.env['res.users'].sudo().search([('partner_id', '=', int(appointee_id))])
        super_user = request.env['res.users'].sudo().browse(SUPERUSER_ID)
        if user_id.tz:
            timezone_tz = user_id.tz
        elif super_user.tz:
            timezone_tz = super_user.tz
        
        local = pytz.timezone(timezone_tz)#request.env.user.tz
        local_dt = local.localize(check_in_date, is_dst=None)
        utc_datetime = local_dt.astimezone(pytz.utc)
        return utc_datetime

    def get_appointment_slots(self, start_date, appointee_id):
        datetime_object = datetime.strptime(
            start_date, '%Y-%m-%d'
        ).strftime('%Y-%m-%d')
        week_day = fields.Date.from_string(
            datetime_object
        ).weekday()
        slot_obj = http.request.env['meeting.slot']
        event_obj = request.env['calendar.event']
        # partner_obj = http.request.env['res.partner']

        day = weekdays[week_day]
        day_match = slot_obj.sudo().search([('day','=', day)])

        print ("appoint------------------",appointee_id)
        date_start = datetime.strptime(
            start_date, '%Y-%m-%d'
        ).strftime('%Y-%m-%d')
        dict_my = {}
        for day_m in day_match.slot_line_ids:
            day_slot = date_start +' '+day_m.time+':00'
            start_datetime = self._convert_to_utc(
                day_slot, appointee_id
            ).strftime("%Y-%m-%d %H:%M:%S")
            book_slots = event_obj.sudo().search([
                ('partner_ids', 'in', [appointee_id]),
                ('slot','=', tools.ustr(day_m.time)),
                ('start_datetime', '=', start_datetime)
            ])

            if book_slots:
                dict_my[day_m.time] = True
            else:
                dict_my[day_m.time] = False
        return day_match,dict_my

    @http.route(['/appointment_management/appointment_get'], type='http', auth="public", methods=['POST'], website=True)
    def appointment_get(self, **post):
        start_date = post['start_date']
        appointee_id = post.get('appointee_id', False) 
        day_match,dict_my = self.get_appointment_slots(
            start_date, appointee_id
        )
        partner_obj = http.request.env['res.partner']
        appointees = partner_obj.sudo().search([
            ('is_available_for_apointment','=',True)
        ])

        if dict_my:
             _logger.info("\n-------------------------Slots are %s-----------------------"%(dict_my))
        else:
            _logger.info("\n-------------------------No any Slots Available-----------------------")
        slot_values = {
        'name' : post['customer_id'],
        'email' : post['email'],
        'phone' : post['phone'],
        'purpose' : post['purpose'],
        'description' : tools.ustr(post['description']),
        'purpose' : post['purpose'],
        'date' : post['start_date'],
        'day':day_match,
        'dict_my':dict_my,
        'appointee_ids' : appointees,
        'appointee_id': int(appointee_id)
        }
        return http.request.render('appointment_management.website_appointment1',slot_values)

    @http.route(['/appointment_management/appointment_confirm'], auth="public", type='http',website=True)
    def confirm(self, **post):
        time = post['slot']
        appointee_id = post.get('appointee_id', False)
        date_start = datetime.strptime(post['start_date'], '%Y-%m-%d').strftime('%Y-%m-%d')
        day_slot = date_start +' '+time+':00'
        event_obj = request.env['calendar.event']
        partner_obj = http.request.env['res.partner']
        slot_obj = http.request.env['meeting.slot']

        #For Check slot available or not 
        appointee = partner_obj.sudo().browse(int(appointee_id))
        start_date = post.get('start_date', False)
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
#        print ("fields.Date.from_string(datetime_object).weekday():::::::::::::",fields.Datetime.from_string(date_start).weekday())
        week_day = start_date.weekday()
        day = weekdays[week_day]
        slot_time = str(tools.ustr(time))
        print("=====================>>\n\n\n",day)
        slot_time_split = slot_time.split(':')
        print("=====================>>\n\n\n",slot_time_split)
        if slot_time_split and len(slot_time_split[0]) == 1:
            slot_time = '0'+ slot_time
        day_match = slot_obj.sudo().search([('day','=', day)])
        print("=====================>>\n\n\n",day_match)
        slot_exist = day_match.slot_line_ids.filtered(lambda j: j.time == slot_time)
        slot_exist = http.request.env['meeting.slot.line'].sudo().search([('slot_id', '=', day_match.id),('time', '=', tools.ustr(time))])
        print("=========jjj============>>\n\n\n",slot_exist)
        if not slot_exist:
            print("=========jjjesh============>>\n\n\n",slot_exist)
            msg = "Incorrect slot: %s. \n Please enter valid slot from slot table." %(tools.ustr(time))
            return request.render('appointment_management.time_slot_validation_template', {'slot_time': tools.ustr(time),
                                                                                           'warn_for': 'incorrect_slot'})
        
        
        
        start_datetime = False
        try:
            start_datetime = self._convert_to_utc(day_slot, appointee_id)
        except:
            start_datetime = False
            
        if not start_datetime:
            return request.render('appointment_management.time_slot_validation_template', {'warn_for': 'slot_validation'})

#         start_datetime = self._convert_to_utc(day_slot, appointee_id)
        start_datetime_strf = start_datetime.strftime("%Y-%m-%d %H:%M:%S")
        print("vbnm",start_datetime_strf)
        book_slots = event_obj.sudo().search([('partner_ids', 'in', [appointee_id]),
                                              ('slot','=', tools.ustr(time)),
                                              ('start_datetime', '=', start_datetime_strf)])
        print("fgb",book_slots)
        if appointee_id:
            print("===============>>\n\n\n")
            for book_slot in book_slots:
                partner_match = partner_obj.sudo().search([('is_available_for_apointment','=',True)])
                for person in book_slot.partner_ids:
                    for p in partner_match:
                        if person == p:
                            return http.request.render('appointment_management.book_slot')
        partner_ids = []
        if int(appointee_id) not in partner_ids:
            partner_ids.append(int(appointee_id))

        if request.env.user.partner_id.id not in partner_ids:
            partner_ids.append(request.env.user.partner_id.id)

        appointment = http.request.env['calendar.event'].sudo().create({
                                                    'name': post['purpose'],
                                                    'customer_name': request.env.user.partner_id.id,
                                                    'email': post['email'],
                                                    'phone': post['phone'],
                                                    'description': post['description'],
                                                    'partner_ids' : [(6, 0, partner_ids)],
                                                    'start_datetime' : start_datetime_strf,
                                                    'stop_datetime' : start_datetime_strf,
                                                    'start': start_datetime_strf,
                                                    'stop': start_datetime_strf,
                                                    'slot': tools.ustr(time),
                                                    'duration':0.0,
                                                    'appointee_id': appointee_id,
                                                    # 'company_name':request.env.user.company_id.name
                                                     })
        print("===============>>\n\n\n",appointment)
        partner_id = partner_obj.sudo().browse(int(appointee_id))
        date = fields.Date.from_string(date_start).strftime('%a %b %d, %Y') + ' ' + time
        print("===============>>\n\n\n",date)
        user_id = request.env.user.name
        local_context = http.request.env.context.copy()
        issue_template = http.request.env.ref('appointment_management.email_template_appointment_book')
#         local_context.update({
#             'partner_email': partner_id.email,
#             'user_id': user_id,
#             'partner_name': partner_id.name,
#             'date': date,
#             'customer_name': appointment.user_id.name,
#             'customer_email': appointment.user_id.partner_id.email,
#             'customer_phone': appointment.user_id.partner_id.phone,
#             'subject': appointment.name,
#             'book_id': appointment.booking_id,
#             'note' : appointment.description,
#         })
        local_context.update({
           'partner_email': partner_id.email,
           'user_id': user_id,
           'partner_name': partner_id.name,
           'date': date,
           'customer_name': appointment.customer_name.name,
           'customer_email': appointment.email,
           'customer_phone': appointment.phone,
           'subject': appointment.name,
           'book_id': appointment.booking_id,
           'note' : appointment.description,
       })
        issue_template.sudo().with_context(local_context).send_mail(request.uid, force_send=True)
        values = {
                'appointment':appointment,
                'company_name':request.env.user.company_id.name,
            }
        return request.render('appointment_management.thanks_submit_template', values)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

