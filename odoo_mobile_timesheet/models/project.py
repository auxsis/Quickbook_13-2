# -*- coding: utf-8 -*-

from odoo import models, fields

class Project(models.Model):
    _inherit = 'project.project'
    
    portal_user_ids = fields.Many2many(
        'res.users',
        string='Timesheet Employee Users',
    )
    is_close = fields.Boolean(
        string='Hide Project',
    )
