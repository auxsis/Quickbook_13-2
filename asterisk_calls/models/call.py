from datetime import datetime, timedelta
import logging
import pytz
from odoo import models, fields, api, _, release
from odoo.exceptions import ValidationError

logger = logging.getLogger(__name__)


DISPOSITION_TYPES = (
    ('NO ANSWER', 'No answer'),
    ('FAILED', 'Failed'),
    ('BUSY', 'Busy'),
    ('ANSWERED', 'Answered'),
    ('CONGESTION', 'Congestion'),
)


class Call(models.Model):
    _name = 'asterisk_calls.call'
    _inherit = ['mail.thread']
    _description = 'Call Log'
    _order = 'id desc'
    _rec_name = 'id'

    tags = fields.Many2many('asterisk_calls.tag',
                            relation='asterisk_calls_call_tag',
                            column1='tag', column2='call')
    tags_list = fields.Char(compute=lambda self: self._get_tags_list(),
                            string=_('Tags'))
    partner = fields.Many2one('res.partner', ondelete='set null',
                              track_visibility='onchange')
    partner_company = fields.Many2one(related='partner.parent_id')
    src_user = fields.Many2one('res.users', ondelete='set null', readonly=True,
                               string=_('From User'))
    dst_user = fields.Many2one('res.users', ondelete='set null', readonly=True,
                               string=_('To User'))
    notes = fields.Text(track_visibility='onchange')
    notes_short = fields.Char(compute='_get_notes_short', string=_('Notes'))
    in_library = fields.Boolean()
    is_private = fields.Boolean(string=_('Private'),
                                help=_('Only call party will have access.'))
    callback = fields.Many2one(comodel_name='asterisk_calls.callback',
                               ondelete='set null', readonly=True)
    channel_short = fields.Char(compute='_get_channel_short', string=_('Channel'))
    dstchannel_short = fields.Char(compute='_get_dstchannel_short', string=_('Dest channel'))
    # Recordings
    recording_filename = fields.Char(readonly=True, index=True)
    recording_data = fields.Binary(readonly=True, string=_('Download'))
    recording_attachment = fields.Binary(attachment=True, string=_('Download'))
    recording_widget = fields.Char(compute='_get_recording_widget')
    recording_icon = fields.Char(compute='_get_recording_icon')
    # Asterisk fields
    accountcode = fields.Char(size=20, string='Account code', index=True,
                              readonly=True)
    src = fields.Char(size=80, string='Source', index=True, readonly=True)
    dst = fields.Char(size=80, string='Destination', index=True, readonly=True)
    dcontext = fields.Char(size=80, string='Destination context', readonly=True)
    clid = fields.Char(size=80, string='Caller ID', index=True, readonly=True)
    channel = fields.Char(size=80, string='Channel', index=True, readonly=True)
    dstchannel = fields.Char(size=80, string='Destination channel', index=True,
                             readonly=True)
    lastapp = fields.Char(size=80, string='Last app', readonly=True)
    lastdata = fields.Char(size=80, string='Last data', readonly=True)
    started = fields.Datetime(index=True, readonly=True)
    answered = fields.Datetime(index=True, readonly=True)
    ended = fields.Datetime(index=True, readonly=True)
    duration = fields.Integer(string='Call Duration', index=True, readonly=True)
    duration_human = fields.Char(string=_('Call Duration'),
                            compute=lambda self: self._compute_duration_human())
    billsec = fields.Integer(string='Talk Time', index=True, readonly=True)
    billsec_human = fields.Char(string=_('Talk Time'),
                            compute=lambda self: self._compute_billsec_human())
    disposition = fields.Char(size=45, string='Disposition', index=True, readonly=True)
    amaflags = fields.Char(size=20, string='AMA flags', readonly=True)
    userfield = fields.Char(size=255, string='Userfield', readonly=True)
    uniqueid = fields.Char(size=150, string='Unique ID', index=True, readonly=True)
    peeraccount = fields.Char(size=80, string='Peer account', index=True, readonly=True)
    linkedid = fields.Char(size=150, string='Linked ID', readonly=True)
    sequence = fields.Integer(string='Sequence', readonly=True)
    # QoS
    # Our side
    ssrc = fields.Char(string=_('Our Synchronization source'), readonly=True)
    rxcount = fields.Integer(string='Received Packets', readonly=True)
    rxjitter = fields.Float(string='Our Jitter', readonly=True)
    # Their side
    themssrc = fields.Char(string=_('Their Synchronization source'), readonly=True)
    lp = fields.Integer(string=_('Local Lost Packets'), readonly=True)
    rlp = fields.Integer(string=_('Remote Lost Packets'), readonly=True)    
    txjitter = fields.Float(string='Their Jitter', readonly=True)
    txcount = fields.Integer(string='Transmitted Packets', readonly=True)
    rtt = fields.Float(string=_('Round Trip Time'), readonly=True)
    is_qos_bad = fields.Html(compute='_is_qos_bad', string='QoS')

    @api.multi
    def write(self, vals):
        for rec in self:
            if not rec.partner and vals.get('partner'):
                # Let set partner phone
                super(Call, self).write(vals)
                # Guess number
                if rec.dst and rec.src_user:
                    number = rec.dst
                elif rec.src and rec.dst_user:
                    number = rec.src
                else:
                    # Cannot guess number
                    continue
                # Check if number is already present
                # Odoo 10
                if release.version[:2] == '10':
                    if number in [rec.partner.phone, rec.partner.mobile,
                                  rec.partner.fax]:
                        continue
                # For Odoo 11 & 12
                elif number in [rec.partner.phone, rec.partner.mobile]:
                        continue
                # Fill partner phones
                if not rec.partner.phone:
                    rec.partner.phone = number
                elif not rec.partner.mobile:
                    rec.partner.mobile = number
                elif release.version[:2] == '10' and not rec.partner.fax:
                    rec.partner.fax = number
                else:
                    # No free slots for new number, so do nothing
                    continue
            else:
                # Just update partner
                super(Call, self).write(vals)
        return True


    @api.multi
    def toggle_library(self):
        self.ensure_one()
        if not (self.env.user.has_group('asterisk_calls.group_asterisk_calls_admin')
            or self.env.user == self.dst_user or self.env.user == self.src_user):
                raise ValidationError(
                    _('You must be admin or one part of the call to change it!'))
        self.in_library = not self.in_library


    @api.constrains('in_library', 'is_private')
    def check_lib_conditions(self):
        self.ensure_one()
        if self.in_library and self.is_private:
            raise ValidationError(_('You cannot add priviate call to the Library!'))


    @api.multi
    def _get_tags_list(self):
        for rec in self:
            rec.tags_list = u', '.join([k.name for k in rec.tags])


    @api.multi
    def _get_channel_short(self):
        for rec in self:
            rec.channel_short = '-'.join(rec.channel.split('-')[:-1])


    @api.multi
    def _get_dstchannel_short(self):
        for rec in self:
            rec.dstchannel_short = '-'.join(rec.dstchannel.split('-')[:-1])


    @api.multi
    def _get_recording_icon(self):
        for rec in self:
            if rec.recording_filename:
                rec.recording_icon = '<span class="fa fa-file-sound-o"/>'
            else:
                rec.recording_icon = ''


    @api.multi
    def _get_notes_short(self):
        for rec in self:
            l = 40
            if not rec.notes:
                rec.notes_short = ''
            elif len(rec.notes) <= l:
                rec.notes_short = rec.notes
            else:
                rec.notes_short = u'{}...'.format(rec.notes[:l])


    @api.multi
    def _compute_billsec_human(self):
        for rec in self:
            rec.billsec_human = str(timedelta(seconds=rec.billsec))


    @api.multi
    def _compute_duration_human(self):
        for rec in self:
            rec.duration_human = str(timedelta(seconds=rec.duration))


    @api.multi
    def open_form(self):
        self.ensure_one()
        return {
            'res_model': 'asterisk_calls.call',
            'res_id': self.id,
            'name': _('Call Log'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
        }



    @api.multi
    def open_partner_form(self):
        self.ensure_one()
        return {
            'res_model': 'res.partner',
            'res_id': self.partner.id,
            'name': _('Partner'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'context': {
                'default_phone': self.dst if self.src_user else self.src,
                'create_call_partner': self.id,
            },
        }

    @api.model
    def parse_user_field(self, userfield):
        res = {}
        try:
            userfields = userfield.split(';')
            for userfield in userfields:
                var_val = userfield.split(':')
                if len(var_val) == 2:
                    var, val = var_val
                    if var == 'ORIGINATED_MODEL':
                        model, obj_id = val.split('-')
                        if model == 'res.partner':
                            res['partner_id'] = int(obj_id)
                    elif var == 'ORIGINATED_UID':
                        res['src_user_id'] = val
        except Exception:
            logger.exception('parse_user_field error:')
        finally:
            return res

    @api.model
    def update_cdr_values(self, original_vals):
        vals = {}
        src = original_vals.get('src')
        dst = original_vals.get('dst')
        dst_channel_short = '-'.join(original_vals.get(
            'dstchannel', '').split('-')[:-1])
        src_channel_short = '-'.join(original_vals.get(
            'channel', '').split('-')[:-1])
        # Get src user from userfield
        ast_src_user_id = self.parse_user_field(
            original_vals.get('userfield', {})).get('src_user_id')
        if ast_src_user_id:
            vals['src_user'] = ast_src_user_id
        else:
            # Get src user by channel
            ast_src_user_id = self.env[
                'asterisk_calls.user'].get_res_user_id_by_channel(
                src_channel_short)
            if not ast_src_user_id:
                # Try to get src user by extension
                ast_src_user_id = self.env[
                    'asterisk_calls.user'].get_res_user_id_by_extension(src)
            if ast_src_user_id:
                vals['src_user'] = ast_src_user_id
        # Get dst user by channel
        ast_dst_user_id = self.env[
            'asterisk_calls.user'].get_res_user_id_by_channel(
            dst_channel_short)
        if not ast_dst_user_id:
            ast_dst_user_id = self.env[
                'asterisk_calls.user'].get_res_user_id_by_extension(dst)
        if ast_dst_user_id:
            vals['dst_user'] = ast_dst_user_id
        # Now get partner from context
        if self.env.context.get('originate_model') and \
                self.env.context['originate_model'] == 'res.partner' and \
                self.env.context.get('originate_res_id'):
            logger.debug('FOUND PARTNER %s FROM CONTEXT',
                         self.env.context.get('originate_res_id'))
            vals['partner'] = self.env.context['originate_res_id']
        elif original_vals.get('userfield'):
            partner_id = self.parse_user_field(
                original_vals['userfield']).get('partner_id')
            if partner_id:
                vals['partner'] = partner_id
        elif ast_src_user_id:
            # Get partner for destination as call is from user
            partner_info = self.env[
                'res.partner'].get_partner_by_number(dst)
            vals['partner'] = partner_info['id']
        elif ast_dst_user_id:
            # Get partner for source as call is to user
            partner_info = self.env['res.partner'].get_partner_by_number(src)
            vals['partner'] = partner_info['id']
        else:
            # No users in the call - assume this is incoming call
            partner_info = self.env['res.partner'].get_partner_by_number(src)
            vals['partner'] = partner_info['id']
        return vals

    @api.model
    def create(self, vals):
        # Update timezone
        if self.env.user.tz:
            try:
                server_tz = pytz.timezone(self.env.user.tz)
                convert_fields = ['started', 'answered', 'ended']
                for field in convert_fields:
                    if field in vals and vals[field]:
                        dt_no_tz = fields.Datetime.from_string(vals[field])
                        dt_server_tz = server_tz.localize(dt_no_tz,
                                                          is_dst=None)
                        dt_utc = dt_server_tz.astimezone(pytz.utc)
                        vals[field] = fields.Datetime.to_string(dt_utc)
            except Exception:
                logger.exception('Error adjusting timezone for Call')
        # Update Call values
        try:
            vals.update(self.update_cdr_values(vals))
        except Exception as e:
            logger.exception('Handle error in update_cdr_values')
        _call = super(Call, self).create(vals)
        call = _call.sudo(True)  # Multi company fix.
        # Subscribe users if any
        subscribe_list = [k.partner_id.id for k in [call.dst_user, call.src_user] if k]
        if subscribe_list:
            call.message_subscribe(partner_ids=subscribe_list)
        # Call notification
        try:
            if call.dst_user and call.disposition != 'ANSWERED':
                if call.dst_user.asterisk_user.missed_calls_notify:
                    call_from = call.src
                    if call.partner:
                        call_from = call.partner.name
                    elif call.src_user:
                        call_from = call.src_user.name
                    self.env['mail.message'].sudo(self.env.user.id).create({
                        'subject': _('Missed call notification'),
                        'body': _('You have a missed call from {}').format(
                                                                    call_from),
                        'model': 'asterisk_calls.call',
                        'res_id': call.id,
                        'message_type': 'notification',
                        'subtype_id': self.env[
                            'ir.model.data'].xmlid_to_res_id(
                                                    'mail.mt_comment'),
                        'partner_ids': [(4, call.dst_user.partner_id.id)],
                        'email_from': self.env.user.partner_id.email,
                        'needaction_partner_ids': [
                                        (4, call.dst_user.partner_id.id)],

                    })
        except Exception as e:
            logger.exception(e)
        finally:
            return call


    @api.model
    def delete_calls(self, days=None):
        if not days:
            days = self.env['asterisk_calls.util'].sudo(
                                ).get_asterisk_calls_param('calls_keep_days')
        expire_date = datetime.now() - timedelta(days=int(days))
        odoo_date = fields.Datetime.to_string(expire_date)
        expired_calls = self.env['asterisk_calls.call'].search([
                                            ('in_library', '=', False),
                                            ('started', '<', odoo_date)])
        logger.info('Expired {} calls'.format(len(expired_calls)))
        for call in expired_calls:
            try:
                call.unlink()
            except Exception as e:
                # Log exception and go ahead
                logger.exception(e)


    @api.multi
    def _get_recording_widget(self):
        recording_storage = self.env['asterisk_calls.util'].sudo(
                            ).get_asterisk_calls_param('recording_storage')
        if recording_storage == 'db':
            recording_source = 'recording_data'
        else:
            recording_source = 'recording_attachment'
        for rec in self:
            rec.recording_widget = '<audio id="sound_file" preload="auto" ' \
                    'controls="controls"> ' \
                    '<source src="/web/content?model=asterisk_calls.call&' \
                    'id={}&filename={}&field={}&' \
                    'filename_field=recording_filename&download=True" ' \
                    'type="audio/wav"/>'.format(rec.id, rec.recording_filename,
                                                recording_source)


    @api.multi
    def _is_qos_bad(self):
        for rec in self:
            rec.is_qos_bad = '<span class="fa fa-warning"/>' if (rec.lp > 2 or rec.rlp > 2) else False

    @api.model
    def update_qos(self, values):
        values = values[0]
        uniqueid = values.get('uniqueid')
        linkedid = values.get('linkedid')
        # TODO Probably we need to optimize db query on millions of records.
        cdrs = self.env['asterisk_calls.call'].search([
            ('started', '>', (datetime.now() - timedelta(seconds=120)).strftime(
                                                        '%Y-%m-%d %H:%M:%S')),
            ('uniqueid', '=', uniqueid),
            ('linkedid', '=', linkedid),
        ])
        if not cdrs:
            logger.info('Omitting QoS, CDR not found, uniqueid {}!'.format(
                uniqueid))
            return False
        else:
            logger.debug('Found CDR for QoS.')
            cdr = cdrs[0]
            cdr.write({
                'ssrc': values.get('ssrc'),
                'themssrc': values.get('themssrc'),
                'lp': int(values.get('lp', '0')),
                'rlp': int(values.get('rlp', '0')),
                'rxjitter': float(values.get('rxjitter', '0')),
                'txjitter': float(values.get('txjitter', '0')),
                'rxcount': int(values.get('rxcount', '0')),
                'txcount': int(values.get('txcount', '0')),
                'rtt': float(values.get('rtt', '0')),
            })
            # Notify QoS channel if QoS is bad
            if cdr.lp >= 0 or cdr.rlp >= 0:
                channel = self.sudo().env.ref('asterisk_calls.qos_channel')
                if channel:
                    fields = []
                    fields.append('UniqueID: {}'.format(cdr.uniqueid))
                    fields.append('lp: {}'.format(cdr.lp))
                    fields.append('rlp: {}'.format(cdr.rlp))
                    if cdr.partner:
                        fields.append('partner: {}'.format(cdr.partner.name))
                    if cdr.src_user:
                        fields.append('from: {}'.format(cdr.src_user.name))
                    if cdr.dst_user:
                        fields.append('to: {}'.format(cdr.dst_user.name))
                    channel[0].message_post(
                        body=', '.join(fields),
                        subject=_('Bad QoS'),
                        subtype='mail.mt_comment',
                        model='asterisk_calls.call',
                        res_id=cdr.id,
                    )
            return True


    @api.model
    def save_call_recording(self, values):
        values = values[0]
        call_id = values['uniqueid']
        file_data = values['data']
        logger.debug('save_call_recording for callid {}.'.format(call_id))
        rec = self.env['asterisk_calls.call'].search([('uniqueid', '=', call_id)],
                                                     limit=1)
        if not rec:
            logger.info(
                'save_call_recording - cdr not found by id {}.'.format(call_id))
            return True
        else:
            logger.debug('Found CDR for id {}.'.format(call_id))
            rec.recording_filename = '{}.wav'.format(call_id)
            if self.env['asterisk_calls.util'].get_asterisk_calls_param(
                                                'recording_storage') == 'db':
                rec.recording_data = file_data
            else:
                rec.recording_attachment = file_data
            return True
