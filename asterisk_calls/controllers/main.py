import logging
import requests
import os
import shutil
import subprocess
import tempfile
from odoo import http, SUPERUSER_ID, registry, _
from odoo.api import Environment
from werkzeug.exceptions import Forbidden, BadRequest

logger = logging.getLogger(__name__)


class AsteriskCallsController(http.Controller):


    def check_ip(self):
        allowed_ips = http.request.env['asterisk_calls.util'].sudo(
                            ).get_asterisk_calls_param('asterisk_ip_addresses')
        if allowed_ips:
            remote_ip = http.request.httprequest.remote_addr
            if remote_ip not in [k.strip(' ') for k in allowed_ips.split(',')]:
                raise Forbidden(
                    'Your IP address {} is not allowed!'.format(remote_ip))


    @http.route('/asterisk_calls/get_caller_name', type='http', auth='none')
    def get_caller_name(self, **kw):
        number = kw.get('number').replace(' ', '')  # Strip spaces
        country_code = kw.get('country')
        if not number:
            return BadRequest('Number not specified in request')
        db = kw.get('db')
        dst_partner_info = {'id': None}  # Defaults
        logger.debug(
            'CALLER NAME REQUEST FOR NUMBER {} country {}'.format(
                                                        number, country_code))
        self.check_ip()
        # If db is passed init env for this db
        if db:
            try:
                with registry(db).cursor() as cr:
                    env = Environment(cr, SUPERUSER_ID, {})
                    dst_partner_info = env['res.partner'].sudo(
                                ).get_partner_by_number(number, country_code)
            except Exception as e:
                raise BadRequest(str(e))
        else:
            dst_partner_info = http.request.env['res.partner'].sudo(
                                ).get_partner_by_number(number, country_code)
        result = ''
        if dst_partner_info['id']:
            result = dst_partner_info['name']
        return result


    @http.route('/asterisk_calls/get_partner_manager', auth='public')
    def get_partner_manager(self, number):
        self.check_ip()
        result = ''
        dst_partner_info = http.request.env['res.partner'].sudo(
                                        ).get_partner_by_number(number)
        if dst_partner_info['id']:
            # Partner found, get manager.
            partner = http.request.env['res.partner'].sudo().browse(
                                                        dst_partner_info['id'])
            if partner.user_id:
                # We have sales person set, now let check if he has an extension.
                if partner.user_id.asterisk_channel:
                    # We have user configured so let return his sxten
                    result = partner.user_id.asterisk_channel
        return result


    @http.route('/asterisk_calls/signup', auth='user')
    def signup(self):
        user = http.request.env['res.users'].browse(http.request.uid)
        email = user.partner_id.email
        if not email:
            return http.request.render('asterisk_calls.email_not_set')
        else:
            mail = http.request.env['mail.mail'].create({
                'subject': 'Asterisk calls subscribe request',
                'email_from': email,
                'email_to': 'odooist@gmail.com',
                'body_html': '<p>Email: {}</p>'.format(email),
                'body': 'Email: {}'.format(email),
            })
            mail.send()
            return http.request.render('asterisk_calls.email_sent',
                                       qcontext={'email': email})


    @http.route('/contact_call', auth='public', website=True,
                methods=['GET', 'POST'])
    def contact_call(self, subject=None, contact_name=None, partner_name=None,
                     phone=None, email=None, call_time=None, **kwargs):
        recaptcha_enabled = http.request.env[
            'asterisk_calls.util'].sudo().get_asterisk_calls_param(
                                        'recaptcha_enabled')
        if http.request.httprequest.method == 'GET':
            key = http.request.env['asterisk_calls.util'].sudo(
                                    ).get_asterisk_calls_param('recaptcha_key')
            placeholder = http.request.env['asterisk_calls.util'].sudo(
                    ).get_asterisk_calls_param('callback_number_placeholder')
            return http.request.render('asterisk_calls.call_us_form',
                    {'phone_placeholder': placeholder,
                     'site_key': key,
                     'recaptcha_enabled': recaptcha_enabled,
                     'request': http.request})
        else:
            if recaptcha_enabled:
                # Check that key is ok
                if not kwargs.get('g-recaptcha-response'):
                    http.request.env['asterisk_calls.callback'].sudo().create({
                        'subject': subject,
                        'contact_name': contact_name,
                        'partner_name': partner_name,
                        'phone': phone,
                        'email': email,
                        'status': 'failed',
                        'status_description': _('No ReCaptcha response'),
                    })                
                    return http.request.render('asterisk_calls.call_us_error',
                                    {'error_message': _('No ReCaptcha response')})
                # Get the value
                secret = http.request.env['asterisk_calls.util'].sudo(
                                ).get_asterisk_calls_param('recaptcha_secret')
                r = requests.post(
                    'https://www.google.com/recaptcha/api/siteverify',
                    data={'secret': secret,
                            'response': kwargs.get('g-recaptcha-response'),
                            'remoteip': http.request.httprequest.environ.get('REMOTE_ADDR'),
                    })
                if r.status_code !=200 or 'success' not in r.text:
                    http.request.env['asterisk_calls.callback'].sudo().create({
                        'subject': subject,
                        'contact_name': contact_name,
                        'partner_name': partner_name,
                        'phone': phone,
                        'email': email,
                        'status': 'failed',
                        'status_description': r.text,
                    })
                    return http.request.render(
                                    'asterisk_calls.call_us_error',
                                    {'error_message': r.text})

            http.request.env['asterisk_calls.callback'].sudo().create({
                'subject': subject,
                'contact_name': contact_name,
                'partner_name': partner_name,
                'phone': phone,
                'email': email,
                'status': 'progress',
                'call_time': call_time,
                })
            return http.request.render('asterisk_calls.call_us_thanks')


    @http.route('/asterisk_calls/callback', auth='public', methods=['GET'])
    def create_callback(self, queue, phone, exten, start_time=None):
        self.check_ip()
        logger.info('Callback request for % @ %', phone, queue)
        partner_info = http.request.env[
                            'res.partner'].sudo().get_partner_by_number(phone)
        http.request.env['asterisk_calls.callback'].sudo().create({
            'phone': phone,
            'queue': queue,
            'queue_exten': exten,
            'contact_name': partner_info['name'],
            'start_time': start_time,
        })
        return 'Callback created'
    

    @http.route('/asterisk_calls/download/agent', auth='user')
    def download_agent(self):
        # Check permission
        user = http.request.env['res.users'].sudo().browse(http.request.uid)
        if not user.has_group('asterisk_calls.group_asterisk_calls_admin'):
            raise Forbidden(
                        'Only Asterisk admin can download the agent!')
        try:
            filename = 'asterisk_calls_agent.tar.gz'
            temp_dir = tempfile.mkdtemp()
            agent_dir = os.path.join(temp_dir, 'asterisk_calls_agent')
            os.mkdir(agent_dir)
            tar_f, tar_path = tempfile.mkstemp()
            current_dir = os.path.dirname(__file__)
            calls_file_list = ['agent.py', 'requirements.txt',
                         'start_agent.sh', 'astcalls_agent.service']
            for file_name in calls_file_list:
                shutil.copy(
                    os.path.join(
                        current_dir, '..', 'deploy', 'agent', file_name),
                    agent_dir)
            # Copy remote_agent folder
            remote_agent_dst_dir = os.path.join(agent_dir, 'remote_agent')
            remote_agent_src_dir = os.path.join(
                                            current_dir, '..', '..',
                                            'remote_agent', 'agent')
            os.mkdir(remote_agent_dst_dir)
            remote_agent_files = ['__init__.py', 'gevent_agent.py',
                                  'agent.crt', 'agent.key', ]
            for r_file_name in remote_agent_files:
                shutil.copy(
                    os.path.join(remote_agent_src_dir, r_file_name),
                    remote_agent_dst_dir)
            # Compress and create the archive
            subprocess.call(
                    'tar cfz {} -C {} asterisk_calls_agent'.format(
                                            tar_path, temp_dir), shell=True)
            headers, content = [], open(tar_path, 'rb').read()
            headers += [('Content-Type', 'application/octet-stream'),
                        ('X-Content-Type-Options', 'nosniff')]
            headers.append(('Cache-Control', 'max-age=0'))
            headers.append(('Content-Disposition', http.content_disposition(
                                                                    filename)))
            headers.append(('Content-Length', len(content)))
            response = http.request.make_response(content, headers)
            return response
        finally:
            shutil.rmtree(temp_dir)
            os.unlink(tar_path)
