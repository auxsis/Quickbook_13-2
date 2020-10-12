# -*- coding: utf-8 -*-


from odoo import models, fields

class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'
    
    custom_equipment_job_id = fields.Many2one(
        'project.task',
        string='Job Order',
        readonly=True,
        copy=False,
    )