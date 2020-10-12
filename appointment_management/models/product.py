# -*- coding: utf-8 -*-

from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.product'
    
    is_appointment = fields.Boolean(
        string='Is Appointment ?',
        default=False,
        copy = False,
    )
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
