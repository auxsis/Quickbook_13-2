from odoo import models, api


class AsteriskCallsAgent(models.Model):
    _inherit = 'remote_agent.agent'

    @api.model
    def create(self, vals):
        # Add asterisk calls group to agents
        agent = super(AsteriskCallsAgent, self).create(vals)
        calls_agent_group = self.env['ir.model.data'].sudo().get_object(
                            'asterisk_calls', 'group_asterisk_calls_service')
        calls_agent_group.users = [(4, agent.user.id)]
        return agent
