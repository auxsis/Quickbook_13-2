# -*- coding: utf-8 -*

from odoo import models, fields, api

class Repairtype(models.Model):
    _name = 'repair.type'
    
    name = fields.Char(
        string="Name",
        required=True,
    )
    code = fields.Char(
        string="Code",
        required=True,
    )
    service_id = fields.Many2one(
        'service.nature',
        string="Service"
    )
