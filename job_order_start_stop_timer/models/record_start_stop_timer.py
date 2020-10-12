# -*- coding: utf-8 -*-

from odoo import fields, models


class RecordStartStopTimer(models.Model):
    _inherit = "record.start.stop.timer"

    joborder_id = fields.Many2one(
        'project.task',
        string='Job Order',
        copy=False,
    )
