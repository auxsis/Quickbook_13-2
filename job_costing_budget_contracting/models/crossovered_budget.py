# -*- coding: utf-8 -*-

from odoo import models, api


class CrossOveredBudget(models.Model):
    _inherit = 'account.analytic.crossovered.budget'
    
    @api.multi
    def show_costsheet(self):
        self.ensure_one()
        costsheet_ids = []
        for rec in self:
            for line in rec.crossovered_budget_line:
                costsheet_ids.append(line.costsheet_id.id)
        res = self.env.ref('odoo_job_costing_management.action_job_costing')
        res = res.read()[0]
        res['domain'] = str([('id', 'in', costsheet_ids)])
        return res

    @api.multi
    def show_costsheet_line(self):
        self.ensure_one()
        sheetline_ids = []
        for rec in self:
            for line in rec.crossovered_budget_line:
                sheetline_ids.append(line.jobcost_line_id.id)
        res = self.env.ref('job_costing_budget_contracting.action_cost_sheet_line')
        res = res.read()[0]
        res['domain'] = str([('id', 'in', sheetline_ids)])
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
