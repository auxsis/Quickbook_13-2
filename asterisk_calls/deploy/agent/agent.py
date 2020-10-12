#!/usr/bin/env python2.7
import argparse
import datetime
import gevent
from gevent.monkey import  patch_all; patch_all()
from gevent.pool import Event
import base64
from expiringdict import ExpiringDict
import json
import logging
import os
import sys
import uuid
import asterisk.manager
# Insert remote_agent into python path
os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from remote_agent import GeventAgent as OdooAgent

logger = logging.getLogger(__name__)

ORIGINATE_RESPONSE_CODES = {
    '0': 'No such extension / number or bad dial tech ie. name of a SIP trunk'
         'that doesn\'t exist',
    '1': 'No answer',
    '4': 'Answered',
    '5': 'Busy',
    '8': 'Congested or not available (Disconnected Number)'
}


def ami_connection(func):
    def wrapper(agent, *args, **kwargs):
        try:
            res = func(agent, *args, **kwargs)
            return res
        except asterisk.manager.ManagerException as e:
            logger.exception(e)
            if e.message == 'Not connected':
                agent.ami_connected.clear()
                agent.ami_disconnected.set()
            else:
                logger.info('Not trying to reconnect.')
    return wrapper


def get_ami_value(response, option):
    # Used by ami functions to get a value from AMI response.
    value = None
    for line in response:
        o, v = line.strip().split(':')
        if o == option:
            value = v
            logger.debug('Option: {}, value: {}'.format(o, v))
            break
    else:
        logger.debug('Option {} not found in response: {}'.format(
                                                            option, response))
    return value


class AsteriskAgent(object):
    version = '2.3'
    asterisk_host = os.environ.get('ASTERISK_HOST', 'asterisk')
    ami_port = os.environ.get('MANAGER_PORT', '5038')
    ami_user = os.environ.get('MANAGER_LOGIN', 'odoo')
    ami_password = os.environ.get('MANAGER_PASSWORD')
    ami_manager = None
    ami_disconnected = Event()
    ami_connected = Event()
    stopped = Event()
    settings = {}
    originate_context = 'test-users'
    originate_timeout = 30
    originated_calls = ExpiringDict(
        max_len=10000, max_age_seconds=3600 * 24)
    active_callback_calls = {}
    recording_tracking = {}  # Dictionary of channels and recording filenames

    def __init__(self):
        if os.environ.get('DEBUG', '0') == '1':
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)
        # Init sentry
        if os.getenv('SENTRY_ENABLED', '0') == '1' and os.getenv('SENTRY_URL'):
            logger.info('Initializing Sentry')
            import sentry_sdk
            sentry_sdk.init(os.getenv('SENTRY_URL'))

    def start(self):
        logger.info('Agent version {} starting'.format(self.version))
        h1 = gevent.spawn(self.ami_connection_loop)
        h2 = gevent.spawn(self.get_originate_settings)
        h3 = gevent.spawn(self.ami_watchdog)
        try:
            gevent.joinall([h1, h2, h3])
        except (KeyboardInterrupt, SystemExit):
            self.stop()
            logger.info('Agent exit')
            sys.exit(0)


    def stop(self):
        self.stopped.set()
        logger.info('Stopping Odoo agent')
        self.odoo_agent.stop()

    def ast_result_notify(self, notify_uid, result):
        self.odoo_agent.notify_user(notify_uid, result.get('Message'),
                                    title='Asterisk Calls',
                                    warning=result.get('Response') == 'Error')

    def get_originate_settings(self):
        self.odoo_agent.odoo_connected.wait()
        def _set_param(param):
            value = self.odoo_agent.odoo.execute(
                'asterisk_calls.util', 'get_asterisk_calls_param', [param])
            if not value:
                logger.warning(
                    'Param {} not set in Odoo, using default: {}'.format(
                                                param, getattr(self, param)))
            else:
                logger.debug(u'Settings {} to {}'.format(param, value))
                setattr(self, param, value)
        map(_set_param, ['originate_context', 'originate_timeout'])
        if os.getenv('ORIGINATE_CONTEXT'):
            self.originate_context = os.getenv('ORIGINATE_CONTEXT')
            logger.info('Overriding originate_context: %s', os.getenv('ORIGINATE_CONTEXT'))

    def add_cdr_user_field(self, channel, value):
        result = self.ami_manager.send_action({
            'Action': 'Getvar',
            'Channel': channel,
            'Variable': 'CDR(userfield)',
        })
        # Wierd, I get here results from previous actions
        if 'Variable' in result.headers and 'Value' in result.headers:
            if result.headers.get('Response') == 'Success':
                vals = []
                if result.headers['Value']:
                    vals.append(result.headers['Value'])
                vals.append(value)
                self.ami_manager.send_action({
                    'Action': 'Setvar',
                    'Channel': channel,
                    'Variable': 'CDR(userfield)',
                    'Value': ';'.join(vals)
                })
            else:
                logger.warning(u'add_cdr_user_field error: {}'.format(json.dumps(
                                                                result.headers)))

    def on_message_setvar(self, channel, msg):
        msg['Action'] = 'Setvar'
        logger.debug(u'Bus event: {}'.format(json.dumps(msg, indent=2)))
        self.ami_manager.send_action(msg)

    @ami_connection
    def on_message_originate(self, channel, msg):
        uid = msg.pop('uid')
        result = {'Response': 'Started', 'Message': 'Call started'}
        # Check if AMI is alive
        if not self.ami_manager:
            logger.error('AMI not connected')
            self.ast_result_notify(uid, {
                             'Response': 'Error',
                             'Message': 'Not connected to Asterisk!'})
            return
        # Check if user's peer is reachable
        if not msg['Channel']:
            # Channel for user is not defined
            logger.error('Channel for UID {} not defined!'.format(uid))
            self.ast_result_notify(uid, {
                             'Response': 'Error',
                             'Message': 'Origination channel is not defined!'})
            return
        if os.getenv('DISABLE_SIP_STATUS_CHECK') == '1':
            pass
        elif msg['Channel'].upper()[:4] == 'SIP/':
            status = self.ami_manager.send_action({'Action': 'SIPshowpeer',
                                        'Peer': msg['Channel'].split('/')[1]})
            if status.headers['Response'] == 'Error':
                self.ast_result_notify(uid, status.headers)
                logger.error(u'Failed originate for {}: {}'.format(
                                                    msg['Channel'],
                                                    status.headers['Message']))
                return False
            elif not ('ok' in status.headers['Status'].lower() or
                      'unmonitored' in status.headers['Status'].lower()):
                logger.info(
                    'Failed originate for {}, peer status is {}'.format(
                                                    msg['Channel'],
                                                    status.headers['Status']))
                self.ast_result_notify(uid, {
                        'Response': 'Error',
                        'Message': '{} status is {}!'.format(
                                msg['Channel'],
                                status.headers['Status'].lower())})
                return False
            else:
                logger.debug(u'Peer {} status is {}, originating'.format(
                            msg['Channel'], status.headers['Status']))
        elif msg['Channel'].upper()[:6] == 'PJSIP/':
            # For PJSIP we have different status check actions.
            status = self.ami_manager.send_action({
                                    'Action': 'PJSIPShowEndpoint',
                                    'Endpoint': msg['Channel'].split('/')[1]})
            if status.headers['Response'] == 'Error':
                err_msg = dict(
                    [k.strip().split(':') for k in status.response])['Message']
                self.ast_result_notify(uid, {'Response': 'Error',
                                       'Message': err_msg})
                logger.error(u'Failed originate for {}: {}'.format(
                                                    msg['Channel'], err_msg))
                return False
            # We do not check endpoint status as panoramisk is not ready for pjsip yet.
        # Go-go-go kukuruza!
        channel_id = uuid.uuid4().hex
        other_channel_id = uuid.uuid4().hex
        action = {
            'Action': 'Originate',
            'EarlyMedia': 'true',
            'Context': self.originate_context,
            'Priority': '1',
            'Timeout': float(self.originate_timeout) * 1000,
            'OtherChannelId': other_channel_id,
            'ChannelId': channel_id,
            'Async': 'true',
        }
        # Check Variable to be a list of vars
        if msg.get('Variable'):
            if type(msg['Variable']) != list:
                msg['Variable'] = [msg['Variable']]
        else:
            # Initialize with empty list
            msg['Variable'] = []
        # Check for # in number for DTMF post-dial.
        if '#' in msg['Exten']:
            dtmf_digits = msg['Exten'].split('#')[-1]
            # Fun trick - pause before sending DTMF is number of #.
            hash_count = len(msg['Exten'].split('#')) - 1
            msg['Variable'] += ['__dtmf_digits={}'.format(dtmf_digits),
                               '__dtmf_delay={}'.format(hash_count)]
            msg['Exten'] = msg['Exten'].split('#')[0]
        action.update(msg)
        logger.debug('Sending action: %s',
                     json.dumps(action, indent=2))
        # Convert action to utf-8 and re-create dict
        res = self.ami_manager.send_action(action)
        action_id = res.headers['ActionID']
        logger.debug('Adding call %s to active calls', action_id)
        self.originated_calls[action_id] = {
            'exten': msg['Exten'],
            'uid': uid,
            'model': msg.get('model'),
            'res_id': msg.get('res_id'),
        }
        if str(res) != 'Success':
            self.originated_calls.pop(action_id)
            self.ast_result_notify(uid, res.headers)
        logger.info(u'Originate call for {} to {} status: {}'.format(
            msg['Channel'], msg['Exten'], res))


    def on_message_originate_callback(self, channel, msg):
        callback_id = msg.get('callback_id')
        cb = self.odoo_agent.odoo.env['asterisk_calls.callback'].browse(callback_id)
        queue = msg.get('queue')
        if queue:
            logger.debug('Queue {} is set, check it'.format(queue))
            # Check if queue exists
            res = self.ami_manager.send_action({
               'Action': 'GetVar',
               'Variable': 'QUEUE_EXISTS({})'.format(queue)
            })
            queue_exists = int(get_ami_value(res.response, 'Value'))
            if queue_exists:
                logger.debug('Queue {} exists'.format(queue))
                # Check if Queue is empty
                res = self.ami_manager.send_action({
                   'Action': 'GetVar',
                   'Variable': 'QUEUE_MEMBER({},ready)'.format(queue)
                })
                ready_count = int(get_ami_value(res.response, 'Value'))
                if ready_count > 0:
                    logger.info(
                        'Queue {} is ready for new callback'.format(queue))
                else:
                    logger.info('Queue {} is not ready'.format(queue))
                    # Update callback status and exit.
                    cb.write({
                        'status_description':
                            'Queue is not ready for new callback',
                        'status': 'failed'})
                    return
            else:
                # Queue is set but does not exist
                logger.error('Queue {} is set but does not '
                             'exist in Asterisk'.format(queue))
                cb.write({'status': 'failed', 'status_description':
                          'Queue {} does not exists in Asterisk'.format(queue)})
                return
        # Originate callback
        channel_id = uuid.uuid4().hex
        other_channel_id = uuid.uuid4().hex
        action = {
            'Action': 'Originate',
            'Channel': msg['channel'],
            'Exten': msg['exten'],
            'CallerID': msg.get('callerid', ''),
            'Context': msg['context'],
            'Priority': '1',
            'Variable': '__CALLBACK_ID={}'.format(callback_id),
            'EarlyMedia': 'true',
            'Async': 'true',
            'Timeout': float(self.originate_timeout) * 1000,
            'OtherChannelId': other_channel_id,
            'ChannelId': channel_id,
        }
        logger.debug(u'Originate callback: {}'.format(
                                            json.dumps(action, indent=2)))
        # Add callback call to the internal dict
        self.active_callback_calls[channel_id] = callback_id
        # Send AMI action
        res = self.ami_manager.send_action(action)
        if str(res) == 'Error':
            cb.write({
                'status': 'failed',
                'status_description': res.headers.get('Message')})


    def on_message_hangup_request(self, channel, msg):
        self.add_cdr_user_field(msg['channel'],
                                'Hangup by user id {}'.format(msg['uid']))
        result = self.ami_manager.send_action({
            'Action': 'Hangup',
            'Channel': msg['channel'],
            'Cause': msg.get('cause', '16'),
        })
        self.ast_result_notify(msg['uid'], result.headers)


    def on_message_redirect(self, channel, msg):
        self.add_cdr_user_field(msg['channel'],
                                'Redirect by user id {}'.format(msg['uid']))
        result = self.ami_manager.send_action({
            'Action': 'Redirect',
            'Channel': msg['channel'],
            'Exten': msg['exten'],
            'Context': msg['context'],
            'Priority': '1'
        })
        self.ast_result_notify(msg['uid'], result.headers)


    def on_message_spy(self, channel, msg):
        self.add_cdr_user_field(msg['spy_channel'],
                                'Spy by user id {}'.format(msg['uid']))
        result = self.ami_manager.send_action({
            'Action': 'Originate',
            'Channel': msg['user_channel'],
            'Application': 'ChanSpy',
            'Data': '{},{}'.format(msg['spy_channel'], msg['spy_options']),
            'Callerid': 'Spy-{} <{}>'.format(msg['spy_exten'], msg['spy_exten']),
            'Variable': '__SIPADDHEADER="{}"'.format(msg['sip_alert_info'] or '')
        })
        self.ast_result_notify(msg['uid'], result.headers)


    def on_message_mute_audio(self, channel, msg):
        self.add_cdr_user_field(msg['channel'],
                                'Mute {} by user id {}'.format(
                                                               msg['state'],
                                                               msg['uid']))
        result = self.ami_manager.send_action({
            'Action': 'MuteAudio',
            'Channel': msg['channel'],
            'Direction': msg['direction'],
            'State': msg['state']
        })
        if str(result) == 'Success':
            result.headers['Title'] = 'Mute Audio'
            result.headers['Message'] = 'State: {}'.format(msg['state'])
        self.ast_result_notify(msg['uid'], result.headers)

    def ami_watchdog(self):
        manager_ping_interval = float(
                                os.environ.get('MANAGER_PING_INTERVAL', '30'))
        logger.debug(u'Manager ping interval: {}'.format(manager_ping_interval))
        while True:
            gevent.sleep(manager_ping_interval)
            if not self.ami_connected.is_set():
                logger.info('Manager not connected')
                continue
            logger.debug(u'Manager ping check')
            try:
                res = self.ami_manager.send_action({'Action': 'Ping'})
                if res.headers.get('Response') != 'Success':
                    raise Exception('Bad response: {}'.format(res.headers))
            except asterisk.manager.ManagerException as e:
                logger.warning('Lost manager connection: {}'.format(e))
                self.ami_connected.clear()
                self.ami_disconnected.set()
            except Exception:
                logger.exception('Manager ping error:')
                self.ami_connected.clear()
                self.ami_disconnected.set()


    def ami_connection_loop(self):
        while True:
            if self.stopped.is_set():
                return
            try:
                # Create PBX connection
                manager = asterisk.manager.Manager()
                logger.info(u'Connecting to {}:{} with {}:{}.'.format(
                    self.asterisk_host, self.ami_port,
                    self.ami_user,
                    self.ami_password[0] + '******' + self.ami_password[-1:]))
                #
                manager.connect(str(self.asterisk_host),
                                port=int(self.ami_port))
                manager.login(self.ami_user, self.ami_password)
                logger.info(u'Connected to AMI.')
                # Register for events
                manager.register_event('VarSet', self.on_asterisk_event)
                manager.register_event('Hangup', self.on_asterisk_event)
                manager.register_event('Cdr', self.on_asterisk_event)
                manager.register_event('Newchannel', self.on_asterisk_event)
                manager.register_event('Newstate', self.on_asterisk_event)
                manager.register_event('NewConnectedLine', self.on_asterisk_event)
                manager.register_event('OriginateResponse', self.on_asterisk_event)
                if os.getenv('DISABLE_EVENT_AGENT_CALLED') != '1':
                    manager.register_event('AgentCalled',
                                           self.on_asterisk_event)
                manager.register_event('UserEvent', self.on_asterisk_event)
                self.ami_manager = manager
                self.ami_disconnected.clear()
                self.ami_connected.set()
                self.ami_disconnected.wait()
                logger.info('AMI disconnected.')

            except asterisk.manager.ManagerSocketException as e:
                logger.error("Error connecting AMI %s:%s: %s",
                             self.asterisk_host, self.ami_port, e)
            except asterisk.manager.ManagerAuthException as e:
                logger.error("Error logging in to the manager: %s" % e)
            except asterisk.manager.ManagerException as e:
                logger.error("Error: %s" % e)
            except Exception as e:
                logger.exception('AMI error:')

            logger.info(u'Reconnecting AMI.')
            gevent.sleep(float(os.environ.get('AMI_RECONNECT_TIMEOUT', '1')))


    def on_asterisk_event(self, event, manager):
        # logger.debug(u'Asterisk event: {}'.format(event.name))
        # We can optionally set exact event handlers
        special_event_handlers = {
            'Newstate': self.on_asterisk_Newstate,
            'NewConnectedLine': self.on_asterisk_Newstate,
        }
        try:
            if event.name in special_event_handlers:
                special_event_handlers[event.name](event, manager)
            elif hasattr(self, 'on_asterisk_{}'.format(event.name)):
                getattr(self, 'on_asterisk_{}'.format(event.name))(event, manager)
            else:
                logger.error(
                    'Asterisk event handler for {} not defined'.format(event.name))
        except Exception as e:
            logger.exception(e)


    # QoS of CDR
    def update_qos(self, event):
        # QoS is not working truly
        return
        value = event.headers.get('Value')
        pairs = [k for k in value.split(';') if k]
        values = {}
        for pairs in pairs:
            k, v = pairs.split('=')
            values.update({k: v})
        values.update({
            'uniqueid': event.headers.get('Uniqueid'),
            'linkedid': event.headers.get('Linkedid')
        })
        gevent.sleep(float(os.environ.get('QOS_UPDATE_DELAY', '3')))
        #logger.debug(u'QoS update: \n{}'.format(json.dumps(
        #    values, indent=2)))
        self.odoo_agent.odoo.execute('asterisk_calls.call', 'update_qos', [values])


    def on_asterisk_VarSet(self, event, manager):
        var = event.headers.get('Variable')
        val = event.headers.get('Value')
        if os.getenv('QOS_DISABLE') != '1' and var in [
                'RTPAUDIOQOS', 'RTPAUDIOQOSRTTBRIDGED',
                'RTPAUDIOQOSLOSSBRIDGED', 'RTPAUDIOQOSJITTERBRIDGED',
                'RTPAUDIOQOSBRIDGED', 'RTPAUDIOQOSLOSS',
                'RTPAUDIOQOSJITTER', 'RTPAUDIOQOSRTT']:
            logger.debug(u'{} VarSet: {}'.format(var, json.dumps(
                                                 event.headers, indent=2)))
            gevent.spawn(self.update_qos, event)
        elif var == 'MIXMONITOR_FILENAME':
            # Track channel recordings
            logger.debug('MIXMONITOR_FILENAME {}, channel {}'.format(
                                        val, event.headers.get('Channel')))
            self.recording_tracking[event.headers.get('Uniqueid')] = val
        elif var == 'MONITOR_FILENAME':
            logger.info('%s', val)

    def on_asterisk_Newchannel(self, event, manager):
        if event.headers['Channel'].startswith('Local/'):
            return
        logger.debug(u'Newchannel: {}'.format(json.dumps(
                                            dict(event.headers.items()),
                                            indent=2)))
        get = event.headers.get
        logger.info('New channel from {} to {}'.format(
                                                    get('CallerIDNum'),
                                                    get('Exten')))
        data = {
            'channel': get('Channel'),
            'uniqueid': get('Uniqueid'),
            'linkedid': get('Linkedid'),
            'context': get('Context'),
            'connected_line_num': get('ConnectedLineNum'),
            'connected_line_name': get('ConnectedLineName'),
            'state': get('ChannelState'),
            'state_desc': get('ChannelStateDesc'),
            'exten': get('Exten'),
            'callerid_num': get('CallerIDNum'),
            'callerid_name': get('CallerIDName'),
            'accountcode': get('AccountCode'),
            'priority': get('Priority'),
            'timestamp': get('Timestamp'),
            'system_name': get('SystemName'),
            'language': get('Language'),
            'event': get('Event'),
            'system_name': get('SystemName'),
        }
        self.odoo_agent.odoo.env['asterisk_calls.channel'].create(data)


    def on_asterisk_Newstate(self, event, manager):
        if event.headers['Channel'].startswith('Local/'):
            return
        gevent.sleep(0.1)  # Just give small priority for create channel method
        if event.headers['ChannelStateDesc'] in ['Down', 'Busy']:
            # No sense in sending Down / Busy updates as Hangup will follow very soon.
            return
        logger.debug(u'Newstate: {}'.format(json.dumps(
                                            dict(event.headers.items()),
                                            indent=2)))
        # Check if it is a originate state change
        active_call = self.originated_calls.get(
                                                    event.headers['Uniqueid'])
        if active_call and event.headers['ChannelStateDesc'] == 'Ringing':
                self.ast_result_notify(active_call['uid'], {
                                                'Response': 'Call Progress',
                                                'Message': 'Ringing...'
                })
        get = event.headers.get
        data = {
            'channel': get('Channel'),
            'uniqueid': get('Uniqueid'),
            'linkedid': get('Linkedid'),
            'context': get('Context'),
            'connected_line_num': get('ConnectedLineNum'),
            'connected_line_name': get('ConnectedLineName'),
            'state': get('ChannelState'),
            'state_desc': get('ChannelStateDesc'),
            'exten': get('Exten'),
            'callerid_num': get('CallerIDNum'),
            'callerid_name': get('CallerIDName'),
            'accountcode': get('AccountCode'),
            'priority': get('Priority'),
            'timestamp': get('Timestamp'),
            'system_name': get('SystemName'),
            'language': get('Language'),
            'event': get('Event'),
            'system_name': get('SystemName'),
        }
        self.odoo_agent.odoo.execute('asterisk_calls.channel', 'update_channel_state',
                          [data])


    def on_asterisk_Hangup(self, event, manager):
        if event.headers['Channel'].startswith('Local/'):
            return
        logger.debug(u'Hangup: {}'.format(
            json.dumps(event.headers, indent=2)))
        logger.info('Hangup channel from {} to {}, state {}'.format(
                                        event.headers.get('CallerIDNum'),
                                        event.headers.get('Exten'),
                                        event.headers.get('ChannelStateDesc')))
        # Check if this is user originated call
        channel_id = event.headers['Uniqueid']
        if self.originated_calls.get(channel_id):
            logger.debug('Hangup found channel %s from originated_calls data.',
                         channel_id)
            chan = self.originated_calls.get(channel_id)
            self.ast_result_notify(chan['uid'], {
                'Response': 'Hangup',
                'Message': event.headers['Cause-txt']
            })
        # Remove channel in Odoo
        self.odoo_agent.odoo.execute('asterisk_calls.channel', 'hangup_channel', [
                                                dict(event.headers.items())])


    def on_asterisk_Cdr(self, event, manager):
        gevent.sleep(1) # Pause a while so that all prev events complete.
        def upload_recording():
            if not int(os.environ.get('RECORDING_UPLOAD_ENABLED', '0')):
                logger.debug(u'Recordings not enabled, skipping')
                return
            # Prepare to upload call recording to Odoo
            gevent.sleep(float(os.environ.get('RECORDING_UPLOAD_DELAY', '5')))
            call_id = event.headers.get('UniqueID')
            file_path = self.recording_tracking.pop(call_id, False)
            if not file_path:
                logger.debug('No MIXMONITOR_FILENAME for channel {}'.format(
                                                event.headers.get('Channel')))
                return
            # Check if recording file still there
            if not os.path.exists(file_path):
                logger.debug(u'Recording for callid {} not found.'.format(
                    call_id))
                return
            # Check if recording is not empty
            if not os.getenv('RECORDING_DISABLE_CLEANUP') == '1' and \
                    os.stat(file_path).st_size == 44:
                # Empty file
                logger.debug('Removing stale {}'.format(file_path))
                os.unlink(file_path)
                return
            # Send file
            logger.debug('Sending call ID %s recording.', call_id)
            data = open(file_path, mode='rb').read()
            result = self.odoo_agent.odoo.execute('asterisk_calls.call',
               'save_call_recording',
               [{'uniqueid': call_id,
                 'data': base64.b64encode(data).decode()}])
            if not result:
                logger.warning(
                    'Odoo save_call_recording result returned False!')
                if int(os.environ.get('RECORDING_KEEP_FAILED_UPLOAD', '0')):
                    logger.debug(u'Recording {} deleted'.format(file_path))
                    os.unlink(file_path)
                else:
                    logger.debug('Recording {} not deleted'.format(file_path))
            else:
                logger.debug('Call recording saved.')
                if os.getenv('RECORDING_KEEP_AFTER_UPLOAD') != '1':
                    if os.path.exists(file_path):
                        os.unlink(file_path)
                        logger.debug(u'Recording {} deleted'.format(file_path))
                    else:
                        logger.debug(
                            u'Recording {} was already removed'.format(
                                                                    file_path))
                else:
                    logger.debug(u'Recording {} not deleted'.format(file_path))

        get = event.headers.get
        if not (get('UniqueID') or get('Uniqueid')):
            logger.warning('Ignoring bad CDR event, hello buggy Asterisk! %s',
                           json.dumps(dict(event.headers.items()), indent=2))
            return
        # Start of on_asterisk_Cdr
        logger.debug(u'Asterisk event Cdr: {}'.format(json.dumps(
                                            dict(event.headers.items()),
                                            indent=2)))
        data = {
            'accountcode': get('AccountCode'),
            'src': get('Source'),
            'dst': get('Destination'),
            'dcontext': get('DestinationContext'),
            'clid': get('CallerID'),
            'channel': get('Channel'),
            'dstchannel': get('DestinationChannel'),
            'lastapp': get('LastApplication'),
            'lastdata': get('LastData'),
            'started': get('StartTime') or False,
            'answered': get('AnswerTime') or False,
            'ended': get('EndTime') or False,
            'duration': get('Duration'),
            'billsec': get('BillableSeconds'),
            'disposition': get('Disposition'),
            'amaflags': get('AMAFlags'),
            'uniqueid': get('UniqueID') or get('Uniqueid'),
            'linkedid': get('Linkedid'),
            'userfield': get('UserField'),
            'system_name': get('SystemName'),
        }
        # Check if this is a callback call
        if get('UniqueID') in self.active_callback_calls:
            callback_id = self.active_callback_calls.pop(
                                                    event.headers['UniqueID'])
            logger.debug('Callback CDR')
            data['callback'] = callback_id
            cb = self.odoo_agent.odoo.env['asterisk_calls.callback'].browse(callback_id)
            if get('Disposition') == 'ANSWERED':
                cb.write({'status': 'done',
                          'status_description': ''})
        # Create CDR
        originate_data = self.originated_calls.get(data['uniqueid'], {})
        if originate_data:
            logger.debug('CDR Originate data found: %s', originate_data)
        self.odoo_agent.odoo.env['asterisk_calls.call'].create(data, context={
             'originate_model': originate_data.get('model'),
             'originate_res_id': originate_data.get('res_id'),
             'mail_create_nolog': True,
             'mail_create_nosubscribe': True,
             'tracking_disable': True,
             'mail_notrack': True})
        gevent.spawn(upload_recording)

    def on_asterisk_OriginateResponse(self, event, manager):
        logger.debug('Asterisk event OriginateResponse: %s',
                     json.dumps(dict(event.headers.items()), indent=2))
        response = event.headers['Response']
        reason = event.headers['Reason']
        channel_id = event.headers['Uniqueid']
        action_id = event.headers['ActionID']
        # Replace action ID to channel ID
        if action_id in self.originated_calls:
            # Replace action_id with channel_id for CDR / Hangup events.
            logger.debug('Replace ActionID %s with ChannelID %s',
                         action_id, channel_id)
            self.originated_calls[
                channel_id] = self.originated_calls[action_id].copy()
            self.originated_calls.pop(action_id)        
        # Check ordinary calls
        if response == 'Failure' and channel_id in self.originated_calls:
            logger.debug('Failed originate')
            chan = self.originated_calls.pop(channel_id)
            self.ast_result_notify(chan['uid'], {
                'Response': 'Error',
                'Message': ORIGINATE_RESPONSE_CODES.get(
                    reason, 'Unknown error')})        
        # Check if this is a callback call
        if response == 'Failure' and channel_id in self.active_callback_calls \
                and reason == '0':
            callback_id = self.active_callback_calls.pop(channel_id)
            logger.debug('Callback Response: {}'.format(response))
            cb = self.odoo_agent.odoo.env[
                'asterisk_calls.callback'].browse(callback_id)
            cb.write({'status': 'failed',
                      'status_description': ORIGINATE_RESPONSE_CODES.get(
                                reason, 'Unknown error')})

    def on_asterisk_AgentCalled(self, event, manager):
        logger.debug(u'Asterisk event AgentCalled: {}'.format(json.dumps(
                                    dict(event.headers.items()), indent=2)))
        msg = {
            'channel': event.headers['Interface'],
            'member_name': event.headers['MemberName'],
            'queue': event.headers['Queue'],
            'event': 'agent_called',
            'dst': event.headers['Exten'],
        }
        self.odoo_agent.odoo.env['bus.bus'].sendone(
                                    'asterisk_calls_channels', json.dumps(msg))


    def on_asterisk_UserEvent(self, event, manager):
        logger.debug(u'Asterisk UserEvent: {}'.format(json.dumps(
                                    dict(event.headers.items()), indent=2)))
        if event.headers.get('UserEvent') == 'CustomCdr':
            return self.on_asterisk_CustomCdr(event, manager)



    def on_asterisk_CustomCdr(self, event, manager):
        dialstatus_disposition_mapping = {
            'CANCEL': 'NO ANSWER',
            'NOANSWER': 'NO ANSWER',
            'CONGESTION': 'CONGESTION',
            'FAILED': 'FAILED',
            'BUSY': 'BUSY',
            'ANSWER': 'ANSWERED',
            'CHANUNAVAIL': 'FAILED',
            '': 'FAILED',
        }
        get = event.headers.get
        ended = datetime.datetime.now()
        duration = int(get('ANSWEREDTIME') or 0)
        dialtime = int(get('DIALEDTIME') or 0)
        started = ended - datetime.timedelta(seconds=dialtime)
        answered = ended - datetime.timedelta(seconds=duration)
        data = {
            'accountcode': get('AccountCode'),
            'src': get('KTS_FROM') or get('CallerIDNum'),
            'dst': get('KTS_TO') or get('ConnectedLineNum'),
            'clid': get('CallerID'),
            'channel': get('Channel'),
            'started': started.strftime('%Y-%m-%d %H:%M:%S'),
            'answered': answered.strftime('%Y-%m-%d %H:%M:%S'),
            'ended': ended.strftime('%Y-%m-%d %H:%M:%S'),
            'duration': dialtime,
            'billsec': duration,
            'disposition': dialstatus_disposition_mapping.get(
                                                        get('DIALSTATUS')),
            'uniqueid': get('Uniqueid'),
            'linkedid': get('Linkedid'),
        }
        # Create CDR
        self.odoo_agent.odoo.env['asterisk_calls.call'].create(data, context={
                                             'mail_create_nolog': True,
                                             'mail_create_nosubscribe': True,
                                             'tracking_disable': True,
                                             'mail_notrack': True})

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s - '
                               '%(funcName)s:%(lineno)s - %(message)s')
    agent = AsteriskAgent()
    odoo_agent = OdooAgent()
    # Add odoo message handlres
    odoo_agent.register_message('setvar', agent.on_message_setvar)
    odoo_agent.register_message('originate', agent.on_message_originate)
    odoo_agent.register_message('originate_callback',
                                agent.on_message_originate_callback)
    odoo_agent.register_message('hangup_request',
                                agent.on_message_hangup_request)
    odoo_agent.register_message('redirect', agent.on_message_redirect)
    odoo_agent.register_message('spy', agent.on_message_spy)
    odoo_agent.register_message('mute_audio', agent.on_message_mute_audio)
    agent.odoo_agent = odoo_agent
    odoo_agent.spawn()
    # Start!
    agent.start()
