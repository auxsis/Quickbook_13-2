# -*- coding: utf-8 -*-

from odoo import fields, models, api

class ProjectTask(models.Model):
    _inherit = 'project.task'
    
    @api.multi
    def view_repair_requests(self):
        self.ensure_one()
        action = self.env.ref('machine_repair_management.action_machine_repair_support').read()[0]
        action['domain'] = [('task_id', '=', self.id)]
        return action

