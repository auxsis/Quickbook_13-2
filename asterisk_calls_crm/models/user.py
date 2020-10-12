from odoo import models, api, tools


class User(models.Model):
    _inherit = 'asterisk_calls.user'


    @api.model
    def originate_partner(self, model_name, res_id, number):
        if model_name == 'crm.lead':
            number = self.get_lead_number(res_id, number)
            return self.originate_call(number)
