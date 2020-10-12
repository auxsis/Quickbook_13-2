# Copyright (c) 2018 Emipro Technologies Pvt Ltd (www.emiprotechnologies.com). All rights reserved.
from odoo import models, fields, api, _

class UPSStockPickingBatchEpt(models.Model):
    _inherit = "stock.picking.batch"
    delivery_type_ept = fields.Selection(selection_add=[('ups_ept', 'UPS')])

class UPSStockPickingToBatchEpt(models.TransientModel):
    _inherit = 'stock.picking.to.batch.ept'
    delivery_type_ept = fields.Selection(selection_add=[('ups_ept', 'UPS')])