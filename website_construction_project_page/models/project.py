# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.


from odoo import models, fields, api

class Project(models.Model):
    _inherit="project.project"

    description = fields.Html(
        string='Description',
    )
    image1 = fields.Binary(
        string="Image 1",
    )

    project_category_id = fields.Many2one(
        'project.category',
        string="Category",
    )
    project_floor_plan_ids = fields.One2many(
        'project.floor.plan',
        'project_id',
        string="Project Floor Plans"
    )
    project_location_plan_ids = fields.One2many(
        'project.location.plan',
        'project_id',
        string="Project Location Plan"
    )
    project_image_ids = fields.One2many(
        'project.image',
        'project_id',
        string="Project Images"
    )
    project_gallary_ids = fields.One2many(
        'project.gallary',
        'project_id',
        string="Project Images"
    )
    project_brochure_ids = fields.Many2many(
        'ir.attachment',
        string="Attachement",
    )
    html_content_one = fields.Html(
        string="Description",
    )
    html_content_two = fields.Html(
        string="Description",
    )
    html_content_three = fields.Html(
        string="Description",
    )
    html_content_four = fields.Html(
        string="Description",
    )
    html_content_five = fields.Html(
        string="Description",
    )
    

    @api.multi
    def google_map_img(self, zoom=8, width=298, height=298):
        partner = self.sudo().partner_id
        return partner and partner.google_map_img(zoom, width, height) or None

    @api.multi
    def google_map_link(self, zoom=8):
        partner = self.sudo().partner_id
        return partner and partner.google_map_link(zoom) or None
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
