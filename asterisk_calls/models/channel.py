from datetime import datetime, timedelta
import json
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

logger = logging.getLogger(__name__)


class Channel(models.Model):
    _name = 'asterisk_calls.channel'
    _rec_name = 'channel'
    _description = 'Active Call'

    partner = fields.Many2one('res.partner', ondelete='set null')
    src_user = fields.Many2one('res.users', string=_('From'), ondelete='set null')
    dst_user = fields.Many2one('res.users', string=_('To'), ondelete='set null')
    is_muted = fields.Boolean(string='Muted')
    callerid = fields.Char(compute='_get_callerid', string=_('Caller ID'))
    connected_line = fields.Char(compute='_get_connected_line')
    duration = fields.Char(compute='_get_duration')
    # Asterisk fields
    channel = fields.Char(index=True)
    channel_short = fields.Char(compute='_get_channel_short',
                                string=_('Channel'))
    uniqueid = fields.Char(size=150, index=True)
    linkedid = fields.Char(size=150, index=True)
    context = fields.Char(size=80)
    connected_line_num = fields.Char(size=80)
    connected_line_name = fields.Char(size=80)
    state = fields.Char(size=80)
    state_desc = fields.Char(size=256, string=_('State'))
    exten = fields.Char(size=32)
    callerid_num = fields.Char(size=32)
    callerid_name = fields.Char(size=32)
    system_name = fields.Char(size=32)
    accountcode = fields.Char(size=80)
    priority = fields.Char(size=4)
    timestamp = fields.Char(size=20)
    app = fields.Char(size=32, string='Application')
    app_data = fields.Char(size=512, string='Application Data')
    language = fields.Char(sise=2)
    event = fields.Char(size=64)


    @api.multi
    def _get_callerid(self):
        for rec in self:
            if rec.callerid_num and 'unknown' not in rec.callerid_num and \
                    'unknown' not in rec.callerid_name:
                rec.callerid = u'{} <{}>'.format(rec.callerid_name,
                                                 rec.callerid_num)
            elif rec.callerid_num and 'unknown' in rec.callerid_name and \
                    'unknown' not in rec.callerid_num:
                rec.callerid = '<{}>'.format(rec.callerid_num)
            else:
                rec.callerid = ''

    @api.multi
    def _get_channel_short(self):
        for rec in self:
            rec.channel_short = '-'.join(rec.channel.split('-')[:-1])


    @api.multi
    def _get_connected_line(self):
        for rec in self:

            if rec.connected_line_num and 'unknown' \
                    not in rec.connected_line_num and \
                    'unknown' not in rec.connected_line_name:
                rec.connected_line = u'{} <{}>'.format(rec.connected_line_name,
                                                       rec.connected_line_num)
            elif rec.connected_line_num and 'unknown' in \
                    rec.connected_line_name and \
                    'unknown' not in rec.connected_line_num:
                rec.connected_line = '<{}>'.format(rec.connected_line_num)
            else:
                rec.connected_line = ''


    @api.multi
    def _get_duration(self):
        for rec in self:
            if isinstance(rec.create_date, datetime):
                create_date = rec.create_date
            else:
                create_date = datetime.strptime(rec.create_date,
                                                '%Y-%m-%d %H:%M:%S')
            rec.duration = str(datetime.now() - create_date).split('.')[0]


    @api.model
    def update_channel_values(self, original_values):
        """
        We have 3 cases:
        1) User calls partner: match src user by callerid number.
        2) User calls user: match both users by callerid numbers.
        3) Partne, queue, ring groups call user: match by dst exten or channel
        """
        values = {}
        # Find source user by caller id
        channel_short = '-'.join(original_values.get(
                                                'channel').split('-')[:-1])
        linkedid = original_values.get('linkedid')
        uniqueid = original_values.get('uniqueid')
        callerid_num = original_values.get('callerid_num')
        exten = original_values.get('exten')
        connected_line_num = original_values.get('connected_line_num')
        ast_src_user_id = ast_dst_user_id = None
        # First let deal with direct calls 100% reliable when uniqueid=linkedid
        if linkedid == uniqueid:
            ast_src_user_by_exten = self.env[
                'asterisk_calls.user'].get_res_user_id_by_extension(
                                                                callerid_num)
            ast_src_user_by_channel = self.env['asterisk_calls.user'
                                ].get_res_user_id_by_channel(channel_short)
            if ast_src_user_by_exten == ast_src_user_by_channel:
                # Same user, so it is 100% outgoing calls
                ast_src_user_id = ast_src_user_by_exten

            # Now match dst user by exten and channel
            ast_dst_user_by_exten = self.env[
                'asterisk_calls.user'].get_res_user_id_by_extension(exten)
            ast_dst_user_by_channel = self.env['asterisk_calls.user'
                                ].get_res_user_id_by_channel(channel_short)
            if ast_dst_user_by_exten == ast_dst_user_by_channel:
                # Same user, so it is 100% outgoing calls
                ast_dst_user_id = ast_dst_user_by_exten

            # Now check if src user calls dst user
            if ast_src_user_id and not ast_dst_user_id:
                # First check if the call is connected
                ast_dst_user_id = self.env['asterisk_calls.user'
                            ].get_res_user_id_by_extension(connected_line_num)
                if not ast_dst_user_id:
                    ast_dst_user_id = self.env['asterisk_calls.user'
                            ].get_res_user_id_by_extension(exten)

            # Now check if dst user has src user set
            if ast_dst_user_id and not ast_src_user_id:
                # First check if the call is connected
                ast_src_user_id = self.env['asterisk_calls.user'
                            ].get_res_user_id_by_extension(connected_line_num)
                if not ast_src_user_id:
                    ast_src_user_id = self.env['asterisk_calls.user'
                            ].get_res_user_id_by_extension(exten)

            # if not dst or src users are found before this moment, try to find user by connected line.
            if not ast_dst_user_id and not ast_src_user_id:
                ast_dst_user_id = self.env['asterisk_calls.user'
                            ].get_res_user_id_by_extension(connected_line_num)

            # Update channel values
            if ast_dst_user_id:
                values['dst_user'] = ast_dst_user_id
            if ast_src_user_id:
                values['src_user'] = ast_src_user_id

            # Now update called partner
            if ast_src_user_id:
                # First get partner by number dialed
                dst_partner_info = self.env['res.partner'
                                            ].get_partner_by_number(exten)
                if not dst_partner_info['id']:
                    dst_partner_info = self.env['res.partner'
                                    ].get_partner_by_number(connected_line_num)
                if dst_partner_info['id']:
                    # Partner found
                    values['partner'] = dst_partner_info['id']

            # Now update calling partner
            else:
                # First get partner by number dialed
                src_partner_info = self.env['res.partner'
                                        ].get_partner_by_number(callerid_num)
                if not src_partner_info['id']:
                    src_partner_info = self.env['res.partner'
                                    ].get_partner_by_number(connected_line_num)
                if src_partner_info['id']:
                    # Partner found
                    values['partner'] = src_partner_info['id']
            # Finished with matching

        # uniqueid != linkedit that means new channel is spawned.
        else:
            # Let take the linked channel and take from it 100% reliable values
            linked_channels = self.search([('uniqueid', '=', linkedid)])
            # Check that taken channel is not also spawned, we can trust only originate channels.
            for chan in linked_channels:
                if chan.uniqueid == chan.linkedid:
                    # We got original channel
                    if chan.src_user:
                        logger.debug('SETTING SRC USER FROM LINKED CHANNEL')
                        values['src_user'] = chan.src_user.id
                    if chan.dst_user:
                        logger.debug('SETTING DST USER FROM LINKED CHANNEL')
                        values['dst_user'] = chan.dst_user.id
                    if chan.partner:
                        logger.debug('SETTING PARTNER FROM LINKED CHANNEL')
                        values['partner'] = chan.partner.id
                    break
            else:
                logger.debug('ORIGINAL CHANNEL FROM LINKED CHANNELS NOT FOUND')

            # If we still don't have dst_user (queue call) let check both channel and callerid
            if not values.get('dst_user'):
                dst_user_by_clid = self.env['asterisk_calls.user'
                                ].get_res_user_id_by_extension(callerid_num)
                dst_user_by_channel = self.env['asterisk_calls.user'
                                ].get_res_user_id_by_channel(channel_short)
                if dst_user_by_channel == dst_user_by_clid:
                    # Bingo, 100% it is a user's channel is called
                    values['dst_user'] = dst_user_by_clid
                elif dst_user_by_channel:
                    # Finally we risk to assign dst user by channel ;-)
                    values['dst_user'] = dst_user_by_channel

        # Finally we check if this is a pure inter user call
        if ast_src_user_id and ast_dst_user_id and not values.get('partner'):
            values['partner'] = self.env['res.users'].sudo().browse(
                                                ast_src_user_id).partner_id.id
        # Return changed values
        return values


    @api.model
    def create(self, vals):
        # Update channel dst / src users, partner
        vals.update(self.update_channel_values(vals))
        chan = super(Channel, self).create(vals)
        # Check if we need to set caller id name via AMI
        if self.env['asterisk_calls.util'].sudo().get_asterisk_calls_param(
                                            'set_caller_name_type') == 'ami':
            if chan.partner:
                self.env['remote_agent.agent'].send_agent('asterisk_calls', json.dumps({
                    'message': 'setvar',
                    'Channel': chan.channel,
                    'Variable': 'CALLERID(name)',
                    'Value': chan.partner.name
                }))
        chan.reload_channels()
        return chan


    @api.multi
    def reload_channels(self):
        self.ensure_one()
        auto_reload = self.env['asterisk_calls.util'].sudo(
                            ).get_asterisk_calls_param('auto_reload_channels')
        self.env['bus.bus'].sendone('asterisk_calls_channels', json.dumps({
                                                'event': 'update_channel',
                                                'dst': self.exten,
                                                'channel': self.channel_short,
                                                'partner_id': self.partner.id,
                                                'auto_reload': auto_reload}))

    @api.model
    def update_channel_state(self, values, channel=None):
        return self.sudo()._update_channel_state(values, channel=channel)


    @api.model
    def _update_channel_state(self, values, channel=None):
        # RPC call from Agent
        # logger.info(json.dumps(values, indent=2))
        if type(values) == list:
            values = values[0]
        if not channel:
            channel = self.env['asterisk_calls.channel'].search([
                ('uniqueid', '=', values.get('uniqueid'))], limit=1)
        if not channel:
            logger.debug('No channel {} found for state update.'.format(
                                                    values.get('uniqueid')))
            return False
        # If exten or caller id or connect line is changed, update values
        if channel.exten != values.get('exten'):
            values.update(self.update_channel_values(values))
        elif channel.callerid_num != values.get('callerid_num'):
            values.update(self.update_channel_values(values))
        elif channel.connected_line_num != values.get('connected_line_num'):
            values.update(self.update_channel_values(values))
        # Update channel
        channel.write(values)
        # Notify users
        if channel.dst_user and channel.partner.id and \
                channel.dst_user.asterisk_user.call_popup_is_enabled and \
                channel.dst_user.partner_id.id != channel.partner.id:
            key = 'dst_user_{}:partner_{}'.format(
                                    channel.dst_user.id, channel.partner.id)
            if not self.env['asterisk_calls.user_notification'].get(key):
                is_sticky = channel.dst_user.asterisk_user.call_popup_is_sticky
                self.env['asterisk_calls.user_notification'].put(key)
                # Notify about partner call
                self.env['bus.bus'].sendone(
                    'remote_agent_notification_{}'.format(channel.dst_user.id),
                    {'title': _('Incoming call'),
                     'message': channel.partner.name,
                     'sticky': is_sticky})
        channel.reload_channels()
        return True


    @api.model
    def hangup_channel(self, values):
        # RPC call from Asterisk to remove channel from Odoo
        if type(values) == list:
            values = values[0]
        uniqueid = values.get('Uniqueid')
        channel = values.get('Channel')
        found = self.env['asterisk_calls.channel'].search(
                                                [('uniqueid', '=', uniqueid)])
        if found:
            logger.debug('Found channel {}'.format(channel))
            found.unlink()
        else:
            logger.info('Channel {} not found for hangup.'.format(uniqueid))
        auto_reload = self.env['asterisk_calls.util'].sudo().get_asterisk_calls_param(
                                                'auto_reload_channels')
        self.env['bus.bus'].sendone('asterisk_calls_channels', json.dumps({
                                        'event': 'hangup_channel',
                                        'auto_reload': auto_reload}))
        return True


    @api.multi
    def pickup(self):
        self.ensure_one()
        if not self.env.user.asterisk_channel:
            raise ValidationError(_('Extension not configured!'))
        self.env['remote_agent.agent'].send_agent('asterisk_calls', json.dumps({
            'message': 'redirect',
            'uid': self.env.user.id,
            'channel': self.channel,
            'context': self.env['asterisk_calls.util'].sudo(
                            ).get_asterisk_calls_param('originate_context'),
            'priority': '1',
            'exten': self.env.user.asterisk_extension
        }))


    @api.multi
    def listen(self):
        self.ensure_one()
        if not self.env.user.asterisk_channel:
            raise ValidationError(_('Extension not configured!'))
        self.env['remote_agent.agent'].send_agent('asterisk_calls', json.dumps({
            'message': 'spy',
            'uid': self.env.user.id,
            'spy_channel': self.channel,
            'user_channel': self.env.user.asterisk_channel,
            'spy_exten': self.exten,
            'spy_options': 'q',
            'sip_alert_info': self.env.user.asterisk_user.sip_alert_info,
        }))


    @api.multi
    def whisper(self):
        self.ensure_one()
        # Check that we are going to whisper on user channel not partner's :-)
        if not self.env.user.asterisk_channel:
            raise ValidationError(_('Extension not configured!'))
        self.env['remote_agent.agent'].send_agent('asterisk_calls', json.dumps({
            'message': 'spy',
            'uid': self.env.user.id,
            'spy_channel': self.channel,
            'user_channel': self.env.user.asterisk_channel,
            'spy_exten': self.exten,
            'spy_options': 'qw',
            'sip_alert_info': self.env.user.asterisk_user.sip_alert_info,
        }))


    @api.multi
    def barge(self):
        self.ensure_one()
        if not self.env.user.asterisk_channel:
            raise ValidationError(_('Extension not configured!'))
        self.env['remote_agent.agent'].send_agent('asterisk_calls', json.dumps({
            'message': 'spy',
            'uid': self.env.user.id,
            'spy_channel': self.channel,
            'user_channel': self.env.user.asterisk_channel,
            'spy_exten': self.exten,
            'spy_options': 'qb',
            'sip_alert_info': self.env.user.asterisk_user.sip_alert_info,
        }))


    @api.multi
    def mute(self):
        self.ensure_one()
        self.is_muted = True
        self.env['remote_agent.agent'].send_agent('asterisk_calls', json.dumps({
            'message': 'mute_audio',
            'uid': self.env.user.id,
            'channel': self.channel,
            'direction': 'out',
            'state': 'off',
        }))


    @api.multi
    def unmute(self):
        self.ensure_one()
        self.is_muted = False
        self.env['remote_agent.agent'].send_agent('asterisk_calls', json.dumps({
            'message': 'mute_audio',
            'uid': self.env.user.id,
            'channel': self.channel,
            'direction': 'out',
            'state': 'on',
        }))


    @api.multi
    def hangup_button(self):
        self.ensure_one()
        self.env['remote_agent.agent'].send_agent('asterisk_calls', json.dumps({
                                        'message': 'hangup_request',
                                        'channel': self.channel,
                                        'uid': self.env.user.id,
                                        }), silent=True)
        self.unlink()
        return {
            'type': 'ir.actions.act_window',
            'target': 'main',
            'res_model': 'asterisk_calls.channel',
            'name': _('Active Calls'),
            'view_mode': 'tree,form',
            'view_type': 'form'
        }

    @api.model
    def cleanup(self, hours=24):
        # Remove calls created previous day
        yesterday = (datetime.now() - timedelta(
                                hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        self.env['asterisk_calls.channel'].search(
                [('create_date', '<', yesterday)]).unlink()
