# -*- coding: utf-8 -*-

from openerp import models, fields, api, _

from odoo.addons import decimal_precision as dp


class ConstructionChngeOrderLine(models.Model):
    _name = 'construction.change.order.line'
    _description = "Change Order Line"
    _order = 'id desc'
    _rec_name = 'product_id'

    @api.depends('quantity', 'sale_price', 'tax_ids')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.sale_price * (1 - (0.0) / 100.0)
            taxes = line.tax_ids.compute_all(price, line.currency_id, line.quantity, product=line.product_id, partner=line.change_order_id.partner_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                #'price_subtotal': taxes['total_excluded'],
                'subtotal': taxes['total_excluded'],
            })

    @api.multi
    @api.depends('quantity', 'sale_price')
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = rec.quantity * rec.sale_price

    price_tax = fields.Float(
        compute='_compute_amount',
        string='Taxes',
        readonly=True,
        store=True,
     )
    price_total = fields.Monetary(
        compute='_compute_amount',
        string='Total',
        readonly=True,
        store=True,
    )
    product_id = fields.Many2one(
        'product.product', 
        string='Product',
    )
    quantity = fields.Float(
        string='Quantity',
        digits=dp.get_precision('Product Unit of Measure'),
        default=1.0
    )
    uom_id = fields.Many2one(
        'uom.uom',#product.uom
        string='Uom',
    )
    description = fields.Text(
        string='Description',
        required='True',
    )
    sale_price = fields.Float(
        string='Sale Price',
        digits=dp.get_precision('Product Price'),
        default=0.0
    )
    change_order_id = fields.Many2one(
        'construction.change.order',
        string='Construction Change',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='change_order_id.currency_id',
    )
    subtotal = fields.Float(
        string='Subtotal',
        compute='_compute_amount',
        store=True,
    )
    tax_ids = fields.Many2many(
        'account.tax',
        string='Taxes',
    )

    @api.multi
    def _get_display_price(self, product):
        # TO DO: move me in master/saas-16 on sale.order
        if self.change_order_id.pricelist_id.discount_policy == 'with_discount':
            return product.with_context(pricelist=self.change_order_id.pricelist_id.id).price
        price, rule_id = self.change_order_id.pricelist_id.get_product_price_rule(self.product_id, self.quantity or 1.0, self.change_order_id.partner_id)
        pricelist_item = self.env['product.pricelist.item'].browse(rule_id)
        if (pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id.discount_policy == 'with_discount'):
            price, rule_id = pricelist_item.base_pricelist_id.get_product_price_rule(self.product_id, self.quantity or 1.0, self.change_order_id.partner_id)
            return price
        else:
            from_currency = self.change_order_id.company_id.currency_id
            return from_currency.compute(product.lst_price, self.change_order_id.pricelist_id.currency_id)

    @api.multi
    @api.onchange('product_id')
    def _onchange_product(self):
        vals = {}
        desc = ' '
        for rec in self:
            if rec.product_id:
                rec.uom_id = rec.product_id.uom_id.id
                if rec.product_id.description_sale:
                    rec.description = rec.product_id.name + '\n' + rec.product_id.description_sale
                else:
                    rec.description = rec.product_id.name
                #rec.sale_price = rec.product_id.lst_price
                rec.tax_ids = rec.product_id.taxes_id.ids
                vals['quantity'] = 1.0
                product = self.product_id.with_context(
                    lang=self.change_order_id.partner_id.lang,
                    partner=self.change_order_id.partner_id.id,
                    quantity=vals.get('quantity') or self.quantity,
                    date=self.change_order_id.date,
                    pricelist=self.change_order_id.pricelist_id.id,
                    uom=self.uom_id.id,
                )

                if self.change_order_id.pricelist_id and self.change_order_id.partner_id:
                    a = self._get_display_price(rec.product_id)
                    vals['sale_price'] = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_ids, self.change_order_id.company_id)
                    rec.update(vals)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
