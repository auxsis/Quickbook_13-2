# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class Meeting(models.Model):
    _inherit = 'calendar.event'
    
    facilitator = fields.Many2one(
        'res.partner',
        string='Facilitator',
    )
    note_taker = fields.Many2one(
        'res.partner',
        string='Note Taker',
    )
    time_keeper = fields.Many2one(
        'res.partner',
        string='Time Keeper',
    )
    presenter_id = fields.Many2one(
        'res.partner',
        string='Presenter',
    )    
    conclusion = fields.Text(
        string='Conclusion',
    )
    action_items = fields.Text(
        string='Action Items',
    )
    agenda_topic = fields.Text(
        string='Agenda Topics',
    )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
