# -*- coding: utf-8 -*-

from odoo import models, fields, api

class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    waste_management_id = fields.Many2one(
        'construction.waste.management',
        string='Waste Material',
        readonly=True,
        copy=False,
    )
    custom_task_id = fields.Many2one(
        'project.task',
        string='Job Order',
        copy=False,
        readonly=True,
    )
