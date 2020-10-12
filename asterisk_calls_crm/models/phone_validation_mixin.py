from odoo import models, registry, SUPERUSER_ID, api
try:
    from odoo.addons.phone_validation.tools import phone_validation
    with registry().cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        env['phone.validation.mixin']
    PHONE_VALIDATION = True
except (ImportError, KeyError, AttributeError):
    PHONE_VALIDATION = False


if PHONE_VALIDATION:
    class PhoneValidationMixin(models.AbstractModel):
        _inherit = 'phone.validation.mixin'

        def phone_format(self, number, country=None, company=None):
            # Numbers without country are not formatted.
            if not self.country_id:
                return number
            # CRM option "Add international prefix" is set
            if self.env.user.company_id.phone_international_format == 'prefix':
                # We format all numbers according to company set for partner
                return phone_validation.phone_format(
                    number,
                    self.country_id.code,
                    self.country_id.phone_code,
                    always_international=True,
                    raise_exception=False)
            # CRM option "No prefix" is set
            else:
                # Only local numbers must be formatted as local
                if self.env.user.company_id.country_id == self.country_id:
                    return phone_validation.phone_format(
                        number,
                        self.country_id.code,
                        self.country_id.phone_code,
                        always_international=False,
                        raise_exception=False)
                # All other countries are formatted with prefix
                else:
                    return phone_validation.phone_format(
                        number,
                        self.country_id.code,
                        self.country_id.phone_code,
                        always_international=True,
                        raise_exception=False)
