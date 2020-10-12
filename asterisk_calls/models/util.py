from datetime import datetime
import json
import logging
from odoo import models, api, fields, _
from odoo.exceptions import ValidationError
from .settings import CallsSettings


logger = logging.getLogger(__name__)


class Util(models.AbstractModel):
    _name = 'asterisk_calls.util'
    _description = 'Util AbstractModel'

    @api.model
    def get_asterisk_calls_param(self, module_param):
        # Used by RPC
        if type(module_param) == list:
            module_param = module_param[0]
        param = 'asterisk_calls.' + module_param
        result = self.env['ir.config_parameter'].get_param(param)
        logger.debug(u'PARAM {} RESULT {}'.format(module_param, result))
        # No ever saved, get initial default values
        if not result:
            result = dict(CallsSettings.ASTERISK_CALLS_PARAMS).get(module_param)
            logger.debug(u'GETTING DEFAULTS: {} = {}'.format(
                                                module_param, result))
        logger.debug(u'PARAM {} = {}'.format(param, result))
        if result == 'False':
            result = False
        elif result == 'True':
            result = True
        return result


class UserNotification(models.Model):
    # Model to keep if user was already notified so not to send many notifies.
    _name = 'asterisk_calls.user_notification'
    _description = 'User Notifications'
    _log_access = False
    MAX_AGE_SECONDS = 10

    key = fields.Char(required=True, index=True)
    created = fields.Datetime(required=True)

    _sql_constraints = [
        ('key_uniq', 'unique (key)', _('The key must be unique !')),
    ]


    @api.model
    def get(self, key, skip_unlink=False):
        now = datetime.now()
        # Remove expired keys
        if not skip_unlink:
            all_keys = self.sudo().search([]).filtered(lambda rec: (
                now - fields.Datetime.from_string(
                    rec.created)).total_seconds() > self.MAX_AGE_SECONDS)
            if all_keys:
                all_keys.unlink()
                self.invalidate_cache()
        # Now search for key
        return bool(self.sudo().search_count([('key', '=', key)]))


    @api.model
    def put(self, key):
        if not self.get(key, skip_unlink=True):
            self.sudo().create({'key': key, 'created': fields.Datetime.now()})
        self.invalidate_cache()
