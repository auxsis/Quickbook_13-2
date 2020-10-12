# -*- coding: utf-8 -*-

from odoo import models, fields

class AnalyticLine(models.Model):
    _inherit = "account.analytic.line"
    
    rfi_time_in = fields.Float(
        string='Time In',
    )
    rfi_time_out = fields.Float(
        string='Time Out',
    )
    rfi_request_information_id = fields.Many2one(
        'request.information',
        domain=[('is_close','=',False)],
        string='Request Information',
    )
    rfi_billable = fields.Boolean(
        string='Billable',
        default=True,
    )
