# -*- coding: utf-8 -*-


from odoo import models, fields, api

class MaintenanceEquipmentWizard(models.TransientModel):
    _name = 'maintenance.equipment.wizard'

    equipment_name = fields.Char(
        string='Name',
        required=True,
    )
    equipment_category_id = fields.Many2one(
        'maintenance.equipment.category',
        string='Equipment Category',
        required=True,
    )
    equipment_model = fields.Char(
        string='Model',
    )
    equipment_serial_no = fields.Char(
        string='Serial Number',
    )
    note = fields.Text(
        string='Notes',
    )
    

    @api.multi
    def create_maintenance_equipment(self):
        active_id = self._context.get('active_id')
        job_cost_sheets = self.env['project.task'].browse(active_id)
        maintenance_equp_obj = self.env['maintenance.equipment']
        vals = {
            'name': self.equipment_name,
            'category_id': self.equipment_category_id.id,
            'model': self.equipment_model,
            'serial_no': self.equipment_serial_no,
            'note': self.note,
            'custom_equipment_job_id': job_cost_sheets.id,
        }
        maintenance_equipment= maintenance_equp_obj.sudo().create(vals)
        job_cost_sheets.maintenance_equipment_id = maintenance_equipment.id

        action = self.env.ref('maintenance.hr_equipment_action')
        result = action.read()[0]
        result['domain'] = [('id', '=', maintenance_equipment.id)]
        return result