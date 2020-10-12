# -*- coding: utf-8 -*-

from odoo import models, api


class PurchaseRequisition(models.Model):
    _inherit = 'material.purchase.requisition'

    @api.model
    def _prepare_po_line(self, line=False, purchase_order=False):
        vals = super(PurchaseRequisition, self)._prepare_po_line(line=line, purchase_order=purchase_order)
        vals.update({
            'job_cost_id': line.custom_job_costing_id.id,
            'job_cost_line_id': line.custom_job_costing_line_id.id
        })
        return vals


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
