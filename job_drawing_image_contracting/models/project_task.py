# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    contracting_drawing_ids = fields.One2many(
        'contracting.drawing',
        'job_card_drawing_id',
        string="Contracting Drawing"
    )

