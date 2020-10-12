# -*- coding: utf-8 -*-

from odoo import fields, models, api


class Task(models.Model):
    _inherit = "project.task"

    @api.multi
    def show_inspection(self):
        self.ensure_one()
        res = self.env.ref('job_inspection.action_job_order_inspection')
        res = res.read()[0]
        res['domain'] = str([('task_id','=', self.id)])
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
