# -*- coding: utf-8 -*-

from odoo import fields, models, api


class HrTimesheetSheet(models.Model):
    _inherit = "hr_timesheet_sheet.sheet"

    state = fields.Selection(selection_add=[
        ('paid', 'Paid'),
    ])
    custom_payslip_id = fields.Many2one(
        'hr.payslip',
        string='Payslip',
        copy=False,
        readonly=True,
    )

    @api.multi
    def refund_sheet_payroll(self):
        for rec in self:
            for line in rec.timesheet_ids:
                line.with_context(skip_warning = True).write({'is_payroll_paid': False})
                line.sheet_id.write({'state': 'confirm'})

    @api.multi
    def show_payslip(self):
        self.ensure_one()
        res = self.env.ref('hr_payroll.action_view_hr_payslip_form')
        res = res.read()[0]
        res['domain'] = str([('id', '=', self.custom_payslip_id.id)])
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
