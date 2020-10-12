# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class TransmittalDocument(models.Model):
    _name = 'transmittal.document'
    _description = 'Transmittal Communication Documents'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _rec_name = 'number'
    
    number = fields.Char(
        string="Number",
        readonly=True,
        copy=False
    )
    name = fields.Char(
        string='Name',
        required=True,
    )
    state = fields.Selection(
        [('draft','New'),
         ('confirm', 'Confirmed'),
         ('approve', 'Approved'),
         ('send', 'Sent'),
         ('reject', 'Refused')],
        string='Status',
        default='draft',
        copy=False,
        track_visibility='onchange',
    )
    sending_date = fields.Date(
        string='Date of Sending',
        required=True,
    )
    sender_company_id = fields.Many2one(
        'res.partner',
        string='Sender Company',
        required=True,
    )
    receiver_company_id = fields.Many2one(
        'res.partner',
        string='Receiver Company',
        copy=False
    )
    project_id = fields.Many2one(
        'project.project',
        string='Project',
        required=True,
    )
    job_costsheet_id = fields.Many2one(
        'job.costing',
        string='Job Costsheet',
    )
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        required=True,
    )
    reason_for_send = fields.Text(
        string='Reason for Sending',
    )
    deadline = fields.Date(
        string='Deadline'
    )
    description = fields.Text(
        string='Description Taken by Recipient'
    )
    user_id = fields.Many2one(
        'res.users',
        default=lambda self: self.env.user, 
        string='Responsible User',
    )
    company_id = fields.Many2one(
        'res.company', 
        default=lambda self: self.env.user.company_id, 
        string='Company',
        readonly=True,
    )
    transmittal_line_ids = fields.One2many(
        'transmittal.document.line',
        'transmittal_id',
        string='Documents',
        copy=True
    )
    job_order_id = fields.Many2one(
        'project.task',
        string='Job Order'
    )
    document_type = fields.Selection(
        [('submittal_type','Submittal'),
         ('transmittal_type','Transmittal')],
        string='Document Type',
    )
    
    @api.model
    def create(self, vals):
        document_type = self._context.get('default_document_type')
        if document_type == 'transmittal_type':
            vals['number'] = self.env['ir.sequence'].next_by_code('transmittal.documents')
        if document_type == 'submittal_type':
            vals['number'] = self.env['ir.sequence'].next_by_code('submittal.documents')
        return super(TransmittalDocument, self).create(vals)
    
    @api.multi
    def unlink(self):
        for document in self:
            if document.state not in ('draft'):
                raise UserError(_('You cannot delete only New Document .'))
        return super(TransmittalDocument, self).unlink()
    
    @api.multi
    def action_send_transmittal_document(self):
        '''
        This function opens a window to compose an email, with the documents template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('transmittals_communication_document', 'email_template_transmittal_submittal_doc')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = {
            'default_model': 'transmittal.document',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'force_email': True
        }
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
        

class TransmittalDocumentLine(models.Model):
    _name = 'transmittal.document.line'
    
    transmit_type_id = fields.Many2one(
        'transmittal.type',
        string='Type',
        required=True,
    )
    transmit_medium_id = fields.Many2one(
        'transmittal.medium',
        string='Channel',
        required=True,
    )
    name = fields.Char(
        string='Name',
        required=True
    )
    description = fields.Char(
        string='Description',
        required=True,
    )
    transmittal_id = fields.Many2one(
        'transmittal.document',
        string='Transmittal Document'
    )

class TransmittalMedium(models.Model):
    _name = 'transmittal.medium'
    
    name = fields.Char(
        string='Name',
        required=True
    )

class TransmittalType(models.Model):
    _name = 'transmittal.type'
    
    name = fields.Char(
        string='Name',
        required=True
    )