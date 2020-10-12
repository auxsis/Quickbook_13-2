from odoo import models,fields,api,_
import logging
_logger = logging.getLogger(__name__)

class AppointRejectReason(models.TransientModel):
    _name="appoint.rejectreason.wizard"
    _description = "Appointment Reject Reason"

    add_reason = fields.Text(string="Reason for Rejection")

    def button_addreason(self):
        obj = self.env['appointment'].browse(self._context.get('active_ids'))
        if obj:
            add_reason =  "Reason for Rejection of Appointment : " + self.add_reason
            obj.reject_appoint(add_reason)
        return
