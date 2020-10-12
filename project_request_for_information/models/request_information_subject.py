# -*- coding: utf-8 -*-

from odoo import models, fields

class RequestInformationSubject(models.Model):
    _name = 'request.information.subject'

    name = fields.Char(
        'Name',
        required=True,
    )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
