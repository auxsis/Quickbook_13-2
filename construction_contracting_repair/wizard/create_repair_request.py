# -*- coding: utf-8 -*-

from odoo import models, fields, api

class RepiarRequestWizard(models.TransientModel):
    _name = 'repair.request.wizard'
    
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
    )
    repair_product_ids = fields.One2many(
        'repair.product.wizard',
        'repair_id',
        string='Repairable Products',
        required=True,
    )
    
    @api.multi
    def create_repair_request(self):
        task_id = self._context.get('active_id')
        task = self.env['project.task'].browse(task_id)
        machine_repair = self.env['machine.repair.support']
        repair_ids = []
        for rec in self:
            for repair in rec.repair_product_ids:
                vals = {
                        'subject': repair.name,
                        'partner_id': rec.partner_id.id,
                        'phone': rec.partner_id.phone,
                        'product_id': repair.product_id.id,
                        'user_id': repair.responsible_user_id.id,
                        'team_id': repair.repair_team_id.id,
                        'nature_of_service_id': repair.nature_service_id.id,
                        'repair_types_ids': [(6, 0, repair.repair_type_ids.ids)],
                        'lot_id': repair.lot_id.id,
                        'problem': repair.problem,
                        'email': task.email_from,
                        'project_id': task.project_id.id,
                        'task_id': task.id,
                        }
                machine_repair_requests = machine_repair.create(vals)
                repair_ids.append(machine_repair_requests.id)
        
        action_id = self.env.ref('machine_repair_management.action_machine_repair_support')
        if action_id:
            action = action_id.read([])[0]
            action['domain'] =\
               "[('id','in', ["+','.join(map(str, repair_ids))+"])]"
            return action
        
                
class RepairProductWizard(models.TransientModel):
    _name = "repair.product.wizard"
    
    repair_id = fields.Many2one(
        'repair.request.wizard',
        string='Repair Product',
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
    )
    name = fields.Char(
        string='Repair Description',
    )
    repair_team_id = fields.Many2one(
        'machine.support.team',
        string='Repair Team',
    )
    responsible_user_id = fields.Many2one(
        'res.users',
        string='Repair Responsible',
    )
    nature_service_id = fields.Many2one(
        'service.nature',
        string='Nature of Service',
    )
    repair_type_ids = fields.Many2many(
        'repair.type',
        string='Repair Type',
    )
    lot_id = fields.Many2one(
        'stock.production.lot',
        string='Lot',
    )
    problem = fields.Text(
        string='Problem',
    )