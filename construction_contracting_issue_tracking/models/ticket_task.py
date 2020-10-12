# -*- coding: utf-8 -*-

from odoo import models, fields

class ProjectTask(models.Model):
    _inherit = "project.task"
    
    construction_ticket_id = fields.Many2one(
        'construction.ticket',
        string='Construction Issue',
        readonly=True,
        copy=False,
    )
  
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

