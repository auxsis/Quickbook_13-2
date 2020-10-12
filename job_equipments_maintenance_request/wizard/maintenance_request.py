# -*- coding: utf-8 -*-


from odoo import models, fields, api

AVAILABLE_PRIORITIES = [
    ('0', 'Very Low'),
    ('1', 'Low'),
    ('2', 'Normal'),
    ('3', 'High')]

class MaintenanceRequestWizard(models.TransientModel):
    _name = 'maintenance.request.wizard'

    maintenance_name = fields.Char(
        string='Name',
        required=True,
    )
    maintenance_equipment_id = fields.Many2one(
        'maintenance.equipment',
        string='Maintenance Equipment',
        required=True,
    )
    mainteance_team_id = fields.Many2one(
        'maintenance.team',
        string='Maintenance Team',
        required=True,
    )
    maintenance_date = fields.Datetime(
        'Schedule Date',
    )
    maintenance_duration = fields.Float(
        'Duration (Hours)',
    )
    mainteance_type = fields.Selection(
        [('corrective','Corrective'),
         ('prevantive','Prevantive')],
        string='Type',
    )
    rating = fields.Selection(
        AVAILABLE_PRIORITIES, 
        select=True,
        string='Priority',
    )
    note = fields.Text(
        string='Notes',
    )
    

    @api.multi
    def create_maintenance_request(self):
        active_id = self._context.get('active_id')
        job_cost_sheets = self.env['project.task'].browse(active_id)
        maintenance_request_obj = self.env['maintenance.request']
        vals = {
            'name': self.maintenance_name,
            'technician_user_id': self.env.user.id,
            'mainteance_team_id': self.mainteance_team_id.id,
            'equipment_id': self.maintenance_equipment_id.id,
            'schedule_date': self.maintenance_date,
            'duration': self.maintenance_duration,
            'priority': self.rating,
            'note': self.note,
            'custom_request_job_id': job_cost_sheets.id,
        }
        maintenance_request= maintenance_request_obj.sudo().create(vals)
        job_cost_sheets.maintenance_request_id = maintenance_request.id
        action = self.env.ref('maintenance.hr_equipment_request_action')
        result = action.read()[0]
        result['domain'] = [('id', '=', maintenance_request.id)]
        return result