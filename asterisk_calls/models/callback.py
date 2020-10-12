from datetime import date, datetime, timedelta
import uuid
import json
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

logger = logging.getLogger(__name__)

class Callback(models.Model):
    _name = 'asterisk_calls.callback'
    _description = 'Callback Request'
    _order = 'id desc'
    _rec_name = 'id'


    uid = fields.Char(default=lambda self: uuid.uuid4().hex)
    name = fields.Char(compute='_get_name')
    subject = fields.Text()
    subject_short = fields.Char(string=_('Subject'), store=True,
                                compute='_compute_subject_short')
    contact_name = fields.Char(string=_('Contact'))
    partner_name = fields.Char(string=_('Partner'))
    phone = fields.Char(required=True)
    email = fields.Char()
    status = fields.Selection(selection=[
        ('progress', 'In Progress'),
        ('done', 'Done'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
    ], default='progress')
    status_description = fields.Char()
    queue = fields.Char(default=lambda self: self.env[
            'asterisk_calls.util'].sudo().get_asterisk_calls_param(
                                            'callback_queue'))
    queue_exten = fields.Char()
    calls = fields.One2many(comodel_name='asterisk_calls.call',
                            inverse_name='callback')
    last_retry = fields.Datetime()
    lead_id = fields.Integer(string=_('Lead'))
    call_time = fields.Char()
    start_time = fields.Datetime()


    @api.multi
    def _get_name(self):
        for rec in self:
            rec.name = str(rec.id)


    @api.depends('subject')
    def _compute_subject_short(self):
        for rec in self:
            if rec.subject:
                rec.subject_short = rec.subject if len(rec.subject) < 50 else \
                                                    rec.subject[:50] + '...'


    @api.model
    def create(self, vals):
        cb = super(Callback, self).create(vals)
        if cb.status == 'progress':
            cb.originate_callback()
        return cb


    def originate_callback(self):
        def send_originate():
            logger.debug('Originate callback ID {}'.format(self.id))
            order = self.env['asterisk_calls.util'].sudo(
                                ).get_asterisk_calls_param('callback_order')
            if order == 'customer':
                # Dial customer first
                self.env['remote_agent.agent'].send_agent('asterisk_calls', json.dumps({
                    'message': 'originate_callback',
                    'queue': queue,
                    'channel': 'Local/{}@{}/nj'.format(self.phone, context),
                    'context': context,
                    'exten': queue_exten,
                    'callback_id': self.id,
                }))
            else:
                # Queue first
                partner_info = self.env['res.partner'].get_partner_by_number(
                                                                    self.phone)
                self.env['remote_agent.agent'].send_agent('asterisk_calls', json.dumps({
                    'message': 'originate_callback',
                    'queue': queue,
                    'channel': 'Local/{}@{}/nj'.format(queue_exten, context),
                    'context': context,
                    'exten': self.phone,
                    'callback_id': self.id,
                    'callerid': u'<{}> "{}"'.format(self.phone,
                                                   partner_info['name']),
                }))
            # Update 
            self.write({'last_retry': fields.Datetime.now()})

        self.ensure_one()
        queue = self.queue if self.queue else self.env[
                'asterisk_calls.util'].sudo().get_asterisk_calls_param(
                                                            'callback_queue')
        queue_exten = self.queue_exten if self.queue_exten else self.env[
                'asterisk_calls.util'].sudo().get_asterisk_calls_param(
                                                                'queue_exten')
        context = self.env[
                'asterisk_calls.util'].sudo().get_asterisk_calls_param(
                                                            'callback_context')
        callback_days = int(self.env[
                'asterisk_calls.util'].sudo().get_asterisk_calls_param(
                                                            'callback_days'))
        callback_daily_attempts = int(self.env['asterisk_calls.util'].sudo(
                        ).get_asterisk_calls_param('callback_daily_attempts'))
        callback_interval_minutes = int(self.env['asterisk_calls.util'].sudo(
                    ).get_asterisk_calls_param('callback_interval_minutes'))
        now = datetime.now()
        # Check if it's a button call
        if self.env.context.get('force_originate'):
            send_originate()
            return
        rec = self
        try:
            # Check callback expiration
            if fields.Datetime.from_string(rec.create_date) + timedelta(
                                                days=callback_days) < now:
                # Callback is expired
                logger.debug('Callback {} expired'.format(rec.id))
                rec.write({'last_retry': fields.Datetime.now(),
                           'status': 'expired'})
                return
            # Check for start time
            if rec.start_time and now < fields.Datetime.from_string(
                                                            rec.start_time):
                logger.debug('Start time has not yet '
                             'come for callback {}'.format(rec.id))
                return
            # Check for call time
            if rec.call_time:
                h, m = rec.call_time.split(':')
                callback_time = now.replace(hour=int(h), minute=int(m))
                if now <= callback_time:
                    logger.debug('Not time yet')
                    return
            # Check retry
            if rec.last_retry and now < fields.Datetime.from_string(
                                    rec.last_retry) + timedelta(
                                        minutes=callback_interval_minutes):
                # Not yet ready
                logger.debug('Callback {} next retry'.format(rec.id))
                return
            # Check for daily calls
            calls = self.env['asterisk_calls.call'].search([
                                                ('callback', '=', rec.id)])
            today_calls = calls.filtered(
                lambda self: fields.Datetime.from_string(
                                            self.create_date).day == now.day)
            if len(today_calls) >= callback_daily_attempts:
                logger.debug('Callback {} daily limit'.format(rec.id))
                return
            # All is passed, go-go-go!
            send_originate()

        except Exception as e:
            # Just log exception for record and proceed with next
            logger.exception(e)


    @api.multi
    def retry(self):
        self.ensure_one()
        self.write({'status': 'progress'})
        self.with_context({'force_originate': True}).originate_callback()


    @api.model
    def cron_originate(self):
        recs = self.env['asterisk_calls.callback'].search(
                                                [('status', '=', 'progress')])
        for rec in recs:
            logger.info('Cron proceed with callback ID {}'.format(rec.id))
            rec.originate_callback()


    @api.multi
    def convert_to_lead(self):
        self.ensure_one()
        try:
            self.env['crm.lead']
        except KeyError:
            raise ValidationError(_('You should install CRM app first!'))
        lead = self.env['crm.lead'].create({
            'partner_name': self.partner_name,
            'name': self.subject,
            'contact_name': self.contact_name,
            'phone': self.phone,
            'email_from': self.email,
        })
        self.lead_id = lead.id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'res_id': lead.id,
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'current',
        }


    @api.multi
    def visit_lead(self):
        self.ensure_one()
        if not self.lead_id:
            raise ValidationError('Not converted to lead')
        try:
            self.env['crm.lead']
        except KeyError:
            raise ValidationError(_('You should install CRM app first!'))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'res_id': self.lead_id,
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'current',
        }


    @api.multi
    def refresh(self):
        return True
