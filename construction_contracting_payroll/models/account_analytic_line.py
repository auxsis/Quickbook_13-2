# -*- coding: utf-8 -*-

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import fields, models, api


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    is_payroll_paid = fields.Boolean(
        string='Is Payroll Paid',
        readonly=True,
    )
    custom_payslip_id = fields.Many2one(
        'hr.payslip',
        string='Payslip',
        copy=False,
        readonly=True,
    )

    @api.model
    def _get_timesheet_cost_hook(self, timesheet):
        cost = super(AccountAnalyticLine, self)._get_timesheet_cost_hook(timesheet)
        start_date = datetime.now().strftime('%Y-%m-01')
        end_date = str(datetime.now() + relativedelta(months=+1, day=1, days=-1))[:10]
        contract_ids = self.env['hr.payslip'].get_contract(timesheet.employee_id, start_date, end_date)
        if contract_ids and timesheet.work_type_id:
            contract = self.env['hr.contract'].browse(contract_ids[0])
            worktype_ids = contract.work_type_ids.filtered(lambda wo:wo.work_type_id.id == timesheet.work_type_id.id)
            if worktype_ids:
                worktype_ids = worktype_ids[0]
                cost = worktype_ids.rate
        return cost

    @api.model
    def _get_field_name_hook(self):
        field_name_lst = super(AccountAnalyticLine, self)._get_field_name_hook()
        field_name_lst += ['work_type_id']
        return field_name_lst

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
