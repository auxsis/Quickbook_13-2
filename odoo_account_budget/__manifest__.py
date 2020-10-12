# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.

{
    'name': 'Accounting Analytic/Project Budget Management',
    'category': 'Accounting',
   'version': '1.0',
    'price': 99.0,
    'currency': 'EUR',
    'license': 'Other proprietary',
    'summary': """Accounting Analytic/Project Budget Management""",
    'description': """

account_budget
account budget
budget odoo 12
odoo 12 budget
budget community
community edition budget
accounting budget
budget
budget module
module budget
budget app

""",
    'author': "Probuse Consulting Service Pvt. Ltd.",
    'website': "www.probuse.com",
    'support': 'contact@probuse.com',
    'live_test_url': '',
    'images': ['static/description/1222.jpg'],
    'depends': ['account'],
    'installable' : True,
    'application' : False,
    'data': [
        'security/ir.model.access.csv',
        'security/account_budget_security.xml',
        'views/account_analytic_account_views.xml',
        'views/account_budget_views.xml',
        'views/res_config_settings_views.xml',
    ],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
