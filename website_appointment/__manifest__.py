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

{
    'name'          :   'Website Appointment Management System',
    'author'        :   'Webkul Software Pvt. Ltd.',
    'sequence'      :   0,
    'category'      :   'website',
    'summary'       :   'Provides facility for customer to book their Appointment directly from website.',
    "license"       :   "Other proprietary",
    'version'       :   "1.0.0",
    'description'   :   """https://webkul.com/blog/odoo-website-appointment-management-system/ , appointment""",
    'website'       :   "https://store.webkul.com/Odoo-Website-Appointment-Management-System.html",
    'live_test_url' :   'http://odoodemo.webkul.com/?module=website_appointment&lifetime=60&lout=0&custom_url=/appointment',
    'depends'       :   [
        'wk_appointment',
        'account',
        'website_payment',
        'account_payment',
    ],
    'data'          :   [
        'security/ir.model.access.csv',
        'security/access_control_security.xml',
        'views/templates.xml',
        'views/inherit_website_template.xml',
        'views/appoint_my_account_menu_template.xml',
        'views/inherit_appoint_config_views.xml',
        'views/inherit_appoint_views.xml',
        'views/payment_views.xml',
        'views/appoint_portal_payment_template.xml',
        'data/website_appoint_data.xml',
    ],
    'installable'   :   True,
    'application'   :   True,
    'auto_install'  :   False,
    'images'        :   ['static/description/Banner.png'],
    'price'         :   79,
    'currency'      :   'EUR',
    'pre_init_hook' :   'pre_init_check',
}
