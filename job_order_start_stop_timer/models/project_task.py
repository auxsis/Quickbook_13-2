# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ProjectTask(models.Model):
    _inherit = "project.task"
    
    @api.depends(
        'start_stop_ids',
        'start_stop_ids.total_duration',
    )
    def _compute_total_duration(self):
        for task in self:
            task.total_duration = sum(t.total_duration for t in task.start_stop_ids)
    
    @api.depends(
        'start_stop_ids',
        'start_stop_ids.start_time',
        'start_stop_ids.stop_timer'
    )
    def _compute_latest_time(self):
        for task in self:
            latest_line = task.start_stop_ids.sorted(reverse=True)
            if latest_line:
                task.latest_start_time = latest_line[0].start_time
                task.latest_stop_time = latest_line[0].stop_timer

    start_stop_ids = fields.One2many(
        'record.start.stop.timer',
        'joborder_id',
        string='Start Stop',
        readonly=False
    )
    last_pause_time = fields.Datetime(
        string="Last Pause Time",
        copy=False,
        readonly=True,
    )
    latest_start_time = fields.Datetime(
        'Latest Start Datetime',
        compute="_compute_latest_time"
    )
    latest_stop_time = fields.Datetime(
        'Latest Stop Datetime',
        compute="_compute_latest_time"
    )
    total_duration = fields.Float(
        string="Total Duration",
        compute="_compute_total_duration",
    )
    
    signature = fields.Binary(
        'Signature',
    )
