# -*- coding: utf-8 -*

from odoo import models, fields, api

class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    brand = fields.Char(
        string = "Brand"
    )
    color = fields.Char(
        string = "Color"
    )
    model = fields.Char(
        string="Model"
    )
    year = fields.Integer(
        string="Year"
    )
    is_machine = fields.Boolean(
        string="Is Machine"
    )
