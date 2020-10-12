# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# License URL : https://store.webkul.com/license.html/
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    available_for_appoint = fields.Boolean(
        string='Can be Appointment Group Member',
        help="Check this box if this contact is available for Appointment."
        )
    time_slot_ids = fields.Many2many(comodel_name = "appointment.timeslot",
        column1= "parter_id",
        column2= "time_slot_id",
        relation= "partner_slot_rel",
        string = "Time Slots")
    appoint_group_ids = fields.Many2many(comodel_name= "appointment.person.group",
        relation= "appoint_partner_table", column1= "res_partner_id",
        column2 = "appoint_group_id", string="Appointment Group")
    appoint_person_charge = fields.Float("Appointment Charge")
    work_exp = fields.Char("Working Experience")
    about_person = fields.Text("About")
    specialist = fields.Char("Specialist")
    booked_appointment_ids = fields.One2many(comodel_name="appointment",
        inverse_name="appoint_person_id",
        string="Appointments",
        )
    allow_multi_appoints = fields.Boolean("Allow Multiple Appointments",
        default=lambda self: self.env['ir.default'].get("res.config.settings",'allow_multi_appoints'),
        help="If it is enabled then this member can handle multiple appointments in a particular timeslot.")
    use_addr_as_appoint = fields.Boolean("Use Appointee Address",
        help="If it is enabled then the address of this member will be used as an appointment address.",
        default=True,copy=True)
