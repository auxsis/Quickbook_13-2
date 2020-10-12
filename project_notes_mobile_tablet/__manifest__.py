# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.

{
    'name': 'Notes on My Account / Portal / Mobile / Tablets',
    'version': '1.0',
        'price': 9.0,

    'depends': [
        'website',
        'odoo_job_costing_management',
    ],
    'currency': 'EUR',
    'license': 'Other proprietary',
    'category': 'Website',
    'summary': 'This module allow technician/employees/portal users add, modify and delete project notes from my account portal.',
    'description': """
    - Project Notes Mobile Tablet
        - Allow project users to added notes from the website
        - Also Allowed to update and delete perticular notes from website
project notes
notes
task notes
construction notes
employee notes
user notes
note
add note
create note
notes project
construction notes
consulting notes
take note
google notes
Construction app
Construction management
job Contracting
job costing
job cost sheet
job sheet
job card
            """,
    'author': 'Probuse Consulting Service Pvt. Ltd.',
    'website': 'www.probuse.com',
    'support': 'contact@probuse.com',
    'images': ['static/description/image1.jpg'],
    'live_test_url': 'https://youtu.be/7DvDJwdETeg',

    'data': [
        'views/project_note_template.xml',
     ], 
    'installable': True,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
