# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from odoo.exceptions import UserError


class ConstructionChangeOrder(models.Model):
    _name = 'construction.change.order'
    _description = "Change Order"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'id desc'

    @api.multi
    @api.depends('order_line_ids')
    def _compute_total(self):
        for rec in self:
            for line in rec.order_line_ids:
                rec.total += line.subtotal

    @api.multi
    @api.depends('original_contract_amount', 'amount_total')
    def _compute_newamount(self):
        for rec in self:
            rec.total_contract_amount_all_change = rec.original_contract_amount + rec.amount_total

    @api.depends('order_line_ids.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line_ids:
                amount_untaxed += line.subtotal
                amount_tax += line.price_tax
            order.update({
                'amount_untaxed': order.pricelist_id.currency_id.round(amount_untaxed),
                'amount_tax': order.pricelist_id.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
            })

    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('approved_hr_manager', 'Approved'),
        ('customer_approved', 'Customer Approved'),
        ('reject', 'Rejected'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')],string='State',
        readonly=True, default='draft',
        track_visibility='onchange',
    )
    name = fields.Char(
        string='Number',
    )
    date = fields.Datetime(
        string='Create Date',
        default=fields.Datetime.now(),
        required=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        default=lambda self: self.env.user.partner_id.id,
        required=True,
    )
    company_id = fields.Many2one('res.company',
        default=lambda self: self.env.user.company_id,
        string='Company',
        required=True,
        readonly=True,
    )
    project_id = fields.Many2one(
        'project.project',
        string='Project',
        required=True,
    )
    task_id = fields.Many2one(
        'project.task',
        string='Job Order',
    )
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Contract/Analytic Account',
        required=True,
    )
    reason_note = fields.Text(
        string='Reason for Change',
    )
    order_line_ids = fields.One2many(
        'construction.change.order.line',
        'change_order_id',
        string='Change order line',
    )
    currency_id = fields.Many2one('res.currency', 
        string='Currency', 
        default=lambda self: self.env.user.company_id.currency_id,
        required=True, 
        readonly=True,
    )
    user_id = fields.Many2one('res.users', 
        string='Responsible User', 
        default=lambda self: self.env.user.id,
        required=True, 
        readonly=True,
    )
    total = fields.Float(
        strong='Total',
        compute='_compute_total',
        store=True,
    )
    note = fields.Text(
        string='Note',
    )
    term = fields.Text(
        string='Terms and Conditions',
    )
    approve_by = fields.Many2one(
        'res.users',
        string='Approved By',
        readonly=True, 
        copy=False,
    )
    approve_date = fields.Date(
        string='Approved Date',
        readonly=True, 
        copy=False,
    )
    customer_approve = fields.Many2one(
        'res.users',
        string='Customer Approved',
        readonly=True, 
        copy=False,
    )
    customer_approve_date = fields.Date(
        string='Customer Approved Date',
        readonly=True, 
        copy=False,
    )
    
    confirm_by = fields.Many2one(
        'res.users',
        string='Confirmed By',
        readonly=True, 
        copy=False,
    )
    confirm_date = fields.Date(
        string='Confirmed Date',
        readonly=True,
        copy=False,
    )
    done_by = fields.Many2one(
        'res.users',
        string='Closed By',
        readonly=True, 
        copy=False,
    )
    done_date = fields.Date(
        string='Closed Date',
        readonly=True, 
        copy=False,
    )
    guarantor_1 = fields.Many2one(
        'res.partner',
        string='Guarantor One'
    )
    guarantor_2 = fields.Many2one(
        'res.partner',
        string='Guarantor Two'
    )
    original_contract_amount = fields.Float(
        string='Original Contract Amount'
    )
    total_contract_amount_all_change = fields.Float(
        string='Total Contract Amount All Change',
        compute='_compute_newamount',
        store=True,
    )
    original_job_completion_date = fields.Date(
        string='Original Job Completion Date',
        copy=False,
        default=fields.date.today(),
    )
    new_estimation_completion_date = fields.Date(
        string='New Estimation Completion Date',
        copy=False,
        default=fields.date.today(),
    )
    is_saleorder = fields.Boolean(
        string='Is Sale order',
        default=False
    )
    pricelist_id = fields.Many2one(
        'product.pricelist',
        string='Pricelist',
        required=True,
    )
    amount_untaxed = fields.Monetary(
        string='Untaxed Amount',
        store=True, readonly=True,
         compute='_amount_all',
        track_visibility='onchange',
    )
    amount_tax = fields.Monetary(
        string='Taxes',
        store=True,
        readonly=True,
        compute='_amount_all',
     )
    amount_total = fields.Monetary(
        string='Total',
        store=True,
        readonly=True,
        compute='_amount_all',
        track_visibility='always',
     )

    @api.model
    def create(self, vals):
        name = self.env['ir.sequence'].next_by_code('construction.change.order.seq')
        vals.update({
        'name': name
        })
        return super(ConstructionChangeOrder, self).create(vals)

    @api.onchange('project_id')
    def _onchange_project(self):
        for rec in self:
            rec.analytic_account_id = rec.project_id.analytic_account_id.id
            
    @api.onchange('partner_id')
    def _onchange_partner(self):
        for rec in self:
            rec.pricelist_id = rec.partner_id.property_product_pricelist.id

    @api.multi
    def confirm_state(self):
        for rec in self:
            if not rec.order_line_ids:
                raise UserError(_('You can not confirm change order without line.'))
            rec.confirm_by = self.env.user.id
            rec.confirm_date = fields.Date.today()
            rec.state = 'confirm'

    @api.multi
    def approve_state(self):
        for rec in self:
            rec.approve_by = self.env.user.id
            rec.approve_date = fields.Date.today()
            rec.state = 'approved_hr_manager'

    @api.multi
    def customer_approve_state(self):
        for rec in self:
            rec.customer_approve = self.env.user.id
            rec.customer_approve_date = fields.Date.today()
            rec.state = 'customer_approved'

    @api.multi
    def done_state(self):
        for rec in self:
            rec.done_by = self.env.user.id
            rec.done_date = fields.Date.today()
            rec.state = 'done'

    @api.multi
    def cancel_state(self):
        for rec in self:
            rec.state = 'cancel'

    @api.multi
    def draft_state(self):
        for rec in self:
            rec.state = 'draft'

    @api.multi
    def reject_state(self):
        for rec in self:
            rec.state = 'reject'

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state not in ['draft', 'cancel']:
                raise UserError(_('You can not delete change order.'))
        return super(ConstructionChangeOrder, self).unlink()

    @api.multi
    def show_contract(self):
        self.ensure_one()
        res = self.env.ref('analytic.action_account_analytic_account_form')
        res = res.read()[0]
        res['domain'] = str([('id', '=', self.analytic_account_id.id)])
        return res

    @api.multi
    def show_saleorder(self):
        self.ensure_one()
        res = self.env.ref('sale.action_orders')
        res = res.read()[0]
        res['domain'] = str([('analytic_account_id', '=', self.analytic_account_id.id)])
        return res

    @api.multi
    def _prepare_quotation_line(self, quotation):
        quo_line_obj = self.env['sale.order.line']
        for rec in self:
            for line in rec.order_line_ids:
                vals = {
                            'product_id':  line.product_id.id,
                            'product_uom_qty': line.quantity,
                            'product_uom': line.uom_id.id,
                            'price_unit' : line.sale_price,
                            'price_subtotal': line.subtotal,
                            'name' : line.description,
                            'price_total' : self.total,
                            'tax_id': [(6, 0, line.tax_ids.ids)],
                            'order_id':quotation.id,
                        }
                quo_line = quo_line_obj.create(vals)

    @api.multi
    def create_saleorder(self):
        quo_obj = self.env['sale.order']
        for rec in self:
            vals = {
                'partner_id':rec.partner_id.id,
                'origin': rec.name,
                'analytic_account_id':rec.analytic_account_id.id,
                'pricelist_id': rec.pricelist_id.id,
                'payment_term_id': rec.partner_id.property_payment_term_id.id,
                }
            quotation = quo_obj.create(vals)
            rec._prepare_quotation_line(quotation)
            rec.is_saleorder = True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
