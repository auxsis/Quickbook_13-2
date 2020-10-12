# -*- coding: utf-8 -*

from odoo import models, fields, api

class Project(models.Model):
    _inherit = 'project.project'

    product_id_construction = fields.Many2one(
        'product.product',
        string='Product',
    )
    
    price_rate = fields.Float(
        string='Price / Rate (Company Currency)',
        default=lambda self :('0'),
        copy=False,
    )
    
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        for project in self:
            project.price_rate = project.partner_id.price_rate
            project.product_id_construction = project.partner_id.product_id_construction
    
    @api.multi
    def action_open_project_construction_ticket(self):
        for rec in self:
            action = self.env.ref('construction_contracting_issue_tracking.action_construction_ticket')
            action = action.read()[0]
            action['domain'] = str([('project_id','=',rec.id)])
        return action
    
