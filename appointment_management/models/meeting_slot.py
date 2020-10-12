# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class MeetingSlot(models.Model):
    _name = 'meeting.slot'
    _rec_name = 'day'
    _description = "Meeting Slot"
    
    @api.model
    def _get_week_days(self):
        return [
            ('Monday', 'Monday'),
            ('Tuesday', 'Tuesday'),
            ('Wednesday', 'Wednesday'),
            ('Thursday', 'Thursday'),
            ('Friday', 'Friday'),
            ('Saturday', 'Saturday'),
            ('Sunday', 'Sunday')
        ]
    
    day = fields.Selection(
        selection=_get_week_days,
        default='Monday',
        string="Day's",
        required = True,
    )
#     start_date = fields.Date(
#         string = 'Start Date',
#         default=fields.Datetime.now,
#     )
#     end_date = fields.Date(
#         string = 'End Date',
#         default=fields.Datetime.now,
#     )
    slot_line_ids = fields.One2many(
        'meeting.slot.line',
        'slot_id',
        string="Slot Line",
    )
    
    @api.constrains('day')
    def _day_validation(self):
        for days in self:
            day_ids = self.search_count([('day', '=', days.day)])
            if day_ids > 1:
                raise ValidationError(_('You can not set multiple Day with Days!'))

class MeetingSlotLine(models.Model):
    _name = 'meeting.slot.line'
    _description = "Meeting Slot Line"
    
    time = fields.Char(
        string = 'Time',
    )
#     state = fields.Selection([
#         ('am', 'am'),
#         ('pm', 'pm')],
#         string='AM/PM',
#     )
    slot_id = fields.Many2one(
        'meeting.slot',
    )