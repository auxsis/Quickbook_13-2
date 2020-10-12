# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProjectTask(models.Model):
    _inherit = 'project.task'

    purchaseorder_line_ids = fields.One2many(
        'order.line',
        'sub_contractor_id',
        string='Material Plan',
    )
    subcontractor_id = fields.Many2one(
        'project.task',
        string='Subcontractor Joborder',
    )
    custom_partner_id = fields.Many2one(
        'res.partner',
        string='Subcontractor',
        readonly=True,
    )
    is_subcontractor_joborder = fields.Boolean(
        string='Subcontractor Job order',
        copy=False,
        default=False,
        readonly=True,
    )

    @api.multi
    def show_purchase_order(self):
        self.ensure_one()
        res = self.env.ref('purchase.purchase_rfq')
        res = res.read()[0]
        res['domain'] = str([('subcontractor_id', '=', self.id)])
        return res

    @api.multi
    def show_subcontractor_jobs(self):
        self.ensure_one()
        res = self.env.ref('job_order_subcontracting.action_subcontractor_job')
        res = res.read()[0]
        res['domain'] = str([('parent_task_id', '=', self.id)])
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
