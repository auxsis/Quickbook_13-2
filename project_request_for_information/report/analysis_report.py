# -*- coding: utf-8 -*-

from odoo import models, fields, tools, api

class RequestInformationReport(models.Model):
    _name = "request.information.report"
    _auto = False

    allow_user_ids = fields.Many2many(
        'res.users',
        string='Allow Users'
    )
    company_id = fields.Many2one(
        'res.company', 
        'Company', 
        readonly=True
    )
    priority = fields.Selection(
        [('0', 'Low'), 
        ('1', 'Normal'), 
        ('2', 'High')],
    )
    project_id = fields.Many2one(
        'project.project', 
        'Project', 
        readonly=True
    )
    user_id = fields.Many2one(
        'res.users', 
        'Assigned to', 
        readonly=True
    )
    partner_id = fields.Many2one(
        'res.partner', 
        'Contact'
    )
    email = fields.Char(
        'Emails',
         readonly=True
     )
    phone = fields.Char(
        string="Phone"
    )
    name = fields.Char(
        string='Number', 
        required=True, 
        copy=False, 
        readonly=True, 
    )
    subject = fields.Char(
        string="Subject"
    )
    team_id = fields.Many2one(
        'request.information.team',
        string='Request Team',
    )
    team_leader_id = fields.Many2one(
        'res.users',
        string='Team Leader',
        related ='team_id.leader_id',
        store=True,
    )
    close_date = fields.Datetime(
        string='Close Date',
    )
    is_close = fields.Boolean(
        string='Is Ticket Closed ?',
        track_visibility='onchange',
        default=False,
        copy=False,
    )
    category = fields.Selection(
        [('technical', 'Technical'),
        ('functional', 'Functional'),
        ('support', 'Support')],
        string='Category',
    )
    request_date = fields.Datetime(
        string='Create Date',
        default=fields.date.today(),
    )
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
    )
    type_ticket_id = fields.Many2one(
        'request.information',
        string="RFI Type",
    )
    subject_type_id = fields.Many2one(
        'request.information.subject',
        string="RFI Subject",
    )
    stage_id = fields.Many2one(
        'request.information.stage.config',
        string='stage',
    )
    planned_revenue = fields.Float(
        'Expected Revenue',
    )
    job_cost_id = fields.Many2one(
        'job.costing',
        string="Job Cost Sheet",
    )
    job_cost_line_id = fields.Many2one(
        'job.cost.line',
        string='Job Cost Line',
    )

    def _select(self):
        select_str = """
            SELECT
                c.id as id,
                c.name as name,
                c.request_date as request_date,
                c.close_date as close_date,
                c.user_id,
                c.is_close,
                c.company_id as company_id,
                c.priority as priority,
                c.project_id as project_id,
                c.subject as subject,
                c.phone as phone,
                c.team_id as team_id,
                c.analytic_account_id as analytic_account_id,
                c.category,
                c.team_leader_id as team_leader_id,
                c.partner_id,
                c.stage_id,
                c.planned_revenue,
                c.type_ticket_id,
                c.subject_type_id,
                c.job_cost_id,
                c.job_cost_line_id
        """
        return select_str

    def _from(self):
        from_str = """
                request_information c
        """
        return from_str

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE OR REPLACE VIEW %s as (
                %s
            FROM 
                %s
            )""" % (self._table, self._select(), self._from()))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
