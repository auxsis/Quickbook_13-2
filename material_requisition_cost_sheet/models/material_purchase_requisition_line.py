# -*- coding: utf-8 -*-

from odoo import models, fields


class PurchaseRequisitionLine(models.Model):
    _inherit = 'material.purchase.requisition.line'

    custom_job_costing_id = fields.Many2one(
        'job.costing',
        string='Job Cost Center',
    )
    custom_job_costing_line_id = fields.Many2one(
        'job.cost.line',
        string='Job Cost Line',
    )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
