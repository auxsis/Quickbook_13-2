# Copyright (c) 2017 Emipro Technologies Pvt Ltd (www.emiprotechnologies.com). All rights reserved.
from . import models
from . import report
from . import wizard
from . import controllers
from odoo import api,SUPERUSER_ID
def _check_view(cr, registry):
    """
    Check other module installed or not. If installed then inactive view from same module.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    ir_module = env['ir.module.module'].search([('name','=','common_connector_library'),('state','=','installed')])
    if ir_module:
        view=env.ref('common_connector_library.view_quant_package_inherit_ept_form')
        view.write({'active':False})