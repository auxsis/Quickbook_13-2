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

from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.tools import consteq
import logging
_logger = logging.getLogger(__name__)

class PortalAccount(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(PortalAccount, self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        my_appoint_count = request.env['appointment'].search_count([
            ('customer', '=', partner.id),
        ])
        values['my_appoint_count'] = my_appoint_count
        return values

    # ------------------------------------------------------------
    # My Appointments
    # ------------------------------------------------------------

    def _appointments_check_access(self, appoint_id, access_token=None):
        appointments = request.env['appointment'].browse([appoint_id])
        appointments_sudo = appointments.sudo()
        try:
            appointments.check_access_rights('read')
            appointments.check_access_rule('read')
        except AccessError:
            if not access_token or not consteq(appointments_sudo.access_token, access_token):
                raise
        return appointments_sudo

    def _appointments_get_page_view_values(self, appointment, access_token, **kwargs):
        values = {
            'page_name': 'appoint_mgmt',
            'appointment': appointment,
        }
        if access_token:
            values['no_breadcrumbs'] = True
        if kwargs.get('error'):
            values['error'] = kwargs['error']
        if kwargs.get('warning'):
            values['warning'] = kwargs['warning']
        if kwargs.get('success'):
            values['success'] = kwargs['success']

        history = request.session.get('my_appointments_history', [])
        values.update(get_records_pager(history, appointment))
        values.update(request.env['payment.acquirer']._get_available_payment_input(appointment.customer, appointment.customer.company_id))

        #for payment ---- ref-> account_payment module
        payment_inputs = request.env['payment.acquirer']._get_available_payment_input(company=appointment.customer.company_id)
        # if not connected (using public user), the method _get_available_payment_input will return public user tokens
        is_public_user = request.env.user._is_public()
        if is_public_user:
            # we should not display payment tokens owned by the public user
            payment_inputs.pop('pms', None)
            token_count = request.env['payment.token'].sudo().search_count([('acquirer_id.company_id', '=', appointment.customer.company_id.id),
                                                                      ('partner_id', '=', appointment.customer.id),
                                                                    ])
            values['existing_token'] = token_count > 0
        values.update(payment_inputs)
        values['partner_id'] = appointment.customer if is_public_user else request.env.user.partner_id,

        return values

    @http.route(['/my/appointments', '/my/appointments/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_appointments(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        AppointmentsObj = request.env['appointment']

        domain = [
            ('customer', '=', partner.id),
        ]

        searchbar_sortings = {
            'create_date': {'label': _('Create Date'), 'order': 'create_date asc'},
            'appoint_date': {'label': _('Appointment Date'), 'order': 'appoint_date asc'},
            'name': {'label': _('Appointment Id'), 'order': 'name asc'},
        }
        # default sort by order
        if not sortby:
            sortby = 'create_date'
        order = searchbar_sortings[sortby]['order']

        archive_groups = self._get_archive_groups('appointment', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        appointments_count = AppointmentsObj.search_count(domain)

        # make pager
        pager = request.website.pager(
            url="/my/appointments",
            url_args={'date_begin': date_begin, 'date_end': date_end},
            total=appointments_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        appointments = AppointmentsObj.search(domain, limit=self._items_per_page, offset=pager['offset'], order=order)
        request.session['my_appointments_history'] = appointments.ids[:100]

        values.update({
            'date': date_begin,
            'appoint_obj': appointments.sudo(),
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/appointments',
            'page_name': 'appoint_mgmt',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("website_appointment.portal_my_appointments", values)


    @http.route(['/my/appointments/<int:appoint_id>'], type='http', auth="user", website=True)
    def portal_my_appointment_detail(self, appoint_id=None, access_token=None, **kw):
        app = request.env['appointment'].browse([appoint_id])
        if not app.exists():
            return request.render('website.404')
        try:
            appointments_sudo = self._appointments_check_access(appoint_id, access_token)
        except AccessError:
            return request.redirect('/my')
        values = self._appointments_get_page_view_values(appointments_sudo, access_token, **kw)

        # for payment mode
        payment_mode = request.env['ir.default'].sudo().get('res.config.settings', 'website_appoint_payment_mode')
        show_cancel_booking = request.env['ir.default'].sudo().get('res.config.settings', 'show_cancel_booking')
        values.update({'payment_mode' : payment_mode if payment_mode else False, 'show_cancel_booking': show_cancel_booking,})
        if payment_mode == 'after_appoint':
            appointment_obj = request.env['appointment'].sudo().browse(appoint_id)
            if appointment_obj.appoint_state == 'new':
                appointment_obj.appoint_state = 'pending'
        return request.render("website_appointment.portal_my_appointments_page", values)

    @http.route(['/my/appointments/pdf/<int:appoint_id>'], type='http', auth="public", website=True)
    def portal_my_appointment_report(self, appoint_id, access_token=None, **kw):
        try:
            appointments_sudo = self._appointments_check_access(appoint_id, access_token)
        except AccessError:
            return request.redirect('/my')
        pdf = request.env.ref('wk_appointment.appoint_mgmt_appoint_report').sudo().render_qweb_pdf([appointments_sudo.id])[0]
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)

    @http.route(["/cancel/booking"], type="json", auth="public", website=True)
    def _cancel_booking(self, appoint_id, reason='', **kw):
        if appoint_id:
            appoint_id = request.env['appointment'].browse(int(appoint_id))
            reason =  "Appointment cancelled by customer : " + reason
            appoint_id.reject_appoint(reason)
            return True
        return False
