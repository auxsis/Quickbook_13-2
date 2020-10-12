# -*- coding: utf-8 -*-

from odoo import models, fields

class Partner(models.Model):
    _inherit = 'res.partner'
    
#     code = fields.Char(
#         string='Code',
#         copy = False,
#     )
    is_available_for_apointment = fields.Boolean(
        'Available for Appointment?',
        copy=False,
    )
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
