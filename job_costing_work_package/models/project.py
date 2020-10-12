# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class Project(models.Model):
    _inherit = "project.project"

    @api.multi
    def action_project_package(self):
        self.ensure_one()
        action = self.env.ref("job_costing_work_package.project_work_pacakges_action").read([])[0]
        action['domain'] = [('project_id', 'in', self.ids)]
        return action


class ProjectTask(models.Model):
    _inherit = "project.task"

    @api.multi
    def action_task_package(self):
        self.ensure_one()
        action = self.env.ref("job_costing_work_package.project_work_pacakges_action").read([])[0]
        action['domain'] = [('task_ids', 'in', self.ids)]
        return action