# -*- coding: utf-8 -*-

from odoo import fields, models


class ContractWorkType(models.Model):
    _name = 'contract.worktype'

    contract_id = fields.Many2one(
        'hr.contract',
        string='Contract',
    )
    work_type_id = fields.Many2one(
        'timesheet.work.type',
        string='Work Type',
    )
    rate = fields.Float(
        string='Rate',
    )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
