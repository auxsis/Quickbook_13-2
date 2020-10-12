# -*- coding: utf-8 -*

from odoo import models, fields, api

class Project(models.Model):
    _inherit = 'project.project'

    rfi_product_id = fields.Many2one(
        'product.product',
        string='Product',
    )
    rfi_price_rate = fields.Float(
        string='Price / Rate (Company Currency)',
        default=lambda self :('0'),
        copy=False,
    )
    
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        for project in self:
            project.rfi_price_rate = project.partner_id.rfi_price_rate
            project.rfi_product_id = project.partner_id.rfi_product_id
            
    @api.multi
    def action_view_rfi_request(self):
        self.ensure_one()
        action = self.env.ref('project_request_for_information.action_request_information')
        action = action.read()[0]
        action['domain'] = str([('project_id','=',self.id)])
        return action

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

