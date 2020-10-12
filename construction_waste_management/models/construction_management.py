# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ConstructionWasteManagement(models.Model):
    _name = 'construction.waste.management'
    _description = 'Material Wastes'
    _order = 'id desc'
    
    @api.model
    def create(self,vals):
        number = self.env['ir.sequence'].next_by_code('construction.waste.management')
        vals.update({
            'name': number,
        })
        return super(ConstructionWasteManagement, self).create(vals) 
    
    name = fields.Char(
        string="Name",
        readonly=True,
        copy=False,
    )
    type = fields.Selection(
        [('reused', 'Reuse Material'),
         ('scrap', 'Scrap Material')],
        string='Waste Method',
        required=True,
        copy=False,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        copy=False,
    )
    qty = fields.Integer(
        string='Quantity'
    )
    uom_id = fields.Many2one(
        'uom.uom',#product.uom
        string='UOM',
        copy=False,
    )    
    project_id = fields.Many2one(
        'project.project',
        related='task_id.project_id',
        string='Project',
        store=True,
        copy=False,
    )
    task_id = fields.Many2one(
        'project.task',
        string='Job Order',
        copy=False,
        required=True,
    )
    stock_scrap_id = fields.Many2one(
        'stock.scrap',
        string='Stock Scrap',
        copy=False,
        readonly=True,
    )
    is_waste_created = fields.Boolean(
        string="Is Waste Created ?",
        copy=False,
    )
    location_id = fields.Many2one(
        'stock.location',
        string='Source Location',
        copy=True,
    )
    dest_location_id = fields.Many2one(
        'stock.location',
        string='Destination Location',
        required=False,
        copy=True,
    )
    internal_picking_id = fields.Many2one(
        'stock.picking',
        string='Picking',
        copy=False,
        readonly=True,
    )
    picking_type_id = fields.Many2one(
        'stock.picking.type',
        string='Picking Type',
        copy=False,
    )
    user_id = fields.Many2one(
        'res.users',
        default=lambda self: self.env.user.id,
        string='User',
    )
    company_id = fields.Many2one(
        'res.company', 
        default=lambda self: self.env.user.company_id, 
        string='Company',
        readonly=True,
     )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for rec in self:
            rec.uom_id = rec.product_id.uom_id
            rec.qty = 1

    @api.multi
    def create_stock_scrap(self):
        stock_obj = self.env['stock.picking']
        move_obj = self.env['stock.move']
        for rec in self:
            if rec.type == 'scrap':
                vals = {
                       'product_id': rec.product_id.id, 
                       'product_uom_id': rec.uom_id.id,
                       'scrap_qty': rec.qty,
                       'custom_task_id': rec.task_id.id
                       }
                stock_scrap = self.env['stock.scrap'].sudo().create(vals)
                stock_scrap.waste_management_id = rec.id
                rec.stock_scrap_id = stock_scrap.id
                rec.is_waste_created = True
                
            if rec.type == 'reused':
                picking_vals = {
                       'partner_id':rec.task_id.partner_id.id,
                       'location_id' : rec.location_id.id,
                       'location_dest_id' : rec.dest_location_id.id,
                       'picking_type_id': rec.picking_type_id.id,
                       }
                internal_picking = stock_obj.sudo().create(picking_vals)
                internal_picking.waste_management_id = rec.id
                internal_picking.custom_task_id = rec.task_id.id
                rec.is_waste_created = True
#                 
                pick_move_vals = {
                       'product_id': rec.product_id.id, 
                       'product_uom': rec.uom_id.id,
                       'product_uom_qty': rec.qty,
                       'name': internal_picking.name,
                       'location_id' : internal_picking.location_id.id,
                       'location_dest_id' : internal_picking.location_dest_id.id,
                       'picking_id': internal_picking.id,
                    }
                move_obj.sudo().create(pick_move_vals)
                rec.internal_picking_id = internal_picking.id
