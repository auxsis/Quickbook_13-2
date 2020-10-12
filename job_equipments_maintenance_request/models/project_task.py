# -*- coding: utf-8 -*-


from odoo import models, fields, api

class ProjectTask(models.Model):
    _inherit = 'project.task'
    
    maintenance_equipment_id = fields.Many2one(
        'maintenance.equipment',
        string='Maintenance Equipment',
        readonly=True,
        copy=False,
    )
    custom_maintenance_equipment_ids = fields.One2many(
        'maintenance.equipment',
        'custom_equipment_job_id',
        string='Maintenance Equipments',
        readonly=True,
        copy=False,
    )
    maintenance_equipment_count = fields.Integer(
        compute='_compute_maintenance_equipment_count',
        string='Maintenance Equipment Count',
        copy=False,
    )
    maintenance_request_id = fields.Many2one(
        'maintenance.request',
        string='Maintenance Request',
        readonly=True,
        copy=False,
    )
    custom_maintenance_request_ids = fields.One2many(
        'maintenance.request',
        'custom_request_job_id',
        string='Maintenance Request',
        readonly=True,
        copy=False,
    )
    maintenance_request_count = fields.Integer(
        compute='_compute_maintenance_request_count',
        string='Maintenance Request Count',
        copy=False,
    )

    @api.multi
    @api.depends('custom_maintenance_equipment_ids')
    def _compute_maintenance_equipment_count(self):
        for rec in self:
            rec.maintenance_equipment_count = len(rec.custom_maintenance_equipment_ids)

    @api.multi
    def action_view_maintenance_equipment(self):
        self.ensure_one()
        action = self.env.ref('maintenance.hr_equipment_action').read()[0]
        action['domain'] = [('custom_equipment_job_id', '=', self.id)]
        return action

    @api.multi
    @api.depends('custom_maintenance_request_ids')
    def _compute_maintenance_request_count(self):
        for rec in self:
            rec.maintenance_request_count = len(rec.custom_maintenance_request_ids)

    @api.multi
    def action_view_maintenance_request(self):
        self.ensure_one()
        action = self.env.ref('maintenance.hr_equipment_request_action').read()[0]
        action['domain'] = [('custom_request_job_id', '=', self.id)]
        return action
