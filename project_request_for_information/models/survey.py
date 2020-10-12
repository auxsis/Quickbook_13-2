# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api

class Survey(models.Model):
    _inherit = "survey.survey"
    
    rfi_request_id = fields.Many2one(
        'request.information',
        string='Request for Information',
    )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
