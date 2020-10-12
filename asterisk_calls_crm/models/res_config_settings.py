import logging
from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import ValidationError

class CallsCrmSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    auto_create_leads_from_calls = fields.Boolean()
    auto_create_leads_sales_person = fields.Many2one('res.users')

    @api.multi
    def set_values(self):
        if not (self.env.user.id == SUPERUSER_ID or
                self.env.user.has_group(
                                'asterisk_calls.group_asterisk_calls_admin')):
            raise ValidationError(
                            _('You must be Calls Administrator to use it!'))
        super(CallsCrmSettings, self).set_values()
        self.env['ir.config_parameter'].set_param(
            'asterisk_calls.auto_create_leads_from_calls',
            self.auto_create_leads_from_calls)
        self.env['ir.config_parameter'].set_param(
            'asterisk_calls.auto_create_leads_sales_person',
            self.auto_create_leads_sales_person.id)


    @api.model
    def get_values(self):
        if not (self.env.user.id == SUPERUSER_ID or
                self.env.user.has_group(
                                'asterisk_calls.group_asterisk_calls_admin')):
            raise ValidationError(
                            _('You must be Calls Administrator to use it!'))
        res = super(CallsCrmSettings, self).get_values()
        res['auto_create_leads_from_calls'] = self.env[
            'ir.config_parameter'].get_param(
                                'asterisk_calls.auto_create_leads_from_calls')
        person_id = self.env[
            'ir.config_parameter'].get_param(
                            'asterisk_calls.auto_create_leads_sales_person')
        res['auto_create_leads_sales_person'] = int(
                                            person_id) if person_id else False

        return res
