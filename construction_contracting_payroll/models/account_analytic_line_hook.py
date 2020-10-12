# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    @api.model
    def _get_timesheet_cost_hook(self, timesheet):
        cost = timesheet.employee_id.timesheet_cost or 0.0
        return cost

    @api.model
    def _get_field_name_hook(self):
        field_name_lst = ['unit_amount', 'employee_id', 'account_id']
        return field_name_lst

#     @api.multi
#     def _timesheet_postprocess(self, values):
#         sudo_self = self.sudo()  # this creates only one env for all operation that required sudo()
#         # (re)compute the amount (depending on unit_amount, employee_id for the cost, and account_id for currency)
# #        if any([field_name in values for field_name in ['unit_amount', 'employee_id', 'account_id']]):
#         if any([field_name in values for field_name in self._get_field_name_hook()]):#call
#             for timesheet in sudo_self:
#                 uom = timesheet.employee_id.company_id.project_time_mode_id
# #                cost = timesheet.employee_id.timesheet_cost or 0.0
#                 cost = self._get_timesheet_cost_hook(timesheet)#call hook
#                 amount = -timesheet.unit_amount * cost
#                 amount_converted = timesheet.employee_id.currency_id.compute(amount, timesheet.account_id.currency_id)
#                 timesheet.write({
#                     'amount': amount_converted,
#                     'product_uom_id': uom.id,
#                 })
#         # (re)compute the theorical revenue
#         if any([field_name in values for field_name in ['so_line', 'unit_amount', 'account_id']]):
#             sudo_self._timesheet_compute_theorical_revenue()
#         return values
    

    @api.multi
    def _timesheet_postprocess_values(self, values):
        """ Get the addionnal values to write on record
            :param dict values: values for the model's fields, as a dictionary::
                {'field_name': field_value, ...}
            :return: a dictionary mapping each record id to its corresponding
                dictionnary values to write (may be empty).
        """
        result = dict.fromkeys(self.ids, dict())
        sudo_self = self.sudo()  # this creates only one env for all operation that required sudo()
        # (re)compute the amount (depending on unit_amount, employee_id for the cost, and account_id for currency)
        if any([field_name in values for field_name in self._get_field_name_hook()]):
            for timesheet in sudo_self:
#                 cost = timesheet.employee_id.timesheet_cost or 0.0
                cost = self._get_timesheet_cost_hook(timesheet)#call hook
                amount = -timesheet.unit_amount * cost
                amount_converted = timesheet.employee_id.currency_id._convert(
                    amount, timesheet.account_id.currency_id, self.env.user.company_id, timesheet.date)
                result[timesheet.id].update({
                    'amount': amount_converted,
                })
        return result


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
