# -*- coding: utf-8 -*-

from odoo import models, fields

class AttachmentTag(models.Model):
    _name = 'attachment.tag'
    
    name = fields.Char(
        string='Name',
        required=True,
    )
    color = fields.Integer(
        string='Color Index'
    )