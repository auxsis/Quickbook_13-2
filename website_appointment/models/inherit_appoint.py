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

from odoo import models, fields, _,api
from odoo.exceptions import ValidationError
from odoo.addons.base.models.res_partner import _tz_get
import logging
_logger = logging.getLogger(__name__)

class Appointment(models.Model):
    _inherit = "appointment"

    tz = fields.Selection(_tz_get, string='Timezone', related="appoint_person_id.tz")
    transaction_ids = fields.Many2many('payment.transaction', 'appointment_transaction_rel', 'appoint_id', 'transaction_id',
                                       string='Transactions', copy=False, readonly=True)
    authorized_transaction_ids = fields.Many2many('payment.transaction', compute='_compute_authorized_transaction_ids',
                                                  string='Authorized Transactions', copy=False, readonly=True)

    payment_tx_ids = fields.One2many('payment.transaction', 'appointment_id', string='Transactions')
    payment_tx_id = fields.Many2one('payment.transaction', string='Last Transaction', copy=False)
    payment_acquirer_id = fields.Many2one(
        'payment.acquirer', string='Payment Acquirer',
        related='payment_tx_id.acquirer_id', store=True)
    payment_tx_count = fields.Integer(string="Number of payment transactions", compute='_compute_payment_tx_count')

    def _compute_payment_tx_count(self):
        tx_data = self.env['payment.transaction'].read_group(
            [('appointment_id', 'in', self.ids)],
            ['appointment_id'], ['appointment_id']
        )
        mapped_data = dict([(m['appointment_id'][0], m['appointment_id_count']) for m in tx_data])
        for appoint in self:
            appoint.payment_tx_count = mapped_data.get(appoint.id, 0)

    def action_view_transactions(self):
        action = {
            'name': _('Payment Transactions'),
            'type': 'ir.actions.act_window',
            'res_model': 'payment.transaction',
            'target': 'current',
        }
        tx = self.env['payment.transaction'].search([('appointment_id', 'in', self.ids)])
        if len(tx) == 1:
            action['res_id'] = tx.ids[0]
            action['view_mode'] = 'form'
        else:
            action['view_mode'] = 'tree,form'
            action['domain'] = [('appointment_id', 'in', self.ids)]
        return action

    def _create_payment_transaction(self, vals):
        '''Similar to self.env['payment.transaction'].create(vals) but the values are filled with the
        current appointment fields (e.g. the partner or the currency).
        :param vals: The values to create a new payment.transaction.
        :return: The newly created payment.transaction record.
        '''
        # Ensure the currencies are the same.
        self.ensure_one()
        currency = self[0].currency_id
        if any([appoint.currency_id != currency for appoint in self]):
            raise ValidationError(_('A transaction can\'t be linked to appointment having different currencies.'))

        # Ensure the partner are the same.
        partner = self[0].customer
        if any([appoint.customer != partner for appoint in self]):
            raise ValidationError(_('A transaction can\'t be linked to appointment having different partners.'))

        # Try to retrieve the acquirer. However, fallback to the token's acquirer.
        acquirer_id = vals.get('acquirer_id')
        acquirer = None
        payment_token_id = vals.get('payment_token_id')

        if payment_token_id:
            payment_token = self.env['payment.token'].sudo().browse(payment_token_id)

            # Check payment_token/acquirer matching or take the acquirer from token
            if acquirer_id:
                acquirer = self.env['payment.acquirer'].browse(acquirer_id)
                if payment_token and payment_token.acquirer_id != acquirer:
                    raise ValidationError(_('Invalid token found! Token acquirer %s != %s') % (
                    payment_token.acquirer_id.name, acquirer.name))
                if payment_token and payment_token.partner_id != partner:
                    raise ValidationError(_('Invalid token found! Token partner %s != %s') % (
                    payment_token.partner.name, partner.name))
            else:
                acquirer = payment_token.acquirer_id

        # Check an acquirer is there.
        if not acquirer_id and not acquirer:
            raise ValidationError(_('A payment acquirer is required to create a transaction.'))

        if not acquirer:
            acquirer = self.env['payment.acquirer'].browse(acquirer_id)

        # Check a journal is set on acquirer.
        if not acquirer.journal_id:
            raise ValidationError(_('A journal must be specified of the acquirer %s.' % acquirer.name))

        if not acquirer_id and acquirer:
            vals['acquirer_id'] = acquirer.id

        vals.update({
            'amount': self[0].amount_total,
            'currency_id': currency.id,
            'partner_id': partner.id,
            'appointment_id': self[0].id,
            'acquirer_id': acquirer.id,
            'type': 'form',
            'amount': self.amount_total,
            'currency_id': self.currency_id.id,
            'partner_id': self.customer.id,
            'partner_country_id': self.customer.country_id.id,
        })

        transaction = self.env['payment.transaction'].create(vals)

        # Process directly if payment_token
        if transaction.payment_token_id:
            transaction.s2s_do_transaction()

        return transaction

    def _compute_portal_url(self):
        super(Appointment, self)._compute_portal_url()
        for appoint in self:
            appoint.portal_url = '/my/appointments/%s' % (appoint.id)

    def _compute_access_url(self):
        super(Appointment, self)._compute_access_url()
        for appoint in self:
            appoint.access_url = '/my/appointments/%s' % (appoint.id)

    @api.depends('transaction_ids')
    def _compute_authorized_transaction_ids(self):
        for trans in self:
            trans.authorized_transaction_ids = trans.transaction_ids.filtered(lambda t: t.state == 'authorized')

    def get_portal_last_transaction(self):
        self.ensure_one()
        return self.transaction_ids.get_last_transaction()

    def payment_action_capture(self):
        for rec in self:
            self.authorized_transaction_ids.s2s_capture_transaction()

    def payment_action_void(self):
        for rec in self:
            self.authorized_transaction_ids.s2s_void_transaction()

    @api.model
    def set_default_source(self):
        source = super(Appointment, self).set_default_source()
        if self._context.get("website_appoint"):
            try:
                source = self.env.ref('wk_appointment.appoint_source3')
            except Exception as e:
                pass
        return source
