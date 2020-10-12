# -*- coding: utf-8 -*

from odoo import models, fields, api

class ProjectPrice(models.Model):
    _inherit = 'project.task'
    
    price_rate = fields.Float(
        string='Price / Rate (Company Currency)',
        default=0.0,
        copy=False,
    )

    product_id_construction = fields.Many2one(
        'product.product',
        string='Product',
    )
    
    @api.onchange('project_id')
    def _onchange_project(self):
        result = super(ProjectPrice, self)._onchange_project()
        self.price_rate = self.project_id.price_rate
        self.product_id_construction = self.project_id.product_id_construction
        return result
    
    @api.multi
    def action_open_construction_task_ticket(self):
        for rec in self:
            action = self.env.ref('construction_contracting_issue_tracking.action_construction_ticket')
            action = action.read()[0]
            action['domain'] = str([('job_order_id','=',rec.id)])
        return action
