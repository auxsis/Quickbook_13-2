import logging
from odoo import models, fields, api, _

logger = logging.getLogger(__name__)


class CrmCall(models.Model):
    _name = 'asterisk_calls.call'
    _inherit = 'asterisk_calls.call'

    lead = fields.Many2one('crm.lead', ondelete='set null',
                           string=_('Lead / Opportunity'))


    @api.model
    def create(self, vals):
        if not self.env['ir.config_parameter'].sudo().get_param(
                            'asterisk_calls.auto_create_leads_from_calls'):
            return super(CrmCall, self).create(vals)
        # Auto create leads from incoming calls
        call = super(CrmCall, self).create(vals)
        if not call.partner and call.dst_user and not call.lead:
            sales_person_id = self.env['ir.config_parameter'].sudo().get_param(
                'asterisk_calls.auto_create_leads_sales_person')
            lead = self.env['crm.lead'].sudo().create({
                'name': call.clid,
                'phone': call.src,
                'user_id': int(sales_person_id) if sales_person_id else False,
            })
            call.lead = lead
        return call


    @api.model
    def update_cdr_values(self, original_vals):
        vals = super(CrmCall, self).update_cdr_values(original_vals)
        dst = original_vals['dst']
        src = original_vals['src']
        # First find by originate data
        if self.env.context.get('originate_model') and \
                self.env.context.get('originate_model') == 'crm.lead' and \
                self.env.context.get('originate_res_id'):
            vals['lead'] = self.env.context.get('originate_res_id')
            logger.debug('FOUND CRM LEAD %s BY ORIGINATE DATA',
                         self.env.context.get('originate_res_id'))
            # Check if lead has a contact so that we also set lead's partner.
            lead = self.env['crm.lead'].sudo().browse(
                self.env.context.get('originate_res_id'))
            if lead.partner_id:
                logger.debug('SETTINGS CALL PARTNER %s FROM LEAD %s',
                             lead.partner_id.id, lead.id)
                vals['partner'] = lead.partner_id.id
        elif vals.get('src_user'):
            # For outgoing calls search dst
            lead = self.env['crm.lead'].get_lead_by_number(dst)
            if lead:
                vals.update({'lead': lead.id})
        elif vals.get('dst_user'):
            # For incoming calls search src
            lead = self.env['crm.lead'].get_lead_by_number(src)
            if lead:
                vals.update({'lead': lead.id})
        else:
            # If there is no dst or src users it can be incoming call to Queue or smth.
            lead = self.env['crm.lead'].get_lead_by_number(src)
            if lead:
                vals.update({'lead': lead.id})
        return vals


    @api.multi
    def create_opportunity(self):
        self.ensure_one()
        return {
            'res_model': 'crm.lead',
            'name': _('Create Opportunity'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': self.env['ir.model.data'].xmlid_to_res_id(
                                            'crm.crm_case_form_view_oppor'),
            'context': {
                'default_phone': self.dst if self.src_user else self.src,
                'default_name': self.partner.name if self.partner else self.clid,
                'default_partner_id': self.partner.id if self.partner else False,
                'default_type': 'opportunity',
                'create_call_lead': self.id,
            },
        }
