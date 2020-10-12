# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def get_analytic_line(self, date_from, date_to, work_type):
        analytic_line_ids = self.env['account.analytic.line'].search([
            ('employee_id', '=', self.id),
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('work_type_id', '=', work_type.id),
            ('is_payroll_paid', '=', False),
            ('sheet_id', '!=', False),
            ('sheet_id.state', '=', 'done'),
            ])
        return analytic_line_ids

    @api.model
    def _get_work_type_salary(self, code, payslip):
        payslip_obj = self.env['hr.payslip'].browse(payslip)
        work_type = self.env['timesheet.work.type'].search([('code', '=', code)])
        analytic = []
        analytic_line_ids = self.get_analytic_line(payslip_obj.date_from, payslip_obj.date_to, work_type)
        for line in analytic_line_ids:
            if not line.custom_payslip_id:
                analytic.append((4, line.id))
        payslip_obj.write({'timesheet_ids': analytic})
        rate = 0.0
        for vline in payslip_obj.contract_id.work_type_ids:
            if vline.work_type_id == work_type:
                rate = vline.rate
        regular = 0.0
        for line in analytic_line_ids:
#            regular += line.amount
            regular += line.unit_amount
        total_amount = rate * regular
        return rate * regular

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
