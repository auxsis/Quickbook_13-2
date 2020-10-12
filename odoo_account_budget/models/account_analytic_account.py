# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

#    crossovered_budget_line = fields.One2many('crossovered.budget.lines', 'analytic_account_id', 'Budget Lines')
    crossovered_budget_line_ids = fields.One2many(
        'account.analytic.crossovered.budget.lines',
        'analytic_account_id',
        string='Budget Lines',
    )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
