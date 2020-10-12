import logging
from odoo import api, SUPERUSER_ID

logger = logging.getLogger(__name__)


def migrate(cr, version):
    try:
        with api.Environment.manage():
            env = api.Environment(cr, SUPERUSER_ID, {})
            u = env['res.users'].search([('login', '=', 'asterisk_agent')])
            if u and not u.has_group(
                                'asterisk_calls.group_asterisk_calls_service'):
                logger.info(
                    'ADDING asterisk_service user to Asterisk Calls Service group')
                g = env['ir.model.data'].get_object('asterisk_calls',
                                                    'group_asterisk_calls_service')
                g.users = [(4, u.id)]
    except:
        logger.exception('Asterisk Calls 2.0 migration non-critical error')
