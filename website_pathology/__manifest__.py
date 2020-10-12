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
    'name'          :   'Website Pathology Lab Management System',
    'author'        :   'Webkul Software Pvt. Ltd.',
    'sequence'      :   0,
    'category'      :   'website',
    'summary'       :   'Provides facility for customer to book the Labtest in Pathology directly from website.',
    "license"       :   "Other proprietary",
    'version'       :   "1.0.0",
    'description'   :   """https://webkul.com/blog/odoo-website-pathology-lab-management-system/, pathology,""",
    'website'       :   'https://store.webkul.com/Website-Pathology-Lab-Management-System.html',
    'live_test_url' :   'http://odoodemo.webkul.com/?module=website_pathology&version=12.0&lifetime=60&lout=1&custom_url=/shop/test',
    'depends'       :   [
        'wk_pathology_management',
        'website_sale',
        'website_payment',
        'account_payment',
        # 'account_invoicing',
    ],
    'data'          :   [
        'security/ir.model.access.csv',
        'security/access_control_security.xml',
        "views/templates.xml",
        "views/inherit_website_template.xml",
        "views/inherit_patho_labtest_view.xml",
        "views/inherit_website_cart_template.xml",
        "views/patho_lab_test_category.xml",
        "views/patho_my_account_menu_template.xml",
        'data/website_pathology_data.xml',
    ],
    'demo'          :   [
        'demo/website_patho_demo_data.xml',
    ],
    'installable'   :   True,
    'application'   :   True,
    'auto_install'  :   False,
    'images'        :   ['static/description/Banner.png'],
    'price'         :   76,
    'currency'      :   'EUR',
    'pre_init_hook' :   'pre_init_check',
}
