# -*- coding: utf-8 -*

from odoo import models, fields, api

class JobCosting(models.Model):
    _inherit = 'job.costing'

    @api.multi
    def action_open_construction_task_ticket(self):
        for rec in self:
            action = self.env.ref('construction_contracting_issue_tracking.action_construction_ticket')
            action = action.read()[0]
            action['domain'] = str([('jobcost_sheet_id','=',rec.id)])
        return action
