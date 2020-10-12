# -*- coding: utf-8 -*

from odoo import models, fields, api

class ServiceNature(models.Model):
    _name = 'service.nature'
    
    name = fields.Char(
       string="Name",
       required=True,
    )