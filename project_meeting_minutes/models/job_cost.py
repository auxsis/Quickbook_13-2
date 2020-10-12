# -*- coding: utf-8 -*-

from odoo import models, fields, api


class JobCost(models.Model):
    _inherit = 'job.costing'

    @api.multi
    @api.depends()
    def _compute_meeting(self):
        calendar_event = self.env['calendar.event']
        for rec in self:
            meeting = calendar_event.search([('project_id', '=', rec.project_id.id), ('analytic_id', '=', rec.analytic_id.id), ('task_id', '=', rec.task_id.id), ('costsheet_id', '=', rec.id)])
            rec.event_count = len(meeting)

    event_count = fields.Integer(
        compute = '_compute_meeting',
        default=0,
     )

    @api.multi
    def show_jobcost_event(self):
        self.ensure_one()
        res = self.env.ref('calendar.action_calendar_event')
        res = res.read()[0]
        res['domain'] = str([('costsheet_id', '=', self.id)])
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
