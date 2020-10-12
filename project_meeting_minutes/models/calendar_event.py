# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    analytic_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
    )
    project_id = fields.Many2one(
        'project.project',
        string='Project',
    )
    task_id = fields.Many2one(
        'project.task',
        string='Job Order',
    )
    costsheet_id = fields.Many2one(
        'job.costing',
        string='Job Cost Sheet',
    )
    costsheet_line_id = fields.Many2one(
        'job.cost.line',
        string='Job Cost Sheet Line',
    )
    timesheet_ids = fields.One2many(
        'account.analytic.line',
        'calendar_id',
        string='Timesheet Line'
    )

    @api.onchange('project_id')
    def _onchange_project_id(self):
        for rec in self:
            rec.analytic_id = rec.project_id.analytic_account_id.id

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
