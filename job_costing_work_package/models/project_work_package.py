# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError, RedirectWarning, ValidationError, Warning


class ProjectWorkPackage(models.Model):
    _name = "project.work.package"
    _description = 'Work Packages'
    _order = 'id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']

    name = fields.Char(
        string='Name', 
        required=True,
        copy=True,
    )
    date = fields.Date(
        string='Date', 
        default=fields.date.today(),
        copy=True,
        required=True,
    )
    company_id = fields.Many2one(
        'res.company', 
        'Company',
        default=lambda self: self.env.user.company_id,
        copy=True, 
        readonly=True,
    )
    user_id = fields.Many2one(
        'res.users',
        'Responsible User',
        required=True,
        default=lambda self: self.env.user.id,
        copy=True,
    )
    project_id = fields.Many2one(
        'project.project', 
        string='Project',
        required=True,
        copy=True,
    )
    task_ids = fields.Many2many(
        'project.task', 
        string='Work Package Lines',
        copy=False,
    )
    number = fields.Char(
        string='Number' ,
        readonly=True,
        copy=False
    )
    partner_id = fields.Many2one(
        'res.partner', 
        string='Customer',
        copy=True,
        required=True,
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('sent', 'Sent'),
        ('cancel','Cancelled')],
        default='draft',
        string='Stage',
        copy=False,
        track_visibility='onchange',
    )
    internal_notes = fields.Text(
        string="Internal Notes",
    )

    @api.multi
    def action_confirm(self):
        for rec in self:
            rec.state = 'confirm'
    
    @api.multi
    def action_draft(self):
        for rec in self:
            rec.state = 'draft'

    @api.multi
    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    @api.multi
    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise UserError("You can not delete record which is not in draft state.")
        return super(ProjectWorkPackage,self).unlink()

    @api.model
    def create(self, vals):
        number = self.env['ir.sequence'].next_by_code('project.work.sequence')
        vals.update({
            'number': number,
            })
        return super(ProjectWorkPackage, self).create(vals)


    @api.multi
    def action_send(self, vals):
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = self.env.ref('job_costing_work_package.email_work_packages_templates').id
        except ValueError:
            template_id = False
        try:
            compose_form_id = self.env.ref('mail.email_compose_message_wizard_form').id
        except ValueError:
            compose_form_id = False
        ctx = {
            'default_model': 'project.work.package',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'force_email': True
        }
        self.state = 'sent'
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
