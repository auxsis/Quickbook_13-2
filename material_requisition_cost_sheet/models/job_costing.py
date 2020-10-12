# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class JobCostLine(models.Model):
    _inherit = 'job.costing'

    @api.multi
    @api.depends('custom_mpr_ids')
    def _requisition_count(self):
        for rec in self:
            rec.requisition_count = len(rec.custom_mpr_ids)

    requisition_count = fields.Integer(
        string='count',
        compute ='_requisition_count',
        store=True,
     )
     
    custom_mpr_ids = fields.One2many(
        'material.purchase.requisition.line',
        'custom_job_costing_id',
        string="Material Purchase Requisition",
    )

    @api.multi
    def show_requisition(self):
        self.ensure_one()
        res = self.env.ref('material_requisition_cost_sheet.action_material_purchase_requisition_lines')
        res = res.read()[0]
        res['domain'] = str([('id','in', self.custom_mpr_ids.ids)])
        return res

    # vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
