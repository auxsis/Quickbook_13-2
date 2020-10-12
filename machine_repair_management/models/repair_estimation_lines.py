# -*- coding: utf-8 -*

from odoo import models, fields, api

class RepairEstimationLines(models.Model):
    _name = 'repair.estimation.lines'
    
    task_id = fields.Many2one(
        'project.task',
        string="Task"
    )
    product_id = fields.Many2one(
        'product.product',
        string="Product"
    )
    qty = fields.Float(
        string = "Quantity",
        default=1.0
    )
    product_uom = fields.Many2one(
        'product.uom',
        string="UOM"
    )
    price = fields.Float(
        string = "Price"
    )
    notes = fields.Text(
       string="Notes",
    )
    
    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        for rec in self:
            rec.product_uom = rec.product_id.uom_id.id
            rec.price = rec.product_id.lst_price