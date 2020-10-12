# -*- coding: utf-8 -*-

from odoo import models, fields

class Task(models.Model):
    _inherit = 'project.task'
    
    portal_user_ids = fields.Many2many(
        'res.users',
        string='Timesheet Employee Users',
    )

class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'
    
    is_close = fields.Boolean(
        string='Is Closed',
    )
