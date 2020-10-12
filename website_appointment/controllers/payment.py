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
from odoo.addons.portal.controllers.portal import _build_url_w_params
from odoo.addons.payment.controllers.portal import PaymentProcessing
from odoo.http import request, route
import logging
_logger = logging.getLogger(__name__)

class PaymentPortal(http.Controller):

    @route('/appointments/pay/<int:appoint_id>/form_tx', type='json', auth="public", website=True)
    def appoint_pay_form(self, acquirer_id, appoint_id, save_token=False, access_token=None, **kwargs):
        success_url = kwargs.get('success_url', '/my/appointments')
        # callback_method = kwargs.get('callback_method', '')

        appoint_sudo = request.env['appointment'].sudo().browse(appoint_id)
        if not appoint_sudo:
            return False

        try:
            acquirer = int(acquirer_id)
        except:
            return False
        if request.env.user._is_public():
            save_token = False # we avoid to create a token for the public user
        vals = {
            'acquirer_id': acquirer_id,
            'return_url': success_url,
        }

        if save_token:
            vals['type'] = 'form_save'

        transaction = appoint_sudo._create_payment_transaction(vals)
        PaymentProcessing.add_payment_transaction(transaction)

        return transaction.render_appoint_button(
            appoint_sudo,
            submit_txt=_('Pay & Confirm'),
            render_values={
                'type': 'form_save' if save_token else 'form',
                'alias_usage': _('If we store your payment information on our server, subscription payments will be made automatically.'),
            }
        )


    @http.route('/appointments/pay/<int:appoint_id>/s2s_token_tx', type='http', auth='public', website=True)
    def appoint_pay_token(self, appoint_id, pm_id=None, **kwargs):
        error_url = kwargs.get('error_url', '/my')
        success_url = kwargs.get('success_url', '/my')
        access_token = kwargs.get('access_token')
        params = {}
        if access_token:
            params['access_token'] = access_token

        appoint_sudo = request.env['appointment'].sudo().browse(appoint_id).exists()
        if not appoint_sudo:
            params['error'] = 'pay_appoint_invalid_doc'
            return request.redirect(_build_url_w_params(error_url, params))

        try:
            token = request.env['payment.token'].sudo().browse(int(pm_id))
        except (ValueError, TypeError):
            token = False
        token_owner = appoint_sudo.customer if request.env.user._is_public() else request.env.user.partner_id
        if not token or token.partner_id != token_owner:
            params['error'] = 'pay_invoice_invalid_token'
            return request.redirect(_build_url_w_params(error_url, params))

        vals = {
            'payment_token_id': token.id,
            'type': 'server2server',
            'return_url': success_url,
        }

        tx = appoint_sudo._create_payment_transaction(vals)
        PaymentProcessing.add_payment_transaction(tx)

        params['success'] = 'pay_invoice'
        return request.redirect(_build_url_w_params(success_url, params))
