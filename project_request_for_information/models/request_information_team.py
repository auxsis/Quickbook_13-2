# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class RequestInformationTeam(models.Model):
    _name = 'request.information.team'
    _rec_name = 'name'
    _description = 'Request Team'
    
    name = fields.Char(
        string='Name',
        required=True,
    )
    team_ids = fields.Many2many(
        'res.users',
        string='Team Members'
    )
    is_team = fields.Boolean(
        'Is Default Team?',
        help='Tick this box to set this team as default support team when request come from website',
    )
    leader_id = fields.Many2one(
        'res.users',
        string='Leader',
        required=True,
    )

    @api.model
    @api.returns('self', lambda value: value.id if value else False)
    def _get_default_team_id(self, user_id=None):
        if not user_id:
            user_id = self.env.uid
        team_id = None
        if 'default_team_id' in self.env.context:
            team_id = self.env['request.information.team'].browse(self.env.context.get('default_team_id'))
        if not team_id or not team_id.exists():
            team_id = self.env['request.information.team'].sudo().search(
                ['|', ('leader_id', '=', user_id), ('team_ids', '=', user_id)],
                limit=1)
        if not team_id:
            default_team_id = self.env.ref('project_request_for_information.team_support_department', raise_if_not_found=False)
            if default_team_id and (self.env.context.get('default_type') != 'lead' or default_team_id.use_leads):
                team_id = default_team_id
        return team_id
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
