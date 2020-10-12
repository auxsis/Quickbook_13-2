# -*- coding: utf-8 -*-

from odoo import fields, models


class JobOrderInspectionLine(models.Model):
    _name = "job.order.inspection.line"

    job_inspection_id = fields.Many2one(
        'job.order.inspection',
        string="Job Inspection"
    )
    inspection_record = fields.Many2one(
        'inspection.record',
        string="Inspection",
        required=True,
    )
    inspection_result = fields.Many2one(
        'inspection.result',
        string="Inspection Result",
        required=True,
    )
    description = fields.Char(
        string="Description",
        required=True,
    )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
