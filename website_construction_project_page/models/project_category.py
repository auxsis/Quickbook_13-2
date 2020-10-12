# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.


from odoo import models, fields, api

class ProjectCategory(models.Model):
    _name="project.category"

    image = fields.Binary(
        string='Image',
    )

    name = fields.Char(
        string="Name",
        required=True,
        copy=False,
    )
    
    website_size_x = fields.Integer('Size X', default=1)
    website_size_y = fields.Integer('Size Y', default=1)
#    website_style_ids = fields.Many2many('product.style', string='Styles')
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
