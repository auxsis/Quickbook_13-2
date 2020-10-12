# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.

{
    'name': 'Job Order / Work Order Inspection',
    'version': '1.1',
    'category' : 'Projects',
    'depends': [
        'odoo_job_costing_management',
    ],
       'price': 70.0,

    'license': 'Other proprietary',
    'currency': 'EUR',
    'summary': """Allow you to have inspection process of your job orders for construction and contracting projects.""",
    'description': """
This module allow you to job inspection process.
This module allow you to job inspection values.
This module allow you to job inspection Results.
This module allow you to job inspection Types.
Job Order Inspection
Job Inspection
Job Inspection Results
Job Inspection Results
Job Inspection Types
Job Inspection Process
Job Inspection PDF Reports
Inspection Report
Job Inspection Qweb Report
Inspection
job order Inspection
work order Inspection
Inspection job
Inspection work order
job costing
job contracting
construction app
construction module
construction management
  
""",
    'author': 'Probuse Consulting Service Pvt. Ltd.',
    'website': 'http://www.probuse.com',
    'support': 'contact@probuse.com',
    'images': ['static/description/img1.jpg'],
    'live_test_url': 'https://youtu.be/tqdCt1ORAYQ',
    'data':[
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/inspection_sequence.xml',
        'report/inspection_report.xml',
        'views/job_inspection_view.xml',
        'views/job_inspection_record_view.xml',
        'views/job_inspection_line_view.xml',
        'views/job_order_view.xml',
        'views/inspection_result.xml',
        'views/inspection_type_view.xml',
        'views/project_view.xml',
        'views/jobcost_sheet_view.xml',
    ],
    'installable' : True,
    'application' : False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
