# -*- coding: utf-8 -*

from odoo import models, fields, api

class ProjectPrice(models.Model):
    _inherit = 'project.task'

    rfi_price_rate = fields.Float(
        string='Price / Rate (Company Currency)',
        default=0.0,
        copy=False,
    )
    rfi_product_id = fields.Many2one(
        'product.product',
        string='Product',
    )
    rfi_request_id = fields.Many2one(
        'request.information',
        string='Request for Information',
        readonly=True,
        copy=False,
    )

    @api.onchange('project_id')
    def _onchange_project(self):
        result = super(ProjectPrice, self)._onchange_project()
        self.rfi_price_rate = self.project_id.rfi_price_rate
        self.rfi_product_id = self.project_id.rfi_product_id
        return result

    @api.multi
    def action_view_rfi_request(self):
        self.ensure_one()
        action = self.env.ref('project_request_for_information.action_request_information')
        action = action.read()[0]
        action['domain'] = str([('task_id','=',self.id)])
        return action
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
