# -*- coding: utf-8 -*-

from datetime import date
from odoo import models, fields, api, _, SUPERUSER_ID, tools
from odoo.exceptions import UserError, Warning

class RequestInformation(models.Model):
    _name = 'request.information'
    _description = 'Request for Information'
    _order = 'id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    

    @api.multi
    def _write(self, vals):#this is to fix access error on stage write with other records.
        if len(vals.keys()) == 1 and 'stage_type' in vals:
            return super(RequestInformation, self.sudo())._write(vals)
        return super(RequestInformation, self)._write(vals)


    @api.model
    def create(self, vals):
        if vals.get('name', False):
            if vals.get('name', 'New') != 'New':
                vals['subject'] = vals['name']
                vals['name'] = 'New'
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('request.information') or 'New'
        
        # set up context used to find the lead's sales team which is needed
        # to correctly set the default stage_id
        context = dict(self._context or {})
        if vals.get('type') and not self._context.get('default_type'):
            context['default_type'] = vals.get('type')
        if vals.get('team_id') and not self._context.get('default_team_id'):
            context['default_team_id'] = vals.get('team_id')

        if not vals.get('partner_id', False) and vals.get('email', ''):
            partner = self.env['res.partner'].sudo().search([('email', '=', vals['email'])], limit=1)
            if partner:
                vals.update({'partner_id': partner.id})

        if vals.get('team_id') and not vals.get('team_leader_id'):
            vals['team_leader_id'] = self.env['request.information.team'].browse(vals.get('team_id')).leader_id.id

        # context: no_log, because subtype already handle this
        return super(RequestInformation, self.with_context(context, mail_create_nolog=True)).create(vals)

    @api.onchange('project_id')
    def onchnage_project(self):
        for rec in self:
            rec.analytic_account_id = rec.project_id.analytic_account_id

    @api.multi
    def _compute_kanban_state(self):
        today = date.today()
        for help_desk in self:
            kanban_state = 'grey'
            if help_desk.date_action:
                lead_date = fields.Date.from_string(help_desk.date_action)
                if lead_date >= today:
                    kanban_state = 'green'
                else:
                    kanban_state = 'red'
            help_desk.kanban_state = kanban_state

    @api.one
    def set_to_close(self):
        stage_id = self.env['request.information.stage.config'].search([('stage_type','=','closed')])
        if self.is_close != True:
            self.is_close = True
            self.close_date = fields.Datetime.now()#time.strftime('%Y-%m-%d')
            self.stage_id = stage_id.id
            template = self.env.ref('project_request_for_information.email_template_request_information')
            print('template=========2222222222======',template)
            template.send_mail(self.id, force_send=True)
            print('template============333333=================',template)
            
    @api.one
    def set_to_reopen(self):
        stage_id = self.env['request.information.stage.config'].search([('stage_type','=','work_in_progress')])
        if self.is_close != False:
            self.is_close = False
            self.stage_id = stage_id.id

    def _default_stage_id(self):
        team = self.env['request.information.team'].sudo()._get_default_team_id(user_id=self.env.uid)
        return self._stage_find(team_id=team.id, domain=[('fold', '=', False)]).id

    @api.multi
    def close_dialog(self):
        return {'type': 'ir.actions.act_window_close'}

    def _stage_find(self, team_id=False, domain=None, order='sequence'):
        """ Determine the stage of the current lead with its teams, the given domain and the given team_id
            :param team_id
            :param domain : base search domain for stage
            :returns crm.stage recordset
        """
        team_ids = set()
        if team_id:
            team_ids.add(team_id)
        for help in self:
            if help.team_id:
                team_ids.add(help.team_id.id)
        # generate the domain
        if team_ids:
            search_domain = ['|', ('team_id', '=', False), ('team_id', 'in', list(team_ids))]
        else:
            search_domain = [('team_id', '=', False)]
        # AND with the domain in parameter
        if domain:
            search_domain += list(domain)
        # perform search, return the first found
        return self.env['request.information.stage.config'].search(search_domain, order=order, limit=1)
    
    name = fields.Char(
        string='Number', 
        required=False,
        default='New',
        copy=False, 
        readonly=True, 
    )
    email = fields.Char(
        string="Email",
        required=False
    )
    phone = fields.Char(
        string="Phone"
    )
    category = fields.Selection(
        [('technical', 'Substitution/Construction Modification'),
        ('functional', 'Clarification or Additional Information'),
        ('support', 'Other')],
        string='RFI Category',
    )
    subject = fields.Char(
        string="Subject"
    )
    type_ticket_id = fields.Many2one(
        'request.information.type',
        string="Type",
        copy=False,
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
        string='Customer/Supplier',
    )
    request_date = fields.Datetime(
        string='Create Date',
        default=fields.Datetime.now,
        copy=False,
    )
    close_date = fields.Datetime(
        string='Closed Date',
    )
    user_id = fields.Many2one(
        'res.users',
        string='Assign To',
    )
    timesheet_line_ids = fields.One2many(
        'account.analytic.line',
        'rfi_request_information_id',
        string='Timesheets',
    )
    is_close = fields.Boolean(
        string='Is Closed ?',
        track_visibility='onchange',
        default=False,
        copy=False,
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
        'request.information.team',
        string='RFI Team',
        default=lambda self: self.env['request.information.team'].sudo()._get_default_team_id(user_id=self.env.uid),
    )
    team_leader_id = fields.Many2one(
        'res.users',
        string='Team Leader',
    )
    journal_id = fields.Many2one(
        'account.journal',
         string='Invoice Journal',
     )
    task_id = fields.Many2one(
        'project.task',
        string='Job Order',
        copy=False,
    )
    company_id = fields.Many2one(
        'res.company', 
        default=lambda self: self.env.user.company_id, 
        string='Company',
        readonly=True,
     )
    comment = fields.Text(
        string='Customer/Supplier Comment',
        readonly=True,
    )
    rating = fields.Selection(
        [('poor', 'Poor'),
        ('average', 'Average'),
        ('good', 'Good'),
        ('very good', 'Very Good'),
        ('excellent', 'Excellent')],
        string='Customer/Supplier Rating',
        readonly=True,
    )
    subject_type_id = fields.Many2one(
        'request.information.subject',
        string="Subject",
        copy=True,
    )
    allow_user_ids = fields.Many2many(
        'res.users',
        string='Allow Users'
    )
    rfi_request_answer = fields.Text(
        string="RFI Answer",
    )
    note = fields.Text(
        'Internal Note',
    )

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        # retrieve team_id from the context and write the domain
        # - ('id', 'in', stages.ids): add columns that should be present
        # - OR ('fold', '=', False): add default columns that are not folded
        # - OR ('team_ids', '=', team_id), ('fold', '=', False) if team_id: add team columns that are not folded
        team_id = self._context.get('default_team_id')
        if team_id:
            search_domain = ['|', ('id', 'in', stages.ids), '|', ('team_id', '=', False), ('team_id', '=', team_id)]
        else:
            search_domain = ['|', ('id', 'in', stages.ids), ('team_id', '=', False)]

        # perform search
        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)
    
    
    stage_id = fields.Many2one(
                'request.information.stage.config',
                string='Stage',
                track_visibility='onchange',
                index=True,
                domain="['|', ('team_id', '=', False), ('team_id', '=', team_id)]",
                group_expand='_read_group_stage_ids', 
                default=lambda self: self._default_stage_id(),
                store=True
    )
    stage_type = fields.Selection(
        'Type',
        store=True,
        related='stage_id.stage_type',
    )
    active = fields.Boolean('Active', default=True)
    color = fields.Integer(
            'Color Index',
            default=0
    )
    planned_revenue = fields.Float(
                        'Expected Revenue',
                        track_visibility='always'
    )
    kanban_state = fields.Selection([('grey', 'No next activity planned'), 
                    ('red', 'Next activity late'), 
                    ('green', 'Next activity is planned')],
                    string='Activity State',
                    compute='_compute_kanban_state',
    )
    date_action = fields.Date('Next Activity Date', index=True)

    job_cost_id = fields.Many2one(
        'job.costing',
        string="Job Cost Sheet",
    )
    job_cost_line_id = fields.Many2one(
        'job.cost.line',
        string='Job Cost Line',
    )
    rfi_survey_ids = fields.One2many(
        'survey.survey',
        'rfi_request_id',
        string='Request Information Surveys'
    )

    @api.multi
    @api.onchange('team_id')
    def team_id_change(self):
        for rec in self:
            rec.team_leader_id = rec.team_id.leader_id.id

    @api.multi
    @api.onchange('partner_id')
    def partner_id_change(self):
        for rec in self:
            rec.email = rec.partner_id.email
            rec.phone = rec.partner_id.phone

    @api.one
    def unlink(self):
        for rec in self:
            if rec.stage_id.stage_type != 'new':
                raise Warning(_('You can not delete record which are not in draft state.'))
        return super(RequestInformation, self).unlink()

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        """ Overrides mail_thread message_new that is called by the mailgateway
            through message_process.
            This override updates the document according to the email.
        """
        self = self.with_context(default_user_id=False)

        if custom_values is None:
            custom_values = {}
        defaults = {
            'name':  msg_dict.get('subject') or _("No Subject"),
            'email': msg_dict.get('from'),
            'email_cc': msg_dict.get('cc'),
            'partner_id': msg_dict.get('author_id', False),
        }
        if 'body' in msg_dict:
            body_msg = tools.html2plaintext(msg_dict['body'])
            defaults.update(description=body_msg)
        defaults.update(custom_values)
        return super(RequestInformation, self).message_new(msg_dict, custom_values=defaults)

    @api.multi
    def action_show_survey(self):
        self.ensure_one()
        action = self.env.ref('survey.action_survey_form')
        action = action.read()[0]
        action['domain'] = str([('rfi_request_id', '=', self.id)])
        action['context'] = {'default_rfi_request_id': self.id}
        return action

    @api.multi
    def action_create_survey(self):
        survey_obj = self.env['survey.survey']
        for rec in self:
            survey_vals = {
                'title': rec.name + ' ' + rec.subject,
                'rfi_request_id' : rec.id,
            }
            survey_id = survey_obj.create(survey_vals)
            return survey_id.action_test_survey()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
