# -*- coding: utf-8 -*

from odoo import models, fields, api

class CustomerPrice(models.Model):
    _inherit = 'res.partner'

    product_id_construction = fields.Many2one(
        'product.product',
        string='Product',
    )
    
    @api.multi
    @api.depends('construction_ticket_ids')
    def _ticket_count(self):
        for rec in self:
            rec.issue_ticket_count = len(rec.construction_ticket_ids)

    price_rate = fields.Float(
        string='Price / Rate (Company Currency)',
        default=0.0,
        copy=False,
    )

    issue_ticket_count = fields.Integer(
        compute = '_ticket_count',
        store=True,
     )
#    ticket_ids = fields.One2many(
#        'helpdesk.support',
#        'partner_id',
#        string='Helpdesk Ticket',
#        readonly=True,
#    )
    construction_ticket_ids = fields.One2many(
        'construction.ticket',
        'partner_id',
        string='Construction Issue',
        readonly=True,
    )
     
    @api.multi
    def show_ticket(self):
        for rec in self:
            res = self.env.ref('construction_contracting_issue_tracking.action_construction_ticket')
            res = res.read()[0]
            res['domain'] = str([('partner_id','=',rec.id)])
        return res
