# -*- coding: utf-8 -*-

from odoo import models, api


class CostSheet(models.Model):
    _inherit = 'job.costing'

    @api.multi
    def show_budget_line(self):
        res = self.env.ref('odoo_account_budget.analytic_act_crossovered_budget_lines_view')
        res = res.read()[0]
        res['domain'] = str([('costsheet_id.id', '=', self.id)])
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
