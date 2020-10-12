# -*- coding:utf-8 -*-

from odoo import http
from odoo.http import request
from openerp import api, fields, models, _


class ContractingDrawing(models.Model):
    _name = "contracting.drawing"

    name = fields.Char(
        string="Drawing Name",
        required=True
    )
    description = fields.Char(
        string="Description",
        required=True
    )
    image = fields.Binary(
        string = 'Drawing Image',
    )
    job_card_drawing_id = fields.Many2one(
        'project.task',
        string="Job Card"
    )

    @api.multi
    def open_drawing_document(self):
        for rec in self:
            return {
                'type': 'ir.actions.act_url',
                'url': '/open/contract_drawing_document/%s' %(rec.id),
                'target': 'self',
                'res_id': rec.id,
            }

class ContractingDrawingDocument(http.Controller):

    @http.route(['/open/contract_drawing_document/<int:res_id>'], type='http', auth="public", website=True)
    def open_drawing_document(self, res_id, **post):
        if res_id:
            document_id = request.env['contracting.drawing'].sudo().browse(res_id)
            values = {
                'document': document_id,
            }
            return request.render('job_drawing_image_contracting.contracting_drawing_document', values)

