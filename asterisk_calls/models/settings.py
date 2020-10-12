import json
import logging
from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError

logger = logging.getLogger(__name__)


class CallsSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ASTERISK_CALLS_PARAMS = [
        ('originate_context', 'test-users'),
        ('originate_timeout', '30'),
        ('calls_keep_days', '90'),
        ('auto_reload_channels', 'True'),
        ('callback_queue', 'sales'),
        ('queue_exten', '500'),
        ('callback_context', 'test-callback'),
        ('callback_daily_attempts', '10'),
        ('callback_interval_minutes', '2'),
        ('callback_days', '2'),
        ('callback_order', 'queue'),
        ('recaptcha_enabled', 'False'),
        ('recaptcha_key', ''),
        ('recaptcha_secret', ''),
        ('set_caller_name_type', 'dialplan'),
        ('asterisk_ip_addresses', ''),
        ('originate_strip_plus', 'True'),
        ('recording_storage', 'db'),
    ]

    originate_context = fields.Char()
    originate_timeout = fields.Char()
    calls_keep_days = fields.Char(
                        string=_('Keep days'),
                        help=_('Call older then set value will be removed'))
    auto_reload_channels = fields.Boolean(
                        help=_('Automatically refresh active channels view'))
    callback_interval_minutes = fields.Char(
                                        string=_('Call interval (minutes)'))
    callback_daily_attempts = fields.Char(string=_('Daily attempts'))
    callback_days = fields.Char()
    callback_queue = fields.Char(
                            help=_('Asterisk queue name for callback calls'))
    callback_order = fields.Selection(selection=[
        ('queue', 'Queue first'), ('customer', 'Customer first')], help=_(
        'Place the call to queue and then try to connect to customer '
        'or place the call to customer and then put it in the queue.'))
    queue_exten = fields.Char(
                            help=_('Asterisk exten for callback calls'))
    callback_context = fields.Char(string=_('Originate context'),
                            help=_('Asterisk context for callback calls'))
    callback_number_placeholder = fields.Char(
                        help=_('Web form placeholder for the phone field'))
    recaptcha_key = fields.Char(string='reCAPTCHA key',
        help=_('Get your key here: https://www.google.com/recaptcha/admin'))
    recaptcha_secret = fields.Char(string='reCAPTCHA secret',
        help=_('Get your secret here: https://www.google.com/recaptcha/admin'))
    recaptcha_enabled = fields.Boolean(string='reCAPTCHA enabled',
                                    help=_('Enable Google ReCaptcha service'))
    set_caller_name_type = fields.Selection([
                                    ('ami', 'AMI (Wait)'),
                                    ('dialplan', 'Dialplan (CURL)')])
    asterisk_ip_addresses = fields.Char(
                        string=_('Asterisk IP address(es)'),
                        help=_('Comma separated list of allowed IP address, '
                               'leave empty to allow all addresses.'))
    originate_strip_plus = fields.Boolean()
    recording_storage = fields.Selection([('db', _('Database')),
                                          ('filestore', _('Files'))])


    @api.multi
    def set_values(self):
        super(CallsSettings, self).set_values()
        if not (self.env.user.id == SUPERUSER_ID or
                self.env.user.has_group(
                                'asterisk_calls.group_asterisk_calls_admin')):
            # Do not save values!
            return
        for field_name, default_value in self.ASTERISK_CALLS_PARAMS:
            value = getattr(self, field_name)
            self.env['ir.config_parameter'].set_param(
                'asterisk_calls.' + field_name, str(value))

    @api.model
    def get_values(self):
        res = super(CallsSettings, self).get_values()
        if not (self.env.user.id == SUPERUSER_ID or
                self.env.user.has_group(
                                'asterisk_calls.group_asterisk_calls_admin')):
            # Do not return values!
            return res
        for field_name, default_value in self.ASTERISK_CALLS_PARAMS:
            res[field_name] = self.env[
                'ir.config_parameter'].get_param(
                    'asterisk_calls.' + field_name, default_value)
            # Dirty but quick :-)
            if field_name == 'auto_reload_channels':
                res[field_name] = True if res[field_name] == 'True' else False
            elif field_name == 'recaptcha_enabled':
                res[field_name] = True if res[field_name] == 'True' else False
            elif field_name == 'originate_strip_plus':
                res[field_name] = True if res[field_name] == 'True' else False
        return res


    @api.multi
    def restart_asterisk_agent(self):
        if not self.env.user.has_group(
                                'asterisk_calls.group_asterisk_calls_admin'):
            raise ValidationError(
                                _('You must be Calls administrator to do it!'))
        agent = self.env['remote_agent.agent']._get_agent_by_uid(
                                                            'asterisk_calls')
        agent.restart_agent()


    @api.multi
    def sync_recording_storage(self):
        count = 0
        try:
            for rec in self.env['asterisk_calls.call'].sudo().search(
                                    [('recording_filename', '!=', False)]):
                if self.recording_storage == 'db' and not rec.recording_data:
                    rec.recording_data = rec.recording_attachment
                    rec.recording_attachment = False
                    count += 1
                elif self.recording_storage == 'filestore' and not rec.recording_attachment:
                    rec.recording_attachment = rec.recording_data
                    rec.recording_data = False
                    count += 1
                self.env.cr.commit()
        except Exception as e:
            # Remove attachments
            logger.info('Sync recordings error: %s', str(e))
        finally:
            logger.info('Moved %s recordings', count)
            self.env['ir.attachment']._file_gc()

