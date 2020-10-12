# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    calendar_id = fields.Many2one(
        'calendar.event',
        string='Calendar',
    )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
