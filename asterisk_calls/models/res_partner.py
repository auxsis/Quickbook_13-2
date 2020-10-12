import logging
import re
from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError

try:
    from odoo.addons.phone_validation.tools import phone_validation
    import phonenumbers
    from phonenumbers import phonenumberutil
    PHONE_VALIDATION = True
except ImportError:
    PHONE_VALIDATION = False

logger = logging.getLogger(__name__)
number_re = re.compile('^(\+)?[0-9]+$')


class Partner(models.Model):
    _inherit = 'res.partner'

    phone = fields.Char(index=True)  # Add indexes
    mobile = fields.Char(index=True)
    asterisk_calls_count = fields.Integer(compute='_get_asterisk_calls_count')
    asterisk_extension = fields.Char(related='asterisk_user.extension',
                                     string=_('Extension'),
                                     readonly=True)
    phone_extension = fields.Char(help=_(
        'Prefix with # to add 1 second pause before entering. '
        'Every # adds 1 second pause. Example: ###1001'))
    asterisk_user = fields.One2many(comodel_name='asterisk_calls.user',
                                    inverse_name='partner')

    @api.model
    def create(self, vals):
        res = super(Partner, self).create(vals)
        try:
            if self.env.context.get('create_call_partner'):
                call = self.env[
                    'asterisk_calls.call'].browse(
                    self.env.context['create_call_partner'])
                call.partner = res.id
        except Exception as e:
            logger.exception(e)
        # Clear partners cache if record was created
        if res:
            self.pool.clear_caches()
        return res

    @api.multi
    def write(self, values):
        res = super(Partner, self).write(values)
        if res:
            self.pool.clear_caches()
        return res

    @api.multi
    def unlink(self):
        res = super(Partner, self).unlink()
        if res:
            self.pool.clear_caches()

    @api.multi
    def _get_asterisk_calls_count(self):
        for rec in self:
            if rec.is_company:
                rec.asterisk_calls_count = self.env[
                    'asterisk_calls.call'].sudo().search_count(
                    ['|', ('partner', '=', rec.id),
                          ('partner.parent_id', '=', rec.id)])
            else:
                rec.asterisk_calls_count = self.env[
                    'asterisk_calls.call'].sudo().search_count(
                    [('partner', '=', rec.id)])

    @api.multi
    def _get_asterisk_calls_user(self):
        for rec in self:
            rec.asterisk_user = self.env['asterisk_calls.user'].search(
                [('partner', '=', rec.id)], limit=1)

    @tools.ormcache('number')
    def _search_partner_by_number(self, number):
        found = self.env['res.partner'].sudo().search([
            ('is_company', '=', False),
            '|', ('phone', '=', number), ('mobile', '=', number)])
        if len(found) == 1:
            logger.debug('FOUND PARTNER BY NUMBER {}'.format(number))
            return found[0]
        elif len(found) > 1:
            logger.debug('MANY CONTACTS FOUND FOR NUMBER {}'.format(number))
            # Many partners by same number
            parents = found.mapped('parent_id')
            if not parents:
                # Just duplicates, no caller id name in this case
                logger.info(
                    'DUPLICATE PARTNERS FOR PHONE NUMBER {}'.format(number))
                return
            logger.debug('PARENTS: {}'.format(parents))
            if len(parents) > 1:
                logger.debug('PARENT COMPANIES ARE NOT THE SAME')
                return
            else:
                # We take company name as caller id name
                logger.debug(
                    'PARENT COMPANIES ARE THE SAME: {}'.format(parents[0]))
                return parents[0]
        else:
            logger.debug('PARTNER NUMBER {} NOT FOUND'.format(number))

    @tools.ormcache('number')
    def _search_company_by_number(self, number):
        found = self.env['res.partner'].sudo().search([
            ('is_company', '=', True),
            '|', ('phone', '=', number), ('mobile', '=', number)])
        if len(found) == 1:
            logger.debug('FOUND COMPANY BY NUMBER {}'.format(number))
            return found[0]
        else:
            logger.debug('COMPANY NUMBER {} NOT FOUND'.format(number))

    @tools.ormcache('number', 'country_code', 'national')
    def _get_formatted_number(self, number, country_code=None, national=True):
        if not country_code:
            # False -> None
            country_code = None
        try:
            phone_nbr = phonenumbers.parse(number, country_code)
            if not phonenumbers.is_possible_number(phone_nbr):
                logger.debug('PHONE NUMBER {} NOT POSSIBLE'.format(number))
                return
            if not phonenumbers.is_valid_number(phone_nbr):
                logger.debug('PHONE NUMBER {} NOT VALID'.format(number))
                return
            # We have a parsed number, let check what format should we give it.
            formatted_number = phonenumbers.format_number(
                phone_nbr,
                phonenumbers.PhoneNumberFormat.NATIONAL
                if country_code and national else
                phonenumbers.PhoneNumberFormat.INTERNATIONAL)
            logger.debug('FORMATTED NUMBER: {}'.format(formatted_number))
            return formatted_number
        except phonenumberutil.NumberParseException:
            logger.debug('PHONE NUMBER {} PARSE ERROR'.format(number))
            return

    def _strip_number(self, number):
        logger.debug('STIP NUMBER {} LEN {}'.format(number, len(number)))
        if '+' in number:
            logger.debug('STRIP +')
            number = number.replace('+', '')
        if ' ' in number:
            logger.debug('STRIP space')
            number = number.replace(' ', '')
        if '-' in number:
            logger.debug('STRIP -')
            number = number.replace('-', '')
        if '(' in number or ')' in number:
            logger.debug('STRIP ()')
            number = number.replace('(', '')
            number = number.replace(')', '')
        logger.debug('AFTER STRIP NUMBER {} LEN {}'.format(
            number, len(number)))
        return number

    @api.model
    @tools.ormcache('number', 'country_code')
    def get_partner_by_number(self, number, country_code=None):
        logger.debug('GET_PARTNER_BY_NUMBER {}'.format(number))
        partner_info = {'name': _('Unknown'), 'id': False}  # Default values
        partner = None
        if not number_re.match(number):
            logger.debug('CORRECT NUMBER {} NOT PASSED'.format(number))
            return partner_info
        number = self._strip_number(number)
        number_plus = '+' + number if number[0] != '+' else number
        # First of all we check if CRM phone validation is activated
        if PHONE_VALIDATION:
            if not country_code:
                # When no country code is passed we take main company country
                country_code = self.env[
                    'res.users'].sudo().browse(1).company_id.country_id.code
            # Assume we got a local phone number
            if number[0] != '+':
                local_number = self._get_formatted_number(number, country_code)
                if local_number:
                    logger.debug('LOCAL NUMBER SEARCH')
                    partner = self._search_partner_by_number(local_number)
                    if not partner:
                        partner = self._search_company_by_number(local_number)
            # Seems not, so let try to seach formatted  international
            if not partner:
                int_number = self._get_formatted_number(number_plus)
                logger.debug('INT NUMBER SEARCH')
                if int_number:
                    partner = self._search_partner_by_number(int_number)
                    if not partner:
                        partner = self._search_company_by_number(int_number)
            # May be some local contacts in international format?
            if not partner:
                local_int_number = self._get_formatted_number(
                    number, country_code, national=False)
                logger.debug('LOCAL INT NUMBER SEARCH')
                if local_int_number:
                    partner = self._search_partner_by_number(local_int_number)
                    if not partner:
                        partner = self._search_company_by_number(
                            local_int_number)
        # PHONE_VALIDATION not used, use exact searches
        if not partner:
            logger.debug('EXACT NUMBER {} SEARCH'.format(number))
            partner = self._search_partner_by_number(number)
        # Try to search with + added
        if not partner and number[0] != '+':
            logger.debug('PLUS NUMBER {} SEARCH'.format(number_plus))
            partner = self._search_partner_by_number(number_plus)
        # Try to search companies
        if not partner:
            logger.debug('EXACT COMPANY {} SEARCH'.format(number))
            partner = self._search_company_by_number(number)
        if not partner and number[0] != '+':
            logger.debug('PLUS COMPANY {} SEARCH'.format(number_plus))
            partner = self._search_company_by_number(number_plus)
        # Set partner info
        if partner:
            partner_info['id'] = partner.id
            if partner.parent_name:
                partner_info['name'] = u'{} ({})'.format(partner.name,
                                                         partner.parent_name)
            else:
                partner_info['name'] = partner.name
            logger.debug(u'FOUND PARTNER {}'.format(partner_info['name']))
        else:
            logger.debug('NO PARTNER FOUND')
        return partner_info

    def _get_partner_country_code(self, partner):
        if partner.country_id:
            # Return partner country code
            return partner.country_id.code
        elif partner.parent_id and partner.parent_id.country_id:
            # Return partner's parent country code
            return partner.parent_id.country_id.code
        elif partner.company_id and partner.company_id.country_id:
            # Return partner's company country code
            return partner.company_id.country_id.code
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
            raise ValidationError(_('Partner ID not defined!'))
        partner = self.env['res.partner'].browse(res_id)
        country_code = self._get_partner_country_code(partner)
        # Check if partner has country_id set and phone validation is available
        if not country_code:
            return number
        try:
            phone_nbr = phone_validation.phone_parse(number, country_code)
            if not phone_nbr:
                logger.debug('COULD NOT FORMAT NUMBER')
                return number
            # We got a parsed number
            return phonenumbers.format_number(
                phone_nbr, phonenumbers.PhoneNumberFormat.E164)
        except UserError:
            logger.debug('ERROR FORMATTING NUMBER')
            return number

    @api.model
    def originate_partner_extension(self, partner_id,
                                    model_name=None, res_id=None):
        partner = self.env['res.partner'].browse(partner_id)
        number = self._format_number(partner.phone, partner_id)
        extension = partner.phone_extension
        if extension and extension[0] != '#':
            # Add one # when not set any
            extension = '#' + extension
        self.env['asterisk_calls.user'].originate_call(
            number + (extension or ''), model_name=model_name, res_id=res_id)
