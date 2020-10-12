# -*- coding: utf-8 -*-
{

    # App information

    'name': 'USPS Odoo Shipping Connector',
    'version': '12.0',
    'category': 'Website',
    'license': 'OPL-1',
    'summary': 'Odoo USPS Shipping Integration connects your Odoo Instance with USPS and manage your US Shipping operations directly from Odoo.',

    # Dependencies

    'depends': ['shipping_integration_ept'],
    

    # Views

   'data': [
       'views/usps_view_shipping_instance_ept.xml',
       'views/delivery_carrier_view.xml',
       ],
    # Odoo Store Specific

    'images': ['static/description/USPS-Odoo-Cover.jpg'],

    # Author

    'author': 'Emipro Technologies Pvt. Ltd.',
    'website': 'http://www.emiprotechnologies.com',
    'maintainer': 'Emipro Technologies Pvt. Ltd.',

    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'live_test_url':'https://www.emiprotechnologies.com/free-trial?app=usps-shipping-ept&version=12',
    'price': '149',
    'currency': 'EUR',

}
