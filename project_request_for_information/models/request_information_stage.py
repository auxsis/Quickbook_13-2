# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api

AVAILABLE_PRIORITIES = [
    ('0', 'Normal'),
    ('1', 'Low'),
    ('2', 'High'),
    ('3', 'Very High'),
]

class RequestInformationStage(models.Model):
    _name = "request.information.stage.config"
    _description = "Stage of case"
    _rec_name = 'name'
    _order = "sequence, name, id"
    _sql_constraints = [
        ('stage_uniq', 'UNIQUE(stage_type)', 'The Type must be unique !')
    ]

    @api.model
    def default_get(self, fields):
        """ Hack :  when going from the pipeline, creating a stage with a sales team in
            context should not create a stage for the current sales team only
        """
        ctx = dict(self.env.context)
        if ctx.get('default_team_id') and not ctx.get('crm_team_mono'):
            ctx.pop('default_team_id')
        return super(RequestInformationStage, self.with_context(ctx)).default_get(fields)
    
    name = fields.Char(
        'Stage Name',
        required=True,
        translate=True
    )
    sequence = fields.Integer(
        'Sequence',
        default=1,
        help="Used to order stages. Lower is better."
    )
    requirements = fields.Text(
        'Requirements', 
        help="Enter here the internal requirements for this stage (ex: Offer sent to customer). It will appear as a tooltip over the stage's name."
    )
    team_id = fields.Many2one(
        'request.information.team',
        string='Support Team',
        ondelete='set null',
        help='Specific team that uses this stage. Other teams will not be able to see or use this stage.'
    )
    legend_priority = fields.Text(
        'Priority Management Explanation',
        translate=True,
        help='Explanation text to help users using the star and priority mechanism on stages or issues that are in this stage.'
    )
    fold = fields.Boolean(
        'Folded in Request Information',
        help='This stage is folded in the kanban view when there are no records in that stage to display.'
    )
    stage_type = fields.Selection(
        [('new','New'),
         ('assigned','Assigned'),
         ('work_in_progress','Work in Progress'),
         ('needs_more_info','Needs More Info'),
         ('needs_reply','Needs Reply'),
         ('reopened','Reopened'),
         ('solution_suggested','Solution Suggested'),
         ('closed','Closed')],
        copy=False,
        string='Type',
    )
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
