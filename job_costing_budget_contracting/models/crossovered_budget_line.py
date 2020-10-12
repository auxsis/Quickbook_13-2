# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class CrossOveredBudgetLine(models.Model):
    _inherit = 'account.analytic.crossovered.budget.lines'

    @api.multi
    @api.depends('jobcost_line_id', 'jobcost_line_id.purchase_order_line_ids', 'date_from', 'date_to')
    def _compute_actual_quantity(self):
        for rec in self:
            for line in rec.jobcost_line_id.purchase_order_line_ids:
                if rec.date_from and rec.date_to and line.order_id.date_order.date() >= rec.date_from and line.order_id.date_order.date() <= rec.date_to and line.order_id.state in ['purchase', 'done']:
                    rec.actual_purchase_quantity += line.product_qty

    @api.multi
    @api.depends('jobcost_line_id', 'jobcost_line_id.account_invoice_line_ids', 'date_from', 'date_to')
    def _compute_actual_vendor_quantity(self):
        for rec in self:
            for line in rec.jobcost_line_id.account_invoice_line_ids:
                if rec.date_from and rec.date_to and line.invoice_id.date_invoice >= rec.date_from and line.invoice_id.date_invoice <= rec.date_to and line.state in ['open', 'paid']:
                    rec.actual_vendor_quantity += line.quantity

    @api.multi
    @api.depends('jobcost_line_id', 'jobcost_line_id.timesheet_line_ids', 'date_from', 'date_to')
    def _compute_actual_cost_unit(self):
        for rec in self:
            for line in rec.jobcost_line_id.timesheet_line_ids:
                if rec.date_from and rec.date_to and line.date >= rec.date_from and line.date <= rec.date_to:
                    rec.actual_cost_unit += line.unit_amount

    @api.multi
    @api.depends('jobcost_line_id', 'jobcost_line_id.purchase_order_line_ids', 'date_from', 'date_to')
    def _compute_actual_purchase_amount(self):
        for rec in self:
            for line in rec.jobcost_line_id.purchase_order_line_ids:
                if rec.date_from and rec.date_to and line.order_id.date_order.date() >= rec.date_from and line.order_id.date_order.date() <= rec.date_to and line.order_id.state in ['purchase', 'done']:
                    rec.actual_purchase_amount += line.price_subtotal

    @api.multi
    @api.depends('jobcost_line_id', 'jobcost_line_id.account_invoice_line_ids', 'date_from', 'date_to')
    def _compute_vendorbill_amount(self):
        for rec in self:
            for line in rec.jobcost_line_id.account_invoice_line_ids:
                if rec.date_from and rec.date_to and line.invoice_id.date_invoice >= rec.date_from and line.invoice_id.date_invoice <= rec.date_to and line.state in ['open', 'paid']:
                    rec.actual_vendorbill_amount += line.price_subtotal

    @api.multi
    @api.depends('jobcost_line_id', 'jobcost_line_id.timesheet_line_ids', 'date_from', 'date_to')
    def _compute_actual_amount_total(self):
        for rec in self:
            for line in rec.jobcost_line_id.timesheet_line_ids:
                if rec.date_from and rec.date_to and line.date >= rec.date_from and line.date <= rec.date_to:
                    rec.actual_amount_total += line.amount

    @api.multi
    @api.onchange('jobcost_line_id')
    def _set_planned_amount(self):
        for rec in self:
            rec.analytic_account_id = rec.jobcost_line_id.direct_id.analytic_id.id
            rec.planned_amount = rec.jobcost_line_id.total_cost
            rec.custom_currency_id = rec.jobcost_line_id.direct_id.currency_id.id
            rec.material_planned_qyt = rec.jobcost_line_id.product_qty
            rec.labour_hour = rec.jobcost_line_id.hours
            rec.overhead_planned_qyt = rec.jobcost_line_id.product_qty
            rec.uom_id = rec.jobcost_line_id.uom_id.id
#            rec.produc_id = rec.jobcost_line_id.product_id.id
            rec.product_id = rec.jobcost_line_id.product_id.id
            rec.description = rec.jobcost_line_id.description
            rec.reference = rec.jobcost_line_id.reference

    jobcost_line_id = fields.Many2one(
        'job.cost.line',
        string="Job Cost Line"
    )
    jobtype_id = fields.Many2one(
        'job.type',
        string='Job Type',
    )
    actual_purchase_quantity = fields.Float(
        string='Actual Purchase Quantity',
        compute='_compute_actual_quantity',
        store=True,
    )
    actual_vendor_quantity = fields.Float(
        string='Actual Vendor Quantity',
        compute='_compute_actual_vendor_quantity',
        store=True,
    )
    actual_cost_unit = fields.Float(
        string='Actual Cost unit',
        compute='_compute_actual_cost_unit',
        store=True,
    )
    actual_purchase_amount = fields.Float(
        string='Actual Purchase Amount',
        compute='_compute_actual_purchase_amount',
        store=True,
    )
    actual_vendorbill_amount = fields.Float(
        string='Actual Vendor Bill Amount',
        compute='_compute_vendorbill_amount',
        store=True,
    )
    actual_amount_total = fields.Float(
        string='Actual Amount Total',
        compute='_compute_actual_amount_total',
        store=True,
    )
    costsheet_id = fields.Many2one(
        'job.costing',
        string='Cost Sheet',
    )
    custom_currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
    )
    line_type = fields.Selection(
        [('material', 'Material'),
        ('labour', 'Labour'),
        ('overhead', 'Overhead')],
        string='Cost Type',
        default='material',
    )
    material_planned_qyt = fields.Float(
        string='Material Planned Qty',
    )
    overhead_planned_qyt = fields.Float(
        string='Overhead Planned Qty',
    )
    labour_hour = fields.Float(
        string='Labour Hours',
    )
    uom_id = fields.Many2one(
        'uom.uom',
#        'product.uom',
        string='Uom',
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
    )
    description = fields.Char(
        string='Description',
    )
    reference = fields.Char(
        string='Reference',
    )

    @api.multi
    @api.onchange('line_type')
    def _onchange_line_type(self):
        self.costsheet_id = False
        self.jobtype_id = False
        self.jobcost_line_id = False
        self.material_planned_qyt = 0.0
        self.labour_hour = 0.0
        self.overhead_planned_qyt = 0.0
        domain = []
        if self.line_type:
            domain += [('job_type', '=', self.line_type)]
        if self.costsheet_id:
            domain += [('direct_id', '=', self.costsheet_id.id)]
        if self.jobtype_id:
            domain += [('job_type_id', '=', self.jobtype_id.id)]
        return {'domain': {'jobcost_line_id': domain}}

    @api.multi
    @api.onchange('costsheet_id', 'jobtype_id', 'jobcost_line_id')
    def _onchange_set_costline(self):
        domain = []
        if self.line_type:
            domain += [('job_type', '=', self.line_type)]
        if self.costsheet_id:
            domain += [('direct_id', '=', self.costsheet_id.id)]
        if self.jobtype_id:
            domain += [('job_type_id', '=', self.jobtype_id.id)]
        return {'domain': {'jobcost_line_id': domain}}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
