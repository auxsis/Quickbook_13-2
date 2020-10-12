# -*- coding: utf-8 -*-

from odoo import models, fields

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    waste_management_id = fields.Many2one(
        'construction.waste.management',
        string='Waste Material',
        copy=False,
        readonly=True,
    )
    custom_task_id = fields.Many2one(
        'project.task',
        string='Job Order',
        copy=False,
        readonly=True,
    )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
