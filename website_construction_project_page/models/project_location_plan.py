# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.


from odoo import models, fields, api

class ProjectLocationPlan(models.Model):
    _name="project.location.plan"

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
    

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
