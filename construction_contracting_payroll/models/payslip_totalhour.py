# -*- coding: utf-8 -*-

from odoo import fields, models


class PayslipTotalHour(models.Model):
    _name = 'payslip.totalhour'
    
    payslip_id = fields.Many2one(
        'hr.payslip',
        string='Payslip',
    )
    work_type_id = fields.Many2one(
        'timesheet.work.type',
        string='Work Type',
    )
    total_hour = fields.Float(
        string='Total Hour',
    )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
