# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.


from odoo import models, fields, api

class ProjectImage(models.Model):
    _name="project.gallary"

    name = fields.Char(
        string="Name",
        required=True,
    )
    image = fields.Binary(
        string="Photo",
    )
    project_id = fields.Many2one(
        'project.project',
        string="Project",
    )
    website_size_x = fields.Integer('Size X', default=1)
    website_size_y = fields.Integer('Size Y', default=1)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
