# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.multi
    @api.depends('timesheet_ids')
    def _timesheet_line_count(self):
        for rec in self:
            rec.timesheet_line_count = len(rec.timesheet_ids)
            
    @api.multi
    @api.depends('timesheet_ids')
    def _compute_work_type(self):
        type_list = []
        total_hour = 0.0
        for rec in self:
            work_type = self.env['timesheet.work.type'].search([])
            for vtype in work_type:
                total_hour = sum([p.unit_amount for p in rec.timesheet_ids if p.work_type_id == vtype])
                if total_hour != 0.0:
                    vals = {
                        'work_type_id': vtype.id,
                        'total_hour': total_hour,
                        'payslip_id': rec.id,
                    }
                    type_list.append((0, 0, vals))
            rec.work_type_ids = type_list

    timesheet_ids = fields.Many2many(
        'account.analytic.line',
        string='Timesheet Line',
        readonly=True,
    )
    work_type_ids = fields.One2many(
        'payslip.totalhour',
        'payslip_id',
        string='Work Type Payslip',
        compute='_compute_work_type',
        store=True,
    )
    timesheet_line_count = fields.Integer(
        compute = '_timesheet_line_count',
        store=True,
     )

    @api.multi
    def action_payslip_done(self):
        ctx = self._context.copy()
        res = super(HrPayslip, self).action_payslip_done()
        for rec in self:
            for line in rec.timesheet_ids:
                line.with_context(skip_warning = True).write({'is_payroll_paid': True, 'custom_payslip_id': rec.id})
                line.sheet_id.write({'state': 'paid', 'custom_payslip_id': rec.id})
        return res

    @api.multi
    def show_paid_timesheetline(self):
        self.ensure_one()
        res = self.env.ref('construction_contracting_payroll.action_analytic_line_custom')
        res = res.read()[0]
        res['domain'] = str([('custom_payslip_id', '=', self.id)])
        return res

    @api.multi
    def show_timesheet(self):
        self.ensure_one()
        res = self.env.ref('odoo_timesheet_sheet.act_hr_all_timesheetsheet_form')
        res = res.read()[0]
        res['domain'] = str([('custom_payslip_id', '=', self.id)])
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
