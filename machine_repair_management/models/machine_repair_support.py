# -*- coding: utf-8 -*-

import time

from odoo import models, fields, api, _
from odoo.exceptions import UserError, Warning

class MachineRepairSupport(models.Model):
    _name = 'machine.repair.support'
    _description = 'Machine Repair Support'
    _order = 'id desc'
#     _inherit = ['mail.thread', 'ir.needaction_mixin']
    _inherit = ['mail.thread', 'mail.activity.mixin', 'format.address.mixin']

    
    @api.model
    def create(self, vals):
        if vals.get('name', False):
            if not vals.get('name', 'New') == 'New':
                vals['subject'] = vals['name']
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('machine.repair.support') or 'New'

        if vals.get('partner_id', False):
            if 'phone' and 'email' not in vals:
                partner = self.env['res.partner'].sudo().browse(vals['partner_id'])
                if partner:
                    vals.update({
                        'email': partner.email,
                        'phone': partner.phone,
                    })
        return super(MachineRepairSupport, self).create(vals)
    
    @api.multi
    @api.depends('timesheet_line_ids.unit_amount')
    def _compute_total_spend_hours(self):
        for rec in self:
            spend_hours = 0.0
            for line in rec.timesheet_line_ids:
                spend_hours += line.unit_amount
            rec.total_spend_hours = spend_hours
    
    @api.onchange('project_id')
    def onchnage_project(self):
        for rec in self:
            rec.analytic_account_id = rec.project_id.analytic_account_id
          
    @api.one
    def set_to_close(self):
        if self.is_close != True:
            self.is_close = True
            self.close_date = fields.Datetime.now()#time.strftime('%Y-%m-%d')
            self.state = 'closed'
            template = self.env.ref('machine_repair_management.email_template_machine_ticket')
            template.send_mail(self.id)
            
    @api.one
    def set_to_reopen(self):
        self.state = 'work_in_progress'
        if self.is_close != False:
            self.is_close = False

    @api.multi
    def create_machine_diagnosys(self):
        for rec in self:
            name = ''
            if rec.subject:
                name = rec.subject +'('+rec.name+')'
            else:
                name = rec.name
            task_vals = {
                'name' : str(name),
                'user_id' : rec.user_id.id,
                'date_deadline' : rec.close_date,
                'project_id' : rec.project_id.id,
                'partner_id' : rec.partner_id.id,
                'description' : rec.description,
                'ticket_id' : rec.id,
                'task_type': 'diagnosys',
            }
            task_id= self.env['project.task'].sudo().create(task_vals)
        action = self.env.ref('machine_repair_management.action_view_task_diagnosis')
        result = action.read()[0]
        result['domain'] = [('id', '=', task_id.id)]
        return result

    @api.one
    def create_work_order(self):
        for rec in self:
            task_vals = {
            'name' : rec.subject +'('+rec.name+')',
            'user_id' : rec.user_id.id,
            'date_deadline' : rec.close_date,
            'project_id' : rec.project_id.id,
            'partner_id' : rec.partner_id.id,
            'description' : rec.description,
            'ticket_id' : rec.id,
            'task_type': 'work_order',
            }
            task_id= self.env['project.task'].sudo().create(task_vals)
        action = self.env.ref('machine_repair_management.action_view_task_diagnosis')
        result = action.read()[0]
        result['domain'] = [('id', '=', task_id.id)]
        return result

    @api.onchange('product_id')
    def onchnage_product(self):
        for rec in self:
            rec.brand = rec.product_id.brand
            rec.color = rec.product_id.color
            rec.model = rec.product_id.model
            rec.year = rec.product_id.year
    
    name = fields.Char(
        string='Number', 
        required=False,
        default='New',
        copy=False, 
        readonly=True, 
    )
    state = fields.Selection(
        [('new','New'),
         ('assigned','Assigned'),
         ('work_in_progress','Work in Progress'),
         ('needs_more_info','Needs More Info'),
         ('needs_reply','Needs Reply'),
         ('reopened','Reopened'),
         ('solution_suggested','Solution Suggested'),
         ('closed','Closed')],
        track_visibility='onchange',
        default='new',
        copy=False, 
    )
    email = fields.Char(
        string="Email",
        required=False
    )
    phone = fields.Char(
        string="Phone"
    )
    category = fields.Selection(
        [('technical', 'Technical'),
        ('functional', 'Functional'),
        ('support', 'Support')],
        string='Category',
    )
    subject = fields.Char(
        string="Subject"
    )
    description = fields.Text(
        string="Description"
    )
    priority = fields.Selection(
        [('0', 'Low'),
        ('1', 'Middle'),
        ('2', 'High')],
        string='Priority',
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
    )
    request_date = fields.Datetime(
        string='Create Date',
        default=fields.Datetime.now,
        copy=False,
    )
    close_date = fields.Datetime(
        string='Close Date',
    )
    user_id = fields.Many2one(
        'res.users',
        string='Technician',
    )
    department_id = fields.Many2one(
        'hr.department',
        string='Department'
    )
    timesheet_line_ids = fields.One2many(
        'account.analytic.line',
        'repair_request_id',
        string='Timesheets',
    )
    is_close = fields.Boolean(
        string='Is Ticket Closed ?',
        track_visibility='onchange',
        default=False,
        copy=False,
    )
    total_spend_hours = fields.Float(
        string='Total Hours Spent',
        compute='_compute_total_spend_hours'
    )
    project_id = fields.Many2one(
        'project.project',
        string='Project',
    )
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
    )
    team_id = fields.Many2one(
        'machine.support.team',
        string='Machine Repair Team',
        default=lambda self: self.env['machine.support.team'].sudo()._get_default_team_id(user_id=self.env.uid),
    )
    team_leader_id = fields.Many2one(
        'res.users',
        string='Team Leader',
    )
    journal_id = fields.Many2one(
        'account.journal',
         string='Journal',
     )
    task_id = fields.Many2one(
        'project.task',
        string='Task',
        readonly = True,
    )
    is_task_created = fields.Boolean(
        string='Is Task Created ?',
        default=False,
    )
    company_id = fields.Many2one(
        'res.company', 
        default=lambda self: self.env.user.company_id, 
        string='Company',
        readonly=True,
     )
    comment = fields.Text(
        string='Customer Comment',
        readonly=True,
    )
    rating = fields.Selection(
        [('poor', 'Poor'),
        ('average', 'Average'),
        ('good', 'Good'),
        ('very good', 'Very Good'),
        ('excellent', 'Excellent')],
        string='Customer Rating',
        readonly=True,
    )
    product_category = fields.Many2one(
        'product.category',
        string="Product Category"
    )
    product_id = fields.Many2one(
        'product.product',
        domain="[('is_machine', '=', True)]",
        string="Product"
    )
    brand = fields.Char(
        string = "Brand"
    )
    color = fields.Char(
        string = "Color"
    )
    model = fields.Char(
        string="Model"
    )
    year = fields.Char(
        string="Year"
    )
    accompanying_items = fields.Text(
        string="Accompanying Items",
    )
    damage = fields.Text(
        string="Damage",
    )
    warranty = fields.Boolean(
        string="Warranty",
    )
    img1 = fields.Binary(
        string="Images1",
    )
    img2 = fields.Binary(
        string="Images2",
    )
    img3 = fields.Binary(
        string="Images3",
    )
    img4 = fields.Binary(
        string="Images4",
    )
    img5 = fields.Binary(
        string="Images5",
    )
    repair_types_ids = fields.Many2many(
        'repair.type',
        string="Repair Type"
    )
    problem = fields.Text(
       string="Problem",
    )
    cosume_part_ids = fields.One2many(
      'product.consume.part',
      'machine_id',
      string="Produ Ctconsume Part"
    )
    nature_of_service_id = fields.Many2one(
        'service.nature',
        string="Nature Of service"
    )
    lot_id = fields.Many2one(
        'stock.production.lot',
        string="Lot"
    )
    website_brand = fields.Char(
        string = "Website Brand"
    )
    website_model = fields.Char(
        string = "Website Model"
    )
    website_year = fields.Char(
        string = "Website Year"
    )
#     @api.multi
#     @api.depends('analytic_account_id')
#     def compute_total_hours(self):
#         total_remaining_hours = 0.0
#         for rec in self:
#             rec.remaining_hours = rec.analytic_account_id.remaining_hours
#     
    total_consumed_hours = fields.Float(
        string='Total Consumed Hours',
#         compute='compute_total_hours',
#         store=True,
    )

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        for rec in self:
            if rec.partner_id:
                rec.email = rec.partner_id.email
                rec.phone = rec.partner_id.phone

    @api.multi
    @api.onchange('product_category')
    def product_id_change(self):
        return {'domain':{'product_id':[('is_machine', '=', True),('categ_id', '=', self.product_category.id)]}}

    @api.multi
    @api.onchange('team_id')
    def team_id_change(self):
        for rec in self:
            rec.team_leader_id = rec.team_id.leader_id.id
    
    @api.one
    def unlink(self):
        for rec in self:
            if rec.state != 'new':
                raise Warning(_('You can not delete record which are not in draft state.'))
        return super(MachineRepairSupport, self).unlink()
    
    @api.multi
    def show_machine_diagnosys_task(self):
        for rec in self:
            res = self.env.ref('machine_repair_management.action_view_task_diagnosis')
            res = res.read()[0]
            res['domain'] = str([('task_type','=','diagnosys'), ('ticket_id', '=', rec.id)])
            res['context'] = {'default_ticket_id': rec.id, 'default_task_type': 'diagnosys'}
        return res
    
    @api.multi
    def show_work_order_task(self):
        for rec in self:
            res = self.env.ref('project.action_view_task')
            res = res.read()[0]
            res['domain'] = str([('task_type','=','work_order'), ('ticket_id', '=', rec.id)])
            res['context'] = {'default_ticket_id': rec.id, 'default_task_type': 'work_order'}
        return res


class HrTimesheetSheet(models.Model):
    _inherit = 'account.analytic.line'

    support_request_id = fields.Many2one(
        'machine.repair.support',
        domain=[('is_close','=',False)],
        string='Machine Repair Support',
    )
    billable = fields.Boolean(
        string='Chargable?',
        default=True,
    )
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
