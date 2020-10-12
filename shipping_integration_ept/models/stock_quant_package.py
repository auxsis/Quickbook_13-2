# Copyright (c) 2019 Emipro Technologies Pvt Ltd (www.emiprotechnologies.com). All rights reserved.
from odoo import fields, models

class QuantPackage(models.Model):
    _inherit = "stock.quant.package"
    # This field is added for add aditional tracking reference in package.
    
    tracking_no = fields.Char(string="Tracking Number",help="In packages, Indicates all tracking number as per provider")