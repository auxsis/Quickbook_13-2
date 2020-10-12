# -*- coding: utf-8 -*-

from odoo import fields, models


class InspectionRecord(models.Model):
    _name = "inspection.record"

    name = fields.Char(
        string="Name",
        required=True,
    )
    code = fields.Char(
        string="Code",
        required=True,
    )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
