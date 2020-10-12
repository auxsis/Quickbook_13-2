# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api

class JobCosting(models.Model):
    _inherit = "job.costing"
    
    @api.multi
    def action_view_rfi_request(self):
        self.ensure_one()
        action = self.env.ref('project_request_for_information.action_request_information')
        action = action.read()[0]
        action['domain'] = str([('job_cost_id','=',self.id)])
        return action

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
