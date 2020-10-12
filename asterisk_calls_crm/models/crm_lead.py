import logging
from odoo import api, models, tools, fields, _
from odoo.exceptions import ValidationError, UserError
try:
    from odoo.addons.phone_validation.tools import phone_validation
    import phonenumbers
    PHONE_VALIDATION = True
except ImportError:
    PHONE_VALIDATION = False

logger = logging.getLogger(__name__)


class Lead(models.Model):
    _name = 'crm.lead'
    _inherit = 'crm.lead'

    asterisk_calls_count = fields.Integer(compute='_get_asterisk_calls_count',
                                          string=_('Calls'))

    @api.multi
    def _get_asterisk_calls_count(self):
        for rec in self:
            rec.asterisk_calls_count = self.env[
                'asterisk_calls.call'].search_count([('lead', '=', rec.id)])

    @api.multi
    def write(self, values):
        res = super(Lead, self).write(values)
        if res:
            self.pool.clear_caches()
        return res


    @api.multi
    def unlink(self):
        res = super(Lead, self).unlink()
        if res:
            self.pool.clear_caches()


    @api.model
    def create(self, vals):
        res = super(Lead, self).create(vals)
        try:
            if self.env.context.get('create_call_lead'):
                call = self.env['asterisk_calls.call'].browse(
                                    self.env.context['create_call_lead'])
                call.lead = res.id
        except Exception as e:
            logger.exception(e)
        if res:
            self.pool.clear_caches()
        return res


    @tools.ormcache('number')
    def _search_lead_by_number(self, number):
        # Get last open lead
        found = self.env['crm.lead'].sudo().search([
                          '|', '|',
                          ('phone', '=', number),
                          ('mobile', '=', number),
                          ('partner_address_phone', '=', number),
                          ('probability', '>', 0),
                          ('probability', '<', 100)],
            limit=1, order='id desc')
        if len(found) == 1:
            logger.debug('FOUND LEAD BY NUMBER {}'.format(number))
            return found[0]
        else:
            logger.debug('LEAD BY NUMBER {} NOT FOUND'.format(number))


    @tools.ormcache('number')
    def get_lead_by_number(self, number):
        if not number or 'unknown' in number or number == 's':
            logger.debug('GET LEAD BY NUMBER NO NUMBER PASSED')
            return
        lead = None
        number = self.env['res.partner']._strip_number(number)
        number_plus = '+' + number if number[0] != '+' else number
        # First of all we check if CRM phone validation is activated
        if PHONE_VALIDATION:
            country_code = self.env['res.users'].sudo(
                                        ).browse(1).company_id.country_id.code
            # Assume we got a local phone number
            if number[0] != '+':
                local_number = self.env['res.partner']._get_formatted_number(
                                                        number, country_code)
                if local_number:
                    logger.debug('LEAD LOCAL NUMBER SEARCH')
                    lead = self._search_lead_by_number(local_number)
            # Seems not, so let try to seach formatted  international
            if not lead:
                int_number = self.env['res.partner']._get_formatted_number(number_plus)
                logger.debug('LEAD INT NUMBER SEARCH')
                if int_number:
                    lead = self._search_lead_by_number(int_number)
            # May be some local contacts in international format?
            if not lead:
                local_int_number = self.env['res.partner']._get_formatted_number(
                                        number, country_code, national=False)
                logger.debug('LEAD LOCAL INT NUMBER SEARCH')
                if local_int_number:
                    lead = self._search_lead_by_number(local_int_number)
        # PHONE_VALIDATION not used, use exact searches
        if not lead:
            logger.debug('LEAD EXACT NUMBER {} SEARCH'.format(number))
            lead = self._search_lead_by_number(number)
        # Try to search with + added
        if not lead and number[0] != '+':
            logger.debug('LEAD PLUS NUMBER {} SEARCH'.format(number_plus))
            lead = self._search_lead_by_number(number_plus)
        logger.debug(u'GET LEAD BY NUMBER RESULT: {}'.format(lead))
        return lead


    def _get_lead_country_code(self, lead):
        if lead.country_id:
            return lead.country_id.code
        elif lead.partner_id and lead.partner_id.country_id:
            return lead.partner_id._get_partner_country_code(lead.partner_id)
        else:
            super_user = self.env['res.users'].sudo().browse(1)
            if super_user.company_id.country_id:
                # Return Odoo's main company country
                return super_user.company_id.country_id.code


    @tools.ormcache('number', 'res_id')
    def _format_number(self, number, res_id):
        if not PHONE_VALIDATION:
            return number
        if not number:
            raise ValidationError(_('Phone number not set!'))
        if not res_id:
            raise ValidationError(_('Lead ID not defined!'))
        lead = self.env['crm.lead'].browse(res_id)
        country_code = self._get_lead_country_code(lead)
        # Check if partner has country_id set and phone validation is available
        if not country_code:
            logger.debug('CANNOT GET LEAD COUNTRY CODE')
            return number
        try:
            phone_nbr = phone_validation.phone_parse(number, country_code)
            if not phone_nbr:
                logger.debug('COULD NOT FORMAT LEAD NUMBER')
                return number
            # We got a parsed number
            return phonenumbers.format_number(
                                    phone_nbr,
                                    phonenumbers.PhoneNumberFormat.E164)
        except UserError:
            logger.debug('ERROR FORMATTING LEAD NUMBER')
            return number
