import json
import logging
from odoo import models, fields, api, tools, _
from odoo.exceptions import ValidationError, UserError

try:
    from odoo.addons.phone_validation.tools import phone_validation
    import phonenumbers
    PHONE_VALIDATION = True
except ImportError:
    PHONE_VALIDATION = False


logger = logging.getLogger(__name__)


class ResUser(models.Model):
    _name = 'res.users'
    _inherit = 'res.users'

    asterisk_user = fields.One2many('asterisk_calls.user', inverse_name='user')
    asterisk_extension = fields.Char(related='asterisk_user.extension',
                                     readonly=True)
    asterisk_channel = fields.Char(related='asterisk_user.channel',
                                   readonly=True)
    asterisk_open_partner_form = fields.Boolean(
                                    related='asterisk_user.open_partner_form')


    @api.model
    def create(self, vals):
        res = super(ResUser, self).create(vals)
        # Clear users cache if record was created
        if res:
            self.pool.clear_caches()
        return res


    @api.multi
    def unlink(self):
        res = super(ResUser, self).unlink()
        if res:
            self.pool.clear_caches()
        return res

class AsteriskUser(models.Model):
    _name = 'asterisk_calls.user'
    _order = 'extension'
    _description = _('Asterisk User')

    user = fields.Many2one('res.users', required=True,
                           ondelete='cascade',
                           domain=[('share', '=', False)])
    partner = fields.Many2one(related='user.partner_id', readonly=True)
    name = fields.Char(compute='_get_name')
    extension = fields.Char(required=True)
    channel = fields.Char(required=True)
    sip_alert_info = fields.Char(
                            string='SIP Alert-info',
                            default='Alert-Info: Auto Answer',
                            groups="asterisk_calls.group_asterisk_calls_admin")
    missed_calls_notify = fields.Boolean(
                                        help=_('Notify user on missed calls.'))
    open_partner_form = fields.Boolean(
                    help=_('Open partner form on incoming calls from partner'))
    call_popup_is_enabled = fields.Boolean(string=_('Call Popup'),
                                           default=True)
    call_popup_is_sticky = fields.Boolean(string=_('Sticky Messages'))
    is_own_record = fields.Boolean(compute='_is_own_record')
    is_asterisk_admin = fields.Boolean(compute='_is_asterisk_admin')


    _sql_constraints = [
        ('extension_uniq', 'unique(extension)', _('The extension must be unique !')),
        ('user_uniq', 'unique("user")', _('The user already has an extension!')),
    ]


    @api.model
    def create(self, vals):
        user = super(AsteriskUser, self).create(vals)
        asterisk_user_group = self.env.ref('asterisk_calls.group_asterisk_calls_user')
        if user.user not in asterisk_user_group.users:
            asterisk_user_group.sudo().users = [(4, user.user.id)]
        if user:
            self.pool.clear_caches()
        return user


    @api.multi
    def write(self, values):
        res = super(AsteriskUser, self).write(values)
        if res:
            self.pool.clear_caches()
        return res


    @api.multi
    def unlink(self):
        asterisk_user_group = self.env.ref('asterisk_calls.group_asterisk_calls_user')
        for rec in self:
            if rec.user in asterisk_user_group.users:
                asterisk_user_group.sudo().users = [(3, rec.user.id)]
        self.pool.clear_caches()
        return super(AsteriskUser, self).unlink()


    @api.multi
    def _get_name(self):
        for rec in self:
            rec.name = '"{}" <{}>'.format(rec.sudo().user.name, rec.extension)


    @api.model
    @tools.ormcache('exten')
    def get_res_user_id_by_extension(self, exten):
        astuser = self.env['asterisk_calls.user'].search([
                                                ('extension', '=', exten)],
                                                limit=1)
        return astuser.sudo().user.id


    @api.model
    @tools.ormcache('channel')
    def get_res_user_id_by_channel(self, channel):
        astuser = self.env['asterisk_calls.user'].search([
                                                ('channel', '=', channel)],
                                                limit=1)
        return astuser.sudo().user.id

    @api.multi
    def _is_own_record(self):
        # used in view to check is current user own the record
        for rec in self:
            rec.is_own_record = True if self.sudo().user.id == self.env.user.id else False


    @api.multi
    def _is_asterisk_admin(self):
        # used in view to check if user has asterisk admin group
        self.is_asterisk_admin = True if self.env.user.has_group(
                    'asterisk_calls.group_asterisk_calls_admin') else False


    @api.onchange('extension')
    def _set_channel(self):
        self.ensure_one()
        if self.extension:
            if self.channel and '/' in self.channel:
                chan_name = self.channel.split('/')[0]
                self.channel = '{}/{}'.format(chan_name, self.extension)
            else:
                self.channel = 'SIP/{}'.format(self.extension)


    @api.multi
    def call_user(self):
        self.ensure_one()
        self.originate_call(self.extension)


    def get_alert_info_sip_header(self):
        alert_info = self.env.user.asterisk_user.sip_alert_info
        header = None
        if alert_info:
            try:
                var_name = alert_info.split(':')[0]
                var_val = ''.join(alert_info.split(':')[1:])
            except IndexError:
                raise ValidationError(_('Incorrect alert info header format!'))
            # Make the right header for SIP and PJSIP
            if 'PJSIP' in self.env.user.asterisk_user.channel.upper():
                header = 'PJSIP_HEADER(add,{})={}'.format(var_name, var_val)
            elif 'SIP' in self.env.user.asterisk_user.channel.upper():
                header = 'SIPADDHEADER="{}:{}"'.format(var_name, var_val)
        return header


    @api.model
    def originate_call(self, number, model_name=None, res_id=None,
                       agent_uid='asterisk_calls'):
        if not number:
            raise ValidationError(_('Phone number not set!'))
        if not self.env.user.asterisk_user:
            raise ValidationError(_("Asterisk extension is not configured!"))
        # Format number for model if present
        if model_name and res_id:
            logger.debug('FORMAT NUMBER FOR MODEL %s', model_name)
            if '_format_number' in self.env[model_name]:
                number = self.env[model_name]._format_number(
                    number, res_id)
                logger.debug('MODEL FORMATTED NUMBER: {}'.format(number))
        # Remove + is present
        if self.env['asterisk_calls.util'].sudo().get_asterisk_calls_param(
                'originate_strip_plus'):
            if number[0] == '+':
                logger.debug('ORIGINATE STRIP PLUS SET, REMOVING +')
                number = number[1:]
        # Strip spaces if present
        number = number.replace(' ', '')
        number = number.replace('(', '')
        number = number.replace(')', '')
        number = number.replace('-', '')
        data = {
            'message': 'originate',
            'Channel': self.env.user.asterisk_channel,
            'Exten': number,
            'CallerID': u'"{}" <{}>'.format(self.env.user.name,
                                            self.env.user.asterisk_extension),
            'uid': self.env.user.id,
            'model': model_name,
            'res_id': res_id,
        }
        header = self.get_alert_info_sip_header()
        if header:
            data.update({'Variable': [header]})
        # Finally send all to agent
        self.env['remote_agent.agent'].send_agent(
            agent_uid, json.dumps(data))
