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

from odoo import models,fields,api,_

class AppointmentGroup(models.Model):
    _name = 'appointment.person.group'
    _rec_name = 'group_name'
    _description = "Appointment Group"

    group_image = fields.Binary(string= "Group Image")
    group_name = fields.Char("Group")
    appoint_person_ids = fields.Many2many(comodel_name= "res.partner", relation= "appoint_partner_table", column1= "appoint_group_id",
        column2 = "res_partner_id", string="Appointment Person")
    color = fields.Integer(string='Color Index')
    appoint_members_count = fields.Integer(" Total Appointment Members", compute="count_appoint_persons")
    general = fields.Boolean("General", default=False)
    currency_id = fields.Many2one("res.currency" , string="Currency", default= lambda self: self.env.user.company_id.currency_id)
    group_charge = fields.Float("Appointment Charge")
    product_tmpl_id = fields.Many2one("product.template", "Group Product",
        help="This product will be used for applying appointment charges while booking an appointment.")
    active = fields.Boolean('Active', default=True, help="If unchecked, it will allow you to hide this record without removing it.")

    def count_appoint_persons(self):
        for rec in self:
            rec.appoint_members_count = len(rec.appoint_person_ids)
        return True
