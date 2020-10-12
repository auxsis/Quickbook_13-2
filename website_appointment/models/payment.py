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

import logging
from odoo import fields, models, _,api
from odoo.tools import float_compare
_logger = logging.getLogger(__name__)

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    appointment_id = fields.Many2one('appointment', string='Appointment')

    def render_appoint_button(self, appoint, submit_txt=None, render_values=None):
        values = {
            'partner_id': appoint.customer.id,
        }
        # update appointment state
        if self.env['ir.default'].sudo().get('res.config.settings', 'website_appoint_payment_mode') == 'before_appoint':
            appoint.appoint_state = 'pending' if appoint.appoint_state == 'new' else appoint.appoint_state
        if render_values:
            values.update(render_values)
        return self.acquirer_id.with_context(submit_class='btn btn-primary', submit_txt=submit_txt or _('Pay Now')).sudo().render(
            self.reference,
            appoint.amount_total,
            appoint.currency_id.id,
            values=values,
        )

    @api.model
    def _compute_reference_prefix(self, values):
        res = super(PaymentTransaction, self)._compute_reference_prefix(values)
        if values and values.get('appointment_id'):
            many_list = self.resolve_2many_commands('appointment_id', [values['appointment_id']], fields=['name'])
            return ','.join(dic['name'] for dic in many_list)
        return res
