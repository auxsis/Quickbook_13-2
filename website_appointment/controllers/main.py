# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# License URL : https://store.webkul.com/license.html/
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################

from odoo import http,_
from odoo.http import request
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_is_zero
import logging, pytz
_logger = logging.getLogger(__name__)

Days = {
    0 : 'monday',
    1 : 'tuesday',
    2 : 'wednesday',
    3 : 'thursday',
    4 : 'friday',
    5 : 'saturday',
    6 : 'sunday',
}

class WebsiteAppointment(http.Controller):

    def get_formatted_lang_date(self, appoint_date):
        lang = request.env['ir.qweb.field'].user_lang()
        appoint_date = datetime.strptime(appoint_date, lang.date_format).strftime(DEFAULT_SERVER_DATE_FORMAT)
        return appoint_date

    @http.route(['/appointment'], type='http',auth='public' , website=True )
    def _get_appointment_page(self, **kw):
        group_id = request.env['appointment.person.group'].sudo().search([])
        lang = request.env['ir.qweb.field'].user_lang()
        return request.render('website_appointment.book_appoint_mgmt_template',
            {
                'group_id'  :    group_id,
                'lang_date_format': lang.date_format,
            })

    @http.route(["/validate/appointment"], type="json", auth="public", website=True)
    def _check_multi_appointments(self, appoint_date, time_slot_id, appoint_person_id):
        result = {}
        appoint_person_obj = request.env["res.partner"].browse(appoint_person_id)
        time_slot_id = request.env["appointment.timeslot"].browse(time_slot_id)
        appoint_date = self.get_formatted_lang_date(appoint_date)
        appoint_date = datetime.strptime(str(appoint_date), DEFAULT_SERVER_DATE_FORMAT).date()

        # case 1: Check for multiple appointment bookings
        if appoint_person_obj and time_slot_id and not appoint_person_obj.allow_multi_appoints:
            appointment_obj = request.env["appointment"].search([
                ("appoint_date",'=', appoint_date),
                ("appoint_person_id",'=', appoint_person_obj.id),
                ("time_slot","=", time_slot_id.id),
            ])
            if appointment_obj:
                return {
                    'status': False,
                    'message': "This slot is already booked for this person at this date. Please select any other."
                }

        # case 2: Check for time slot not available for today
        if appoint_date and time_slot_id:
            rd = relativedelta(date.today(), appoint_date)
            if rd.days == 0 and rd.months == 0 and rd.years == 0:
                time_to = str(time_slot_id.start_time).split('.')
                time_to_hour = str(time_to[0])[:2]
                minutes = int(round((time_slot_id.start_time % 1) * 60))
                if minutes == 60:
                    minutes = 0
                time_to_min = str(minutes).zfill(2)
                current_time = datetime.now().replace(microsecond=0).replace(second=0)
                user_tz = pytz.timezone(appoint_person_obj.tz or 'UTC')
                current_time = pytz.utc.localize(current_time).astimezone(user_tz).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                current_time = datetime.strptime(str(current_time), '%Y-%m-%d %H:%M:%S')
                if current_time.hour > int(time_to_hour):
                    return {
                        'status': False,
                        'message': "This slot is not available for today. Please select any other."
                    }
                if current_time.hour == int(time_to_hour) and current_time.minute >= int(time_to_min):
                    return {
                        'status': False,
                        'message': "This slot is not available for today. Please select any other."
                    }

        return {'status': True,'message': ''}

    @http.route(["/find/appointee/timeslot"], type="json", auth="public", website=True)
    def _get_appoint_person_date_timeslots(self, group_id, appoint_date):
        appoint_date = self.get_formatted_lang_date(appoint_date)
        if appoint_date:
            d1 = datetime.strptime(appoint_date,DEFAULT_SERVER_DATE_FORMAT).date()
            d2 = date.today()
            rd = relativedelta(d2,d1)
            if rd.days > 0 or rd.months > 0 or rd.years > 0:
                return
        app_group_obj = request.env['appointment.person.group'].sudo().search([('id', '=', int(group_id))])
        selected_day = datetime.strptime(appoint_date,DEFAULT_SERVER_DATE_FORMAT).weekday()
        vals = {
            'app_group_obj' : app_group_obj.sudo(),
            'selected_day': Days[selected_day],
            'appoint_date': appoint_date,
            'website_show_tz': request.env['ir.default'].sudo().get('res.config.settings', 'website_show_tz'),
        }
        return request.env['ir.ui.view'].render_template('website_appointment.appointee_listing_template', vals)

    @http.route("/appointment/book", type="http", auth="public", website=True )
    def _book_appointment(self, **appoint_dict):
        if appoint_dict=={}:
            return request.redirect("/appointment")
        customer = request.env.user.partner_id
        appoint_group = request.env['appointment.person.group'].sudo().search([('id', '=', int(appoint_dict.get('appoint_groups', False)))])
        appoint_person = request.env['res.partner'].sudo().search([('id', '=', int(appoint_dict.get('appoint_person', False)))])
        appoint_date = appoint_dict.get('appoint_date', False)
        appoint_slot = request.env['appointment.timeslot'].sudo().search([('id', '=', int(appoint_dict.get('appoint_timeslot_id', False)))])
        appoint_date = self.get_formatted_lang_date(appoint_date)
        # appoint_day = datetime.strptime(appoint_date, DEFAULT_SERVER_DATE_FORMAT).strftime("%A")
        appoint_charge = 0
        if appoint_person and appoint_person.appoint_person_charge > 0:
            appoint_charge = appoint_person.appoint_person_charge
        else:
            if appoint_group and appoint_group.group_charge > 0:
                appoint_charge = appoint_group.group_charge
        vals = {
            'customer': customer,
            'appoint_group':appoint_group,
            'appoint_person': appoint_person,
            'appoint_date': appoint_date,
            # 'appoint_day': dict(appoint_slot._fields['day'].selection).get(appoint_slot.day),
            'appoint_slot': appoint_slot,
            'appoint_charge': appoint_charge,
        }
        if appoint_dict.get('appoint_error'):
            vals.update({
                'appoint_error' : appoint_dict.get('appoint_error'),
            })
        return request.render('website_appointment.confirm_book_appoint_mgmt_template', vals)

    @http.route("/appointment/confirmation", type="http", auth="public", website=True )
    def _confirm_appointment(self, **post):
        if post == {}:
            return request.redirect("/appointment")
        try:
            customer = request.env.user.partner_id
            appoint_group = request.env['appointment.person.group'].sudo().search([('id', '=', int(post.get('appoint_group', False)))])
            appoint_person = request.env['res.partner'].sudo().search([('id', '=', int(post.get('appoint_person', False)))])
            appoint_date = post.get('appoint_date', False)
            appoint_slot = request.env['appointment.timeslot'].sudo().search([('id', '=', int(post.get('appoint_slot', False)))])
            pricelist_id = False
            irmodule_obj = request.env['ir.module.module']
            module_installed = irmodule_obj.sudo().search([('name', 'in', ['website_sale']), ('state', 'in', ['installed'])])
            if module_installed:
                pricelist_id = request.website.get_current_pricelist()
            else:
                pricelist_id = customer.property_product_pricelist
            currency_id = pricelist_id.currency_id.id if pricelist_id else False
            vals = {
                'customer': customer.id,
                'pricelist_id': pricelist_id.id,
                'currency_id': currency_id,
                'appoint_group_id': appoint_group.id,
                'appoint_person_id': appoint_person.id,
                'appoint_date': appoint_date,
                'time_slot': appoint_slot.id,
                'appoint_state': 'new',
                'description' : post.get("appoint_desc", False) if post.get("appoint_desc") else ''
            }
            appoint_obj = request.env['appointment'].sudo().with_context(website_appoint=True).create(vals)

            appoint_charge = 0
            name = ""
            if appoint_person and appoint_person.appoint_person_charge > 0:
                appoint_charge = appoint_person.appoint_person_charge
                name = "Charge for Appointment Person"
            else:
                if appoint_group and appoint_group.group_charge > 0:
                    appoint_charge = appoint_group.group_charge
                    name = "Charge for Appointment Group"
            if appoint_charge > 0:
                appoint_line = {
                    'appoint_product_id': appoint_group.product_tmpl_id.product_variant_id.id if appoint_group else False,
                    'tax_id': [(6, 0, appoint_group.product_tmpl_id.product_variant_id.taxes_id.ids)],
                    'appoint_id': appoint_obj.id,
                    'name': name,
                    'price_unit': appoint_charge,
                }
                appoint_lines = request.env['appointment.lines'].sudo().create(appoint_line)
            else:
                appoint_line = {
                    'appoint_product_id': appoint_group.product_tmpl_id.product_variant_id.id if appoint_group else False,
                    'tax_id': [(6, 0, appoint_group.product_tmpl_id.product_variant_id.taxes_id.ids)],
                    'appoint_id': appoint_obj.id,
                    'name': "Appointment Free of Charge",
                    'price_unit': 0.0,
                    'product_qty' : 1.0,
                    'price_subtotal': 0.0,
                }
                appoint_lines = request.env['appointment.lines'].sudo().create(appoint_line)
        except Exception as e:
            _logger.info("----------------- Some Error Occurred : %r ----------------", e )
            # return request.redirect(request.httprequest.referrer + "?appoint_error=1")
            return request.redirect("/appointment")
        return request.redirect("/my/appointments/" + str(appoint_obj.id))
