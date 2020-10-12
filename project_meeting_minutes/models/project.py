# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Project(models.Model):
    _inherit = 'project.project'

    @api.multi
    @api.depends()
    def _compute_meeting(self):
        calendar_event = self.env['calendar.event']
        for rec in self:
            meeting = calendar_event.search([('project_id', '=', rec.id)])
            rec.meeting_count = len(meeting)

    meeting_count = fields.Integer(
        compute = '_compute_meeting',
     )


    @api.multi
    def show_jobcost_event(self):
        self.ensure_one()
        res = self.env.ref('calendar.action_calendar_event')
        res = res.read()[0]
        res['domain'] = str([('project_id', '=', self.id)])
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
