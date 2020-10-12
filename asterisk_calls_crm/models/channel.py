import json
import logging
from odoo import models, fields, api, _

logger = logging.getLogger(__name__)


class CrmChannel(models.Model):
    _name = 'asterisk_calls.channel'
    _inherit = 'asterisk_calls.channel'

    lead = fields.Many2one('crm.lead', ondelete='set null',
                           string=_('Lead / Opportunity'))


    @api.model
    def update_channel_values(self, original_vals):
        vals = super(CrmChannel, self).update_channel_values(original_vals)
        src = original_vals['callerid_num']
        exten = original_vals['exten']
        connected_line_num = original_vals['connected_line_num']
        lead = self.env['crm.lead'].get_lead_by_number(src)
        if not lead:
            lead = self.env['crm.lead'].get_lead_by_number(connected_line_num)
        if not lead:
            lead = self.env['crm.lead'].get_lead_by_number(exten)
        if lead:
            vals.update({'lead': lead.id})
        return vals


    @api.multi
    def reload_channels(self):
        # Add lead and view ids to the message
        self.ensure_one()
        auto_reload = self.env['asterisk_calls.util'].sudo(
                            ).get_asterisk_calls_param('auto_reload_channels')
        lead_id = self.sudo().lead.id if self.sudo().lead else False
        if lead_id:
            if self.sudo().lead.type == 'opportunity':
                view_id = self.env['ir.model.data'].sudo().xmlid_to_res_id(
                                            'crm.crm_case_form_view_oppor')
            else:
                view_id = self.env['ir.model.data'].sudo().xmlid_to_res_id(
                                            'crm.crm_case_form_view_leads')
        else:
            view_id = False
        self.env['bus.bus'].sendone('asterisk_calls_channels', json.dumps({
                                    'event': 'update_channel',
                                    'dst': self.exten,
                                    'channel': self.channel_short,
                                    'partner_id': self.partner.id,
                                    'auto_reload': auto_reload,
                                    'lead_id': lead_id,
                                    'view_id': view_id}))

    @api.multi
    def open_opportunity(self):
        self.ensure_one()
        return {
            'res_model': 'crm.lead',
            'res_id': self.lead.id,
            'name': _('Create Opportunity'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': self.env['ir.model.data'].xmlid_to_res_id(
                                            'crm.crm_case_form_view_oppor'),
        }
